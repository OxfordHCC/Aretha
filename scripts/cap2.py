#! /usr/bin/env python3

import argparse
import configparser
from datetime import datetime, timezone
import os
import psycopg2
import pyshark
import sys
import traceback
import ipaddress
import math

import peewee
from playhouse.postgres_ext import PostgresqlExtDatabase
from playhouse.reflection import generate_models, print_model, print_table_sql

import logging

# constants
DEBUG_LEVEL = logging.DEBUG
ARETHA_BASE = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
CONFIG_PATH = os.path.sep.join((ARETHA_BASE, "config", "config.cfg"))
LOG_PATH = os.path.sep.join((ARETHA_BASE, 'log'))
MODULENAME = 'cap2'
logFormatter = logging.Formatter("%(asctime)s {}::%(levelname)s %(message)s".format(MODULENAME))
log = logging.getLogger()
log.setLevel(DEBUG_LEVEL)
fileHandler = logging.FileHandler(os.path.sep.join((LOG_PATH, '%s.log' % MODULENAME)))
fileHandler.setFormatter(logFormatter)
log.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
log.addHandler(consoleHandler)

# initialise vars
time_since_last_commit = 0
queue = []
COMMIT_INTERVAL_SECS = None
CONFIG = None

def fix_sniff_tz(sniff_dt):
    # pyshark doesn't return an aware datetime, so we misinterpret things to being non local
    # what we need to do is figure out what timezone we captured in
    local_tz = datetime.utcnow().astimezone().tzinfo
    # then we need to create a new datetime with the actual timezone... cast back into UTC.
    return datetime.combine(sniff_dt.date(),sniff_dt.time(),local_tz).astimezone(timezone.utc)


def connect():
    # open db connection
    database = CONFIG['postgresql']['database']
    username = CONFIG['postgresql'].get('username') or ''
    password = CONFIG['postgresql'].get('password') or ''
    host = CONFIG['postgresql'].get('host') or 'localhost'
    return PostgresqlExtDatabase(database, host=host, user=username, password=password, port=5432)

def compute_ends(time):
    start = COMMIT_INTERVAL_SECS * math.floor(time.timestamp() / COMMIT_INTERVAL_SECS)
    return (datetime.fromtimestamp(start), datetime.fromtimestamp(start+COMMIT_INTERVAL_SECS))

def DatabaseInsert(packets):
    global time_since_last_commit
    db = connect()
    models = generate_models(db)
    exposures, transmissions = models['exposures'], models['transmissions']

    for packet in packets:
        # clean up packet info before entry
        mac = ''
        src = ''
        dst = ''
        proto = ''
        ext = ''

        if 'ip' not in packet:
            continue

        try:
            src, dst = packet.ip.src, packet.ip.dst
        except AttributeError as ke:
            log.error("AttributeError determining src/dst", exc_info=ke)
            continue

        if ipaddress.ip_address(src).is_multicast or ipaddress.ip_address(dst).is_multicast or packet['eth'].src == 'ff:ff:ff:ff:ff:ff' or  packet['eth'].dst == 'ff:ff:ff:ff:ff:ff':
            # broadcast, multicast, so skip
            continue

        srcLocal = ipaddress.ip_address(src).is_private
        dstLocal = ipaddress.ip_address(dst).is_private

        if srcLocal == dstLocal:
            continue  # internal packet that we don't care about, or no local host (should never happen)
        elif not dstLocal:
            mac = packet['eth'].src
            ext = packet.ip.dst
        else:
            mac = packet['eth'].dst
            ext = packet.ip.src

        if len(packet.highest_layer) > 10:
            proto = packet.highest_layer[:10]
        else:
            proto = packet.highest_layer

        dst_port = packet[packet.transport_layer].dstport

        pkt_time = fix_sniff_tz(packet.sniff_time)
        segstart,segend  = compute_ends(pkt_time)
        
        exps = exposures.select().where(exposures.start_time==segstart, exposures.end_time==segend)

        if exps:
            log.info(f"updating previous exposure {exps[-1].id} [{exps[-1].start_time}]")
            exp = exps[-1] # get laste one
        else:
            log.info(f"creating new exposure {segstart}-{segend}")
            exp = exposures.create(start_time=segstart, end_time=segend)

        xmissions = transmissions.select().where(
            transmissions.exposure == exp,
            transmissions.src == src,
            transmissions.dst == dst,
            transmissions.proto == proto,
            transmissions.mac == mac,
            transmissions.dstport == dst_port,
            transmissions.ext == ext
        );

        if xmissions:
            log.info(f"updating existing transmission { xmissions[-1].id }")            
            xmission = xmissions[-1]
        else:
            log.info(f"creating new transmission")                        
            xmission = transmissions.create(
                exposure = exp,
                src = src,
                dst = dst,
                proto = proto,
                mac = mac,
                dstport=dst_port,
                ext=ext,
                bytes=0,
                bytevar=0,
                packets=0
            )
            log.info(f"new transmission id {xmission.id}")                        
        
        transmissions.update(
            bytes=xmission.bytes + int(packet.length),
            packets=xmission.packets + 1,
            bytevar=0,  ## todo
        ).where(transmissions.id==xmission.id).execute()


    pass

    ## cur.close()
    ## conn.close()    
    log.info(f"Captured {str(len(packets))} packets this tick")
    db.commit()
    db.close()


def QueuedCommit(packet):
    # commit packets to the database in COMMIT_INTERVAL_SECS second intervals

    now = datetime.utcnow()
    global time_since_last_commit
    global queue

    # first packet in new queue
    if time_since_last_commit == 0:
        time_since_last_commit = now

    queue.append(packet)

    # time to commit to db
    if (now - time_since_last_commit).total_seconds() > COMMIT_INTERVAL_SECS:
        if len(queue) > 0:
            try: 
                DatabaseInsert(queue)
            except Exception as e:
                log.error('Error in DB Insert >>>> ', exc_info=e)
        queue = []
        time_since_last_commit = 0



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest="config", type=str, help="Path to config file, default is %s" % CONFIG_PATH)
    parser.add_argument('--interface', dest="interface", type=str, help="Interface to listen to")
    parser.add_argument('--interval', dest="interval", type=float, help="Commit interval in seconds")
    parser.add_argument('--debug', dest='debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)
        
    INTERFACE = None
    CONFIG_PATH = args.config if args.config else CONFIG_PATH

    log.debug(f"Loading config from {CONFIG_PATH}")
    CONFIG = configparser.ConfigParser()
    CONFIG.read(CONFIG_PATH)

    if args.interface is not None:
        INTERFACE = args.interface
    elif "capture" in CONFIG and "interface" in CONFIG['capture']:
        INTERFACE = CONFIG['capture']['interface']
    else:
        log.error(parser.print_help())
        sys.exit(-1)

    if args.interval is not None:
        COMMIT_INTERVAL_SECS = args.interval
    elif "capture" in CONFIG and "interval" in CONFIG['capture']:
        COMMIT_INTERVAL_SECS = int(CONFIG['capture']['interval'])
    else:
        log.error(parser.print_help())
        sys.exit(-1)    

    log.info(f"Setting capture interval {COMMIT_INTERVAL_SECS} ")
    log.info(f"Setting up to capture from {INTERFACE}")
    capture = pyshark.LiveCapture(interface=INTERFACE, bpf_filter='udp or tcp')

    if log.level == logging.DEBUG:
        capture.set_debug()

    log.info("Starting capture")

    capture.apply_on_packets(QueuedCommit)  # timeout=30)
    capture.close()

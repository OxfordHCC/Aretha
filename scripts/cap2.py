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
import db.databaseBursts as db
import cProfile

import logging

# constants
DB = None
DEBUG_LEVEL = logging.INFO
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
RESOLUTION_SECS = None
CONFIG = None

DOPROFILE = True
__PROFILER_CT = 0
__PROFILER = None
__PROFILE_LIMIT = 30

def fix_sniff_tz(sniff_dt):
    # pyshark doesn't return an aware datetime, so we misinterpret things to being non local
    # what we need to do is figure out what timezone we captured in
    local_tz = datetime.utcnow().astimezone().tzinfo
    # then we need to create a new datetime with the actual timezone... cast back into UTC.
    return datetime.combine(sniff_dt.date(),sniff_dt.time(),local_tz).astimezone(timezone.utc)

def compute_ends(time):
    start = RESOLUTION_SECS * math.floor(time.timestamp() / RESOLUTION_SECS)
    return (datetime.fromtimestamp(start), datetime.fromtimestamp(start+RESOLUTION_SECS))

# def to_trans_tuple(transmission):
#     return (transmission.src, transmission.srcport, transmission.dst, transmission.dstport, transmission.mac, transmission.proto, transmission.ext)
    
def mk_trans_tuple(expid, src, srcport, dst, dstport, mac, proto, ext):
    return (expid, src, srcport, dst, dstport, mac, proto, ext)

_transcache = {}
_expcache = {}

def get_exposure(segstart, segend):
    exposures, transmissions = DB.Exposures, DB.Transmissions    
    if not _expcache.get((segstart,segend)): 
        exps = exposures.select().where(exposures.start_time == segstart, exposures.end_time == segend)
        if exps:    
            log.debug(f"updating previous exposure {exps[-1].id} [{exps[-1].start_time}]")
            exp = exps[-1] # get last one
        else:
            log.debug(f"creating new exposure {segstart}-{segend}")
            exp = exposures.create(start_time=segstart, end_time=segend)
        _expcache[(segstart, segend)] = exp
    return _expcache[(segstart,segend)]
    
def get_trans(packet_time, src, srcport, dst, dstport, mac, proto, ext):
    exposures, transmissions = DB.Exposures, DB.Transmissions        
    segstart, segend = compute_ends(packet_time)
    exp = get_exposure(segstart, segend)
    transtup = mk_trans_tuple(exp.id, src, srcport, dst, dstport, mac, proto, ext)
    if not _transcache.get(transtup):
        trans = transmissions(
                    exposure=exp,
                    src=src,
                    srcport=srcport,
                    dst=dst,
                    dstport=dstport,
                    proto=proto,
                    mac=mac,
                    ext=ext,
                    bytes=0,
                    bytevar=0,
                    packets=0
                )
        log.debug(f"created new transmission id {trans.id}")
        _transcache[transtup] = trans
    return _transcache[transtup]

def DatabaseInsert(packets):
    global time_since_last_commit
    exposures, transmissions = DB.Exposures, DB.Transmissions

    # # cached mode
    # times = set([compute_ends(fix_sniff_tz(packet.sniff_time)) for packet in packets])

    # # build trans cache, via excache
    # transcache = {}
    transdirty = set()

    # for t in times:
    #     segstart, segend = t
    #     exps = exposures.select().where(exposures.start_time == segstart, exposures.end_time == segend)
    #     if exps:    
    #         log.debug(f"updating previous exposure {exps[-1].id} [{exps[-1].start_time}]")
    #         exp = exps[-1] # get last one
    #     else:
    #         log.debug(f"creating new exposure {segstart}-{segend}")
    #         exp = exposures.create(start_time=segstart, end_time=segend)        

    #     # build_trans_cache
    #     transmissions.select().where(transmissions.exposure == exp)
    #     [transcache.update(dict([(to_trans_tuple(t), t)])) for t in transmissions]

    for packet in packets:
        try:
            # non ip packet blast away
            if 'ip' not in packet:
                continue

            src, dst = packet.ip.src, packet.ip.dst
            if ipaddress.ip_address(src).is_multicast or ipaddress.ip_address(dst).is_multicast or packet['eth'].src == 'ff:ff:ff:ff:ff:ff' or  packet['eth'].dst == 'ff:ff:ff:ff:ff:ff':
                continue

            # check locality
            srcLocal, dstLocal = ipaddress.ip_address(src).is_private, ipaddress.ip_address(dst).is_private

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

            srcport = packet[packet.transport_layer].srcport
            dstport = packet[packet.transport_layer].dstport

            trans = get_trans(fix_sniff_tz(packet.sniff_time), src, srcport, dst, dstport, mac, proto, ext)

            # update
            trans.bytes = trans.bytes + int(packet.length)
            trans.packets = trans.packets + 1
            trans.bytevar = 0
            transdirty.add(trans)

        except Exception as a:
            log.error("Exception parsing out packet", exc_info=a)
            continue
        pass
    
    # commit our transdirties
    # print(transdirty)
    log.info(f"saving {len(transdirty)} transmissions to db")
    [trans.save() for trans in transdirty]

    ## cur.close()
    ## conn.close()    
    log.info(f"Captured {str(len(packets))} packets this tick")
    DB.peewee.commit()
    # DB.peewee.close()

def QueuedCommit(packet):
    # commit packets to the database in COMMIT_INTERVAL_SECS second intervals

    now = datetime.utcnow()
    global time_since_last_commit
    global queue
    global __PROFILER_CT
    global __PROFILER
    global _transcache
    global _expcache


    # first packet in new queue
    if time_since_last_commit == 0:
        time_since_last_commit = now

    queue.append(packet)

    # time to commit to db
    if (now - time_since_last_commit).total_seconds() > COMMIT_INTERVAL_SECS:
        if len(queue) > 0:
            try:
                if DOPROFILE:
                    if __PROFILER == None and __PROFILER_CT == 0:
                        __PROFILER = cProfile.Profile()
                        __PROFILER.enable()
                    elif __PROFILER_CT == __PROFILE_LIMIT and __PROFILER:
                        __PROFILER.disable()
                        __PROFILER.print_stats()
                        __PROFILER = None
                    __PROFILER_CT += 1                        
                DatabaseInsert(queue)
            except Exception as e:
                log.error('Error in DB Insert >>>> ', exc_info=e)
        queue = []
        time_since_last_commit = 0

        if len(_transcache) > 1000:
            log.info(f"clearing {len(_transcache)} transcache")
            _transcache = {}
        if len(_expcache) > 1000:
            log.info(f"clearing {len(_expcache)} expcache")            
            _expcache = {}
    else:
        pass
        # print(".", end="")

    

    



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest="config", type=str, help="Path to config file, default is %s" % CONFIG_PATH)
    parser.add_argument('--interface', dest="interface", type=str, help="Interface to listen to")
    parser.add_argument('--interval', dest="interval", type=int, help="Commit interval in seconds")
    parser.add_argument('--resolution', dest="resolution", type=int, help="Commit resolution in seconds")    
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
        COMMIT_INTERVAL_SECS = 30

    if args.resolution is not None:
        RESOLUTION_SECS = args.resolution
    elif "capture" in CONFIG and "resolution" in CONFIG['capture']:
        RESOLUTION_SECS = int(CONFIG['capture']['resolution'])
    else:
        RESOLUTION_SECS = 5
        log.error(parser.print_help())
        sys.exit(-1)
        
    DB = db.dbManager()

    log.info(f"Setting capture interval {COMMIT_INTERVAL_SECS} ")
    log.info(f"Setting resolution {RESOLUTION_SECS} ")
    log.info(f"Setting up to capture from {INTERFACE}")
    capture = pyshark.LiveCapture(interface=INTERFACE, bpf_filter='udp or tcp')

    if log.level == logging.DEBUG:
        capture.set_debug()

    log.info("Starting capture")

    capture.apply_on_packets(QueuedCommit)  # timeout=30)
    capture.close()

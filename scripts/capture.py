#! /usr/bin/env python3

import argparse
import configparser
import datetime
import os
import psycopg2
import pyshark
import rutils
import sys
import traceback

# constants
DEBUG = False
local_ip_mask = rutils.make_localip_mask()

# initialise vars
timestamp = 0
queue = []
COMMIT_INTERVAL = None
CONFIG_PATH = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0] + "/config/config.cfg"
CONFIG = None


def DatabaseInsert(packets):
    global timestamp

    # open db connection
    database = CONFIG['postgresql']['database']
    username = CONFIG['postgresql']['username']
    password = CONFIG['postgresql']['password']
    conn = psycopg2.connect(f"dbname={database} user={username} password={password}")
    cur = conn.cursor()

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
            src = packet.ip.src
            dst = packet.ip.dst
        except AttributeError as ke:
            print("Error", ke, packet)
            continue

        if rutils.is_multicast_v4(src) or rutils.is_multicast_v4(dst) or packet['eth'].src == 'ff:ff:ff:ff:ff:ff' or  packet['eth'].dst == 'ff:ff:ff:ff:ff:ff':
            continue

        srcLocal = local_ip_mask.match(src)
        dstLocal = local_ip_mask.match(dst)

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

        # insert packets into table
        try:
            cur.execute("INSERT INTO packets (time, src, dst, mac, len, proto, ext) VALUES (%s, %s, %s, %s, %s, %s, %s)", (packet.sniff_time, src, dst, mac, packet.length, proto, ext))
        except:
            print("Unexpected error on insert:", sys.exc_info())
            traceback.print_exc()
            sys.exit(-1)

    # commit the new records and close db connection
    conn.commit()
    cur.close()
    conn.close()
    print("Captured " + str(len(packets)) + " packets this tick")


def QueuedCommit(packet):
    # commit packets to the database in COMMIT_INTERVAL second intervals

    now = datetime.datetime.now()
    global timestamp
    global queue

    # first packet in new queue
    if timestamp == 0:
        timestamp = now

    queue.append(packet)

    # time to commit to db
    if (now - timestamp).total_seconds() > COMMIT_INTERVAL:
        if len(queue) > 0:
            DatabaseInsert(queue)
        queue = []
        timestamp = 0


def log(*args):
    if DEBUG:
        print(*args)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest="config", type=str, help="Path to config file, default is %s" % CONFIG_PATH)
    parser.add_argument('--interface', dest="interface", type=str, help="Interface to listen to")
    parser.add_argument('--interval', dest="interval", type=float, help="Commit interval in seconds")
    parser.add_argument('--debug', dest='debug', action='store_true')
    args = parser.parse_args()

    DEBUG = args.debug
    INTERFACE = None
    CONFIG_PATH = args.config if args.config else CONFIG_PATH

    print("Loading config from ", CONFIG_PATH)
    CONFIG = configparser.ConfigParser()
    CONFIG.read(CONFIG_PATH)

    if args.interface is not None:
        INTERFACE = args.interface
    elif "capture" in CONFIG and "interface" in CONFIG['capture']:
        INTERFACE = CONFIG['capture']['interface']
    else:
        print(parser.print_help())
        sys.exit(-1)

    if args.interval is not None:
        COMMIT_INTERVAL = args.interval
    elif "capture" in CONFIG and "interval" in CONFIG['capture']:
        COMMIT_INTERVAL = float(CONFIG['capture']['interval'])
    else:
        print(parser.print_help())
        sys.exit(-1)

    log("Setting capture interval ", COMMIT_INTERVAL)
    print(f"Setting up to capture from {INTERFACE}")
    capture = pyshark.LiveCapture(interface=INTERFACE, bpf_filter='udp or tcp')

    if DEBUG:
        capture.set_debug()

    log("Starting capture")

    capture.apply_on_packets(QueuedCommit)  # timeout=30)
    capture.close()

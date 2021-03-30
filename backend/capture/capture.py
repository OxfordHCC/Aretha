#! /usr/bin/env python3
import pyshark
import math
import cProfile
from datetime import datetime, timezone
from scripts.databaseBursts import updateVar
from models import db
from logger import getArethaLogger
from capture.shark_utils import (
    fix_sniff_tz,
    get_internal_mac,
    get_external_ip,
    is_packet_of_interest,
)

# constants
MODULE_NAME = 'capture'

# globals
log = None
_transcache = {}
_expcache = {}


# snap timestamp into a segment of resolution_seconds length
# returns segment start and segment end
def get_time_segment(time, resolution_seconds):
    start = resolution_seconds * math.floor(time.timestamp() / resolution_seconds)
    return (
        datetime.fromtimestamp(start),
        datetime.fromtimestamp(start+resolution_seconds)
    )

def to_trans_tuple(transmission):
    return (transmission.src,
            transmission.srcport,
            transmission.dst,
            transmission.dstport,
            transmission.mac,
            transmission.proto,
            transmission.ext)

def mk_trans_tuple(expid, src, srcport, dst, dstport, mac, proto, ext):
    return (expid, src, srcport, dst, dstport, mac, proto, ext)

def get_exposure(Exposures, segstart, segend):
    if not _expcache.get((segstart,segend)): 
        exps = Exposures.select().where(Exposures.start_time == segstart,
                                        Exposures.end_time == segend)
        if exps:
            prev = exps[-1]
            log.debug(f"updating prev. exposure {prev.id} [{prev.start_time}]")
            exp = prev
        else:
            log.debug(f"creating new exposure [{segstart}] :: [{segend}]")
            exp = Exposures.create(start_time=segstart, end_time=segend)

        _expcache[(segstart, segend)] = exp
    return _expcache[(segstart,segend)]


# TODO replace unreadable arguments with named tuple
# get transmission
def get_trans(Transmissions, Exposures, packet_time, src, srcport, dst, dstport, mac, proto, ext, resolution_seconds):
    
    segstart, segend = get_time_segment(packet_time, resolution_seconds)
    exp = get_exposure(Exposures, segstart, segend)
    
    transtup = mk_trans_tuple(exp.id, src, srcport, dst, dstport, mac, proto, ext)
    
    if not _transcache.get(transtup):
        trans = Transmissions(
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
        # note this will always have id none because it's not saved
        log.debug(f"created new transmission id {trans.id}")
        _transcache[transtup] = trans
        
    return _transcache[transtup]


# TODO should we filter packets of interest on capture?
def database_insert(Transmissions, Exposures, packets, resolution_seconds):
    global _transcache
    global _expcache
    transdirty = set()

    log.info(f"database_insert: analyzing {str(len(packets))} captured packets")

    packets_of_interest = [packet for packet in packets if is_packet_of_interest(packet)]
    
    for packet in packets_of_interest:
        try:
            src, dst = packet.ip.src, packet.ip.dst

            # TODO maybe change to take src and dst as args
            mac = get_internal_mac(packet)
            ext = get_external_ip(packet)
            
            proto = packet.highest_layer[:10]

            src_port = packet[packet.transport_layer].srcport
            dst_port = packet[packet.transport_layer].dstport

            # get transmission of this packet
            trans = get_trans(
                Transmissions,
                Exposures,
                fix_sniff_tz(packet.sniff_time),
                src,
                src_port,
                dst,
                dst_port,
                mac,
                proto,
                ext,
                resolution_seconds)

            packet_length = int(packet.length)

            trans_mean = 0
            if trans.packets > 0:
                trans_mean = trans.bytes/trans.packets
            
            (_, _, trans.bytevar) = updateVar(trans.packets,
                                              trans_mean,
                                              trans.bytevar,
                                              packet_length)
            trans.bytes += packet_length
            trans.packets += 1

            transdirty.add(trans)

        except Exception as a:
            log.error("Exception parsing out packet", exc_info=a)
            continue
        pass

    # TODO investigate if bulk_insert would not be more
    # readable/efficient than save() + atomic()
    with db.atomic() as txn:
        # commit our transdirties
        db.connect()
        log.info(f"saving {len(transdirty)} transmissions to database.")

        [trans.save() for trans in transdirty]

        db.close()
        log.info(f"Aggregated {str(len(packets_of_interest))} packets this tick.")
        
    if len(_transcache) > 1000:
        log.info(f"clearing {len(_transcache)} transcache")
        _transcache = {}

    if len(_expcache) > 1000:
        log.info(f"clearing {len(_expcache)} expcache")            
        _expcache = {}


# TODO test that database_insert is called every n seconds
# test error handling
# commit packets to the database in commit_interval_seconds second intervals
def get_packet_callback(Transmissions, Exposures, commit_interval_seconds, resolution_seconds):
    queue = []
    last_commit = 0

    # profiling variables
    DOPROFILE = True
    __PROFILER_CT = 0
    __PROFILER = None
    __PROFILE_LIMIT = 30

    def queued_commit(packet):
        now = datetime.utcnow()

        nonlocal queue
        nonlocal last_commit
        nonlocal __PROFILER
        nonlocal __PROFILER_CT
        

        # first packet in new queue
        if last_commit == 0:
            last_commit = now

        queue.append(packet)

        seconds_since_last_commit = (now - last_commit).seconds
        if seconds_since_last_commit < commit_interval_seconds:
            return

        # time to commit to db
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

            database_insert(Transmissions, Exposures, queue, resolution_seconds)
            queue = []
            last_commit = 0

        except Exception as e:
            log.error('Error in DB Insert >>>> ', exc_info=e)

    # return from get_packet_callback
    return queued_commit


def startCapture(models, interface, commit_interval_seconds, resolution_seconds, debug=False):
    global log
    log = getArethaLogger(MODULE_NAME, debug=debug)

    # Start capture
    log.info(f"Setting capture interval {commit_interval_seconds} ")
    log.info(f"Setting resolution {resolution_seconds} ")
    log.info(f"Setting up to capture from {interface}")

    capture = pyshark.LiveCapture(interface=interface, bpf_filter='udp or tcp')

    if debug is True:
        capture.set_debug()

    log.info("Starting packet capture")
    
    packet_callback = get_packet_callback(
        models['transmissions'],
        models['exposures'],
        commit_interval_seconds,
        resolution_seconds
    )
    
    # will run indefinitely
    capture.apply_on_packets(packet_callback)

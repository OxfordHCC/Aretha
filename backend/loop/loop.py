#! /usr/bin/env python3
import random
import sys
import time
import json
from datetime import datetime

import requests
import ipaddress

from loop import ipdata, ipapi
from loop.beacon import get_beacon_handler
from loop.firewall import get_firewall
from loop.eval_loop import EvalLoop
from scripts.databaseBursts import DbManager
from models import db

log = None

# TODO see what RAW_IPS does. Don't we need to empty it? It currently
# only accumulates
RAW_IPS = set()
RAW_IPS_ID = 0
_events = []  # async db events


FRUITS = ["Apple", "Orange", "Banana", "Cherry", "Apricot", "Avocado",
          "Blueberry", "Cherry", "Cranberry", "Grape", "Kiwi", "Lime",
          "Lemon", "Mango", "Nectarine", "Peach", "Pineapple",
          "Raspberry", "Strawberry"]

LAST_VIEW_REFRESH = 0

# get company geodata
# TODO test that this function returns expected types
def get_company_info(ip, geoapi_provider):
    if geoapi_provider == 'ipdata':
        try:
            geodata = ipdata.get_company_info(ip)
        except Exception as e:
            log.error(' Failure querying ipdata for [%s]' % ip, exc_info=e)
        finally:
            return geodata

    if geoapi_provider == 'ip-api':
        try:
            geodata = ipapi.get_company_info(ip)
        except Exception as e:
            log.error(' Failure querying ip-api for [%s]' % ip, exc_info=e)
        finally:
            return geodata

    raise Exception("Unknown geoapi provider.")
    

# gathers data about newly seen ip addresses
def process_geos(Transmissions, Geodata, geoapi_provider):
    global RAW_IPS_ID
    
    # update the list of known ips from where we left off last time
    # new id is gathered before other ops to ensure that no packets
    # are missed
    try:
        new_id = (Transmissions
                  .select(Transmissions.id)
                  .order_by(Transmissions.id.desc())
                  .limit(1)
                  .dicts())[0]["id"]
    except:
        new_id = 0

    # TODO can we do this better in a single pass over Transmissions?
    # add unseed src ips from transmissions
    raw_txs_src = (Transmissions
               .select(Transmissions.src, Transmissions.id)
               .distinct()
               .where(Transmissions.id > RAW_IPS_ID)
               .dicts())

    for row in raw_txs_src:
        RAW_IPS.add(row['id'])

        
    # add unseen dst ips from transmissions
    raw_txs_dst = (Transmissions
               .select(Transmissions.dst, Transmissions.id)
               .distinct()
               .where(Transmissions.id > RAW_IPS_ID)
               .dicts())

    for row in raw_txs_dst:
        RAW_IPS.add(row['id'])

    # update last seen id
    RAW_IPS_ID = new_id

    # get a list of ip addresses we've already looked up
    raw_geos = Geodata.select(Geodata.ip).dicts()    
    known_ips = [row['ip'] for row in raw_geos]

    # go through and enrich the rest

    # TODO it seems like this always goes through every ip_address in
    # raw_ips -- otherwise put, raw_ips never graduate to "cooked_ips"
    for ip in RAW_IPS:
        if ipaddress.ip_address(ip).is_private:
            # local ip, so skip
            continue

        # Well, actually it seems like "cooked_ips" get pruned of here
        # (see comment above)
        if ip not in known_ips:
            geodata = get_company_info(ip, geoapi_provider)
            
            # commit the extra info to the database
            log.info('inserting geodata entry %s' % json.dumps(geodata))

            Geodata.insert({
                Geodata.ip: ip,
                Geodata.lat: geodata.get('lat', "00"),
                Geodata.lon: geodata.get('lon', '00'),
                Geodata.country: geodata.get('country', 'XX'),
                Geodata.orgname: geodata.get('orgname', 'unknown')[:256],
                Geodata.domain: geodata.get('domain', 'unknown')[:256],
                Geodata.tracker: geodata.get('tracker', False)
            }).execute()
            
            # bookkeeping
            log.info("Adding to known IPs %s " % ip)
            known_ips.append(ip)


def get_manufacturer(mac):
    res = requests.get(f"https://api.macvendors.com/{mac}")
    res_text = res.text

    if "errors" in res.text:
        raise Exception("Some error happened while fetching manufacturer from macvendors")
    return res.text

# gets manufacturers of new devices and inserts into the database
def process_macs(Transmissions, Devices, autogen_device_names):
    
    # TODO find way to get raw_macs without going through whole txs
    # table

    # We return tuples from our selections so we can construct sets
    # (tuples hare hashable)
    tx_macs = set(Transmissions.select(Transmissions.mac).distinct(True).tuples())
    known_macs = set(Devices.select(Devices.mac).tuples())
    raw_macs = list(tx_macs - known_macs)

    for mac in raw_macs:
        deviceName = "unknown"
        if autogen_device_names:
            deviceName = random.choice(FRUITS) + "#" + str(random.randint(100,999))

        try:
            manufacturer = get_manufacturer(mac)
        except:
            manufacturer = "unknown"

        log.debug(f"adding device {mac[0]}, {manufacturer[:20]}, {deviceName}")
        Devices.insert({
            Devices.mac: mac[0],
            Devices.manufacturer: manufacturer[:20],
            Devices.name: f"{deviceName}({manufacturer})"
        }).execute()

# TODO replace packets table with transmissions
def is_upsert_packet_event(json_event):
    operation = json_event['operation']
    table = json_event['table']

    if not operation in ['UPDATE','INSERT']:
        return False
    if not table == "packets":
        return False
    return True

# get src ip or dst ip or raise KeyError
def ip_from_event(json_event):
    data = json_event['data']
    return data.get('src') or data.get('dst')
        
# updates RAW_IPS (see process_geos)
def process_events():
    global _events
    log.debug("process_events has %s waiting in queue " % len(_events))

    curr_events = _events.copy()
    _events.clear()

    # map to json
    json_events = [json.loads(event) for event in curr_events]

    # filter out events not relating to update/insert on packet table 
    upsert_events = [event for event in json_events if is_upsert_packet_event(event)]

    # map to ip address in packet (src or dst or null)
    packet_ips = [ip_from_event(event) for event in upsert_events]

    # filter out null ips
    packet_ips = [ip for ip in packet_ips if not ip is None]

    # add to global memory to be processed by next eval_loop step
    for ip in packet_ips:
        RAW_IPS.add(ip)

    log.debug("RAW IPS now has %s " % (len(RAW_IPS) if RAW_IPS else 'none'))

# checks to see if any new iptables rules need to be made
def process_firewall(Rules, BlockedIPs, Geodata):
    # TODO should not even queue process_firewall function if platform
    # is not supported
    # get firewall supported by this system, if any
    firewall = get_firewall()
    if firewall is None:
        log.info("no firewall handling implemented for this system yet.")
        return

    firewall_rules = (Rules
                      .select(Rules.id, Rules.c_name, Rules.device, BlockedIPs.ip)
                      .join(BlockedIPs, "LEFT", on=(Rules.id == BlockedIPs.rule)))

    geodata = Geodata.select(Geodata.c_name, Geodata.ip)

    # construct a dict of all ips blocked for each rule
    rule_company = dict()
    rule_device = dict()
    rule_ips = dict()
    for rule_id, company_name, blocked_ip, device in firewall_rules:
        rule_company[id] = company_name
        rule_device[id] = device
        if id not in rule_ips:
            rule_ips[id] = set()
        rule_ips[id].add(blocked_ip)

    # construct a dict of all known company/ip matchings
    geos = dict()
    for company_name, ip in geodata:
        if company_name not in geos:
            geos[company_name] = set()
        geos[company_name].add(ip)
    
    # compare the two
    # TODO handle possible db write failures -> reset iptables
    # TODO handle possible iptables failure -> revert db
    for rule, company in rule_company.items():
        for ip in geos.get(company, set()) - rule_ips.get(rule, set()):
            BlockedIPs.insert({
                BlockedIPs.ip: ip,
                BlockedIPs.rule: rule
            }).execute()

            if rule_device[rule] is None:
                firewall.drop_inbound_ip(ip)
                firewall.drop_outbound_ip(ip)
            else:
                firewall.drop_ip_for_mac(ip, rule_device[rule])

    # some systems require explicit saving 
    firewall.persist()


def open_db():
    db.connect()

def close_db():
    db.close()
    
def startLoop(models, db_name, db_user, db_pass, db_host, db_port, interval, is_beacon, autogen_device_names, geoapi_provider, logger):
    global _events
    global log
    log = logger

    running = [True]

    Transmissions = models['transmissions']
    Devices = models['devices']
    Rules = models['rules']
    BlockedIPs = models['blocked_ips']
    Geodata = models['geodata']

    # listen for db changes and append to _events
    # note that this creates a *second* datbase connection
    # TODO see how we can convert this to peewee
    listener_thread_stopper = DbManager(
        database=db_name,
        username=db_user,
        password=db_pass,
        host=db_host,
        port=db_port
    ).listen(
        'db_notifications',
        lambda payload:_events.append(payload)
    )

    
    # create infinite eval loop
    loop = EvalLoop(
        interval,
        on_close=listener_thread_stopper,
        log=log
    )
    
    loop.register(open_db)
    loop.register(process_events)
    loop.register(
        lambda: process_geos(Transmissions, Geodata, geoapi_provider),
        "process_geos")
    loop.register(
        lambda: process_macs(Transmissions, Devices, autogen_device_names),
        "process_macs")

    # conditional handlers
    if get_firewall() is not None:
        loop.register(lambda: process_firewall(Rules, BlockedIPs, Geodata))

    if(is_beacon):
        beacon = get_beacon_handler(Transmissions, Geodata, Rules)
        def run_beacon():
            last_beacon = beacon(last_beacon)
        
        loop.register(run_beacon)

    # close db after each loop
    loop.register(close_db)

    # start loop
    loop.start()

#! /usr/bin/env python3

import argparse
import configparser
import dns.resolver, dns.reversename
import json
import os
import random
import requests
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime
import tldextract
import urllib
import ipaddress

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
DB_MANAGER = None
DEBUG = False
log = lambda *args: print(*args) if DEBUG else ''
RAW_IPS = set()
RAW_IPS_ID = 0
_events = []  # async db events
IOTR_BASE = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
CONFIG_PATH = IOTR_BASE + "/config/config.cfg"
CONFIG = None
CONFIG_ID = None
FRUITS = ["Apple", "Orange", "Banana", "Cherry", "Apricot", "Avocado", "Blueberry", "Cherry", "Cranberry", "Grape", "Kiwi", "Lime", "Lemon", "Mango", "Nectarine", "Peach", "Pineapple", "Raspberry", "Strawberry"]
TRACKERS = None
last_beacon = float(0)
BEACON_URL = None
BEACON_ENDPOINT = None
BEACON_INTERVAL = None
BEACON_KEY = None
BEACON_SSH = None
LAST_VIEW_REFRESH = 0


# gathers data about newly seen ip addresses
def processGeos():
    global RAW_IPS
    global RAW_IPS_ID

    # update the list of known ips from where we left off last time
    # new id is gathered before other ops to ensure that no packets are missed
    try:
        new_id = DB_MANAGER.execute("select id from packets order by id desc limit 1", ())[0][0]
    except:
        new_id = 0
    for r in DB_MANAGER.execute("select distinct src, id from packets where id > %s", (RAW_IPS_ID,)):
        RAW_IPS.add(r[0])
    for r in DB_MANAGER.execute("select distinct dst, id from packets where id > %s", (RAW_IPS_ID,)):
        RAW_IPS.add(r[0])
    RAW_IPS_ID = new_id
    
    # get a list of ip addresses we've already looked up
    raw_geos = DB_MANAGER.execute("SELECT ip FROM geodata", ())
    known_ips = []
    for row in raw_geos:
        known_ips.append(row[0])

    # go through and enrich the rest
    for ip in RAW_IPS:
        if ipaddress.ip_address(ip).is_private:
            # local ip, so skip
            continue
        
        if ip not in known_ips:
            lat = '00'
            lon = '00'
            country = 'XX'
            orgname = 'unknown'
            domain = 'unknown'
            tracker = False

            # get company info from ipdata
            try:
                data = requests.get('https://api.ipdata.co/' + ip + '?api-key=' + CONFIG['ipdata']['key'])
                if data.status_code==200 and data.json()['latitude'] is not None:
                    data = data.json()
                    tracker = istracker(ip)
                    orgname = data['organisation'] 
                    lat = data['latitude']
                    lon = data['longitude']
                    country = data['country_code'] or data['continent_code']
            except:
                pass

            # make reverse dns call to get the domain
            res = dns.resolver.Resolver()
            res.nameservers = ['8.8.8.8', '8.8.4.4']
            # try:
            #     dns_ans = res.query(ip + ".in-addr.arpa", "PTR")
            #     raw_domain = str(dns_ans[0])
            #     domain = tldextract.extract(raw_domain).registered_domain
            # except:
            #     pass

            try:
                dns_ans = dns.resolver.query(dns.reversename.from_address(ip),'PTR')
                raw_domain = str(dns_ans[0])
                domain = tldextract.extract(raw_domain).registered_domain
            except:
               print("Error resolving ip ", ip, " - ", sys.exc_info()[0])
               pass


            # commit the extra info to the database
            DB_MANAGER.execute("INSERT INTO geodata VALUES(%s, %s, %s, %s, %s, %s, %s)", (ip, lat, lon, country, orgname and orgname[:25] or "", domain and domain[:30] or "", tracker))
            
            # if orgname and domain: 
            #     DB_MANAGER.execute("INSERT INTO geodata VALUES(%s, %s, %s, %s, %s, %s)", (ip, lat, lon, country, orgname[:20], domain[:30]))
            # else:
            #     # TODO what to do here?
            #     log("No orgname or domain", orgname, domain)

            # bookkeeping
            known_ips.append(ip)
            log("Adding to known IPs ", ip)


# gets manufacturers of new devices and inserts into the database
def processMacs():
    raw_macs = DB_MANAGER.execute("SELECT DISTINCT mac FROM packets", ())
    known_macs = DB_MANAGER.execute("SELECT mac FROM devices", ())
    for mac in raw_macs:
        if mac not in known_macs:

            deviceName = "unknown"
            if CONFIG['loop'] and CONFIG['loop']['autogen-device-names']:
                deviceName = random.choice(FRUITS) + "#" + str(random.randint(100,999))

            manufacturer = requests.get("https://api.macvendors.com/" + mac[0]).text
            if "errors" not in manufacturer:
                DB_MANAGER.execute("INSERT INTO devices VALUES(%s, %s, %s)", (mac[0], manufacturer[:20], deviceName + " (" + manufacturer + ")"))
            else:
                DB_MANAGER.execute("INSERT INTO devices VALUES(%s, 'unknown', %s)", (mac[0], deviceName))


# updates RAP_IPS (see processGeos)
def processEvents():
    global _events
    log("processEvents has ", len(_events), " waiting in queue")
    cur_events = _events.copy()
    _events.clear()
    for evt in cur_events:
        evt = json.loads(evt)
        if RAW_IPS and evt["operation"] in ['UPDATE','INSERT'] and evt["table"] == 'packets':
            try:
                RAW_IPS.add(evt["data"]["src"])
            except:
                pass
            try:
                RAW_IPS.add(evt["data"]["dst"])
            except:
                pass
        pass
    log("RAW IPS now has ", len(RAW_IPS) if RAW_IPS else 'none')

#uses the config tracker list to determine whether an ip address is from a tracker
def istracker(ip):
    if TRACKERS is None:
        return False
    try:
        domain = tldextract.extract(socket.gethostbyaddr(ip)[0])
        if domain.registered_domain in TRACKERS:
            return True
    except:
        return False
    return False


# checks to see if any new iptables rules need to be made
def process_firewall():
    fw = DB_MANAGER.execute("SELECT r.id, r.c_name, b.ip, r.device FROM rules as r LEFT JOIN blocked_ips as b ON r.id = b.rule", ())
    gd = DB_MANAGER.execute("SELECT c_name, ip FROM geodata", ())

    # construct a dict of all ips blocked for each rule
    rule_company = dict()
    rule_device = dict()
    rule_ips = dict()
    for rule in fw:
        rule_company[rule[0]] = rule[1]
        rule_device[rule[0]] = rule[3]
        if rule[0] not in rule_ips:
            rule_ips[rule[0]] = set()
        rule_ips[rule[0]].add(rule[2])

    # construct a dict of all known company/ip matchings
    geos = dict()
    for geo in gd:
        if geo[0] not in geos:
            geos[geo[0]] = set()
        geos[geo[0]].add(geo[1])

    # compare the two
    if sys.platform.startswith("linux"):
        for rule, company in rule_company.items():
            for ip in geos.get(company, set()) - rule_ips.get(rule, set()):
                DB_MANAGER.execute("INSERT INTO blocked_ips(ip, rule) VALUES(%s, %s)", (ip, rule))
                if rule_device[rule] is None:
                    subprocess.run(["sudo", "iptables", "-I", "INPUT", "-s", ip, "-j", "DROP"])
                    subprocess.run(["sudo", "iptables", "-I", "OUTPUT", "-d", ip, "-j", "DROP"])
                else:
                    subprocess.run(["sudo", "iptables", "-I", "FORWARD", "-d", ip, "-m", "mac", "--mac-source", rule_device[rule], "-j", "DROP"])
                subprocess.run(["sudo", "dpkg-reconfigure", "-p", "critical", "iptables-persistent"])
    else:
        print(f"ERROR: platform {sys.platform} is not linux - cannot add {ip} to rule {rule}")


# phone home and check for commands
def beacon():
    global last_beacon
    content = ""
    if time.time() - last_beacon > BEACON_INTERVAL:
        p = DB_MANAGER.execute("SELECT COUNT(id) FROM packets", (), all=False)[0]
        g = DB_MANAGER.execute("SELECT COUNT(ip) FROM geodata", (), all=False)[0]
        f = DB_MANAGER.execute("SELECT COUNT(id) FROM rules", (), all=False)[0]
        post_data = urllib.parse.urlencode({'i': CONFIG_ID, 'k': BEACON_KEY, 'p': p, 'g': g, 'f': f}).encode('ascii')
        try:
            resp = urllib.request.urlopen(url=f"http://{BEACON_URL}:{BEACON_ENDPOINT}", data=post_data)
            content =  resp.read().decode(resp.headers.get_content_charset())
            last_beacon = time.time()
        except:
            print("Error contacting beacon server")

        # command triggers
        if content == "CN":
            print("remote: opening secure connection")
            try:
                subprocess.run(["ssh", "-i", "~/.ssh/aretha.pem", "-fTN", "-R", f"2500:localhost:22", f"{BEACON_SSH}"], timeout=3600, check=True)
            except:
                print("error opening connection")
        elif content == "RB":
            print("remote: reboot")
            try:
                subprocess.run(["shutdown", "-r", "now"], timeout=120, check=True)
            except:
                print("error opening connection")
        elif content == "RS":
            print("remote: reset service")
            try:
                subprocess.run(["systemctl", "restart", "iotrefine"], timeout=300, check=True)
            except:
                print("error opening connection")

def refreshView():
    global LAST_VIEW_REFRESH
    if LAST_VIEW_REFRESH != datetime.utcnow().minute:
        DB_MANAGER.execute("refresh materialized view impacts with data", ());
        LAST_VIEW_REFRESH = datetime.utcnow().minute


################
# loop control #
################
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest="config", type=str, help="Path to config file, default is %s " % CONFIG_PATH)    
    parser.add_argument('--interval', dest="interval", type=float, help="Specify loop interval in sec (can be fractions)")
    parser.add_argument('--debug', dest='debug', action="store_true", help='Turn debug output on (Default off)')
    args = parser.parse_args()

    DEBUG = args.debug    
    CONFIG_PATH = args.config if args.config else CONFIG_PATH
        
    log("Loading config from .... ", CONFIG_PATH)
    CONFIG = configparser.ConfigParser()
    CONFIG.read(CONFIG_PATH)
    DB_MANAGER = databaseBursts.dbManager()
    INTERVAL = None
    ISBEACON = False
    
    if args.interval is not None:
        INTERVAL = float(args.interval)
    elif "loop" in CONFIG and "interval" in CONFIG['loop']:
        INTERVAL = float(CONFIG['loop']['interval'])
    else:
        print("Error parsing interval", 'loop' in CONFIG)
        parser.print_help()
        sys.exit(-1)
    
    if "loop" in CONFIG and "beacon" in CONFIG['loop']:
        ISBEACON = CONFIG['loop']['beacon'].lower()=='true'
    else:
        ISBEACON = False

    if ISBEACON:
        if not "beacon" in CONFIG: 
            print("BEACON config section missing")
            parser.print_help()
            sys.exit(-1)

        if "url" in CONFIG['beacon']:
            BEACON_URL = CONFIG['beacon']['url']
        else:
            print('config.BEACON missing URL')
            sys.exit(-1)

        if 'endpoint' in CONFIG['beacon']:
            BEACON_ENDPOINT = CONFIG['beacon']['endpoint']
        else:
            print('config.BEACON missing endpoint')
            sys.exit(-1)

        if 'key' in CONFIG['beacon']:
            BEACON_KEY = CONFIG['beacon']['key']
        else:
            print("config.BEACON missing key")
            sys.exit(-1)
        
        if 'ssh' in CONFIG['beacon']:
            BEACON_SSH = CONFIG['beacon']['ssh']
        else:
            print("config.BEACON missing ssh")
            sys.exit(-1)
        
        if "interval" in CONFIG['beacon']:
            BEACON_INTERVAL = int(CONFIG['beacon']['interval'])
        else:
            BEACON_INTERVAL = 3600

    if not CONFIG['api']['url']:
        print("ERROR: CONFIG url must be set under [api]")
        sys.exit(-1)
    
    if not CONFIG['general']['id']:
        print("ERROR: CONFIG id must be set under [general]")
        sys.exit(-1)
    else:
        CONFIG_ID = CONFIG['general']['id']

    DEVICES_API_URL = CONFIG['api']['url'] + '/devices'
    log("Devices API URL set to %s" % DEVICES_API_URL)

    running = [True]

    # note that this creates a *second* datbase connection
    listener_thread_stopper = databaseBursts.dbManager().listen('db_notifications', lambda payload:_events.append(payload))
    
    sys.stdout.write("Loading trackers file...")
    try:
        with open(IOTR_BASE + CONFIG['loop']['trackers']) as trackers_file:
            TRACKERS = []
            for line in trackers_file.readlines():
                TRACKERS.append(line.strip('\n'))
        print("ok")
    except:
        print("error")

    def shutdown(*sargs):
        running[0] = False
        listener_thread_stopper()
    
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # loop through categorisation tasks
    while(running[0]):
        log("Awake!");
        if running[0]:
            processEvents()
        if running[0]:
            refreshView()
        if running[0]:
            processGeos()
        if running[0]:
            processMacs()
        if running[0]:
            process_firewall()
        if ISBEACON == True and running[0]:
            beacon()
        if running[0]:
            log("sleeping zzzz ", INTERVAL);
            time.sleep(INTERVAL)

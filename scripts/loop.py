#! /usr/bin/env python3

import argparse
import configparser
import dns.resolver
import json
import os
import random
import requests
import signal
import socket
import subprocess
import sys
import time
import tldextract
import urllib
import ipaddress

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
DB_MANAGER = None
DEBUG = False
log = lambda *args: print(*args) if DEBUG else ''
RAW_IPS = None
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


# gathers data about newly seen ip addresses
def processGeos():

    # to save us querying the whole packet table every loop
    # global RAW_IPS
    # if not RAW_IPS:
    #    log("Preloading RAW_IPS")
    RAW_IPS = set([r[0] for r in DB_MANAGER.execute("SELECT DISTINCT src FROM packets", ())]).union([r[0] for r in DB_MANAGER.execute("SELECT DISTINCT dst FROM packets", ())])
    #    log(" Done ", len(RAW_IPS), " known ips ")
    
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
                if data.status_code==200 and data.json()['latitude'] is not '':
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
            try:
                dns_ans = res.query(ip + ".in-addr.arpa", "PTR")
                raw_domain = str(dns_ans[0])
                domain = tldextract.extract(raw_domain).registered_domain
            except:
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
    for rule, company in rule_company.items():
        for ip in geos.get(company, set()) - rule_ips.get(rule, set()):
            DB_MANAGER.execute("INSERT INTO blocked_ips(ip, rule) VALUES(%s, %s)", (ip, rule))
            if sys.platform.startswith("linux"):
                if rule_device[rule] is None:
                    subprocess.run(["sudo", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"])
                    subprocess.run(["sudo", "iptables", "-A", "OUTPUT", "-d", ip, "-j", "DROP"])
                else:
                    subprocess.run(["sudo", "iptables", "-A", "FORWARD", "-d", ip, "-m", "mac", "--mac-source", rule_device[rule], "-j", "DROP"])
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
            print("remote: opening tunnel")
            subprocess.run(["ssh", "-R", f"4203:{BEACON_URL}:22", f"wilmor@{BEACON_URL}"])
        if content == "RB":
            print("remote: reboot")
            subprocess.run(["shutdown", "-r", "now"])
        if content == "RS":
            print("remote: reset service")
            subprocess.run(["systemctl", "restart", "iotrefine"])
        if content.startswith("EX"):
            content = content.strip("EX")
            content = content.split(";")
            key = content[0]
            value = content[1]
            print(f"remote: set {key} to {value}")
            DB_MANAGER.execute("UPDATE experiment SET value = %s WHERE name = %s", (key, value))


def refreshView():
    DB_MANAGER.execute("refresh materialized view impacts with data", ());


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
        ISBEACON = CONFIG['loop']['beacon']
        if "url" in CONFIG['beacon']:
            BEACON_URL = CONFIG['beacon']['url']
            BEACON_ENDPOINT = CONFIG['beacon']['endpoint']
            BEACON_KEY = CONFIG['beacon']['key']
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

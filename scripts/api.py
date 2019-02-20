#! /usr/bin/env python3

from flask import Flask, request, jsonify, make_response, Response
import json, re, sys, os, traceback, copy, argparse
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts, rutils

####################
# global variables #
###################

DB_MANAGER = None #for running database queries
app = Flask(__name__) # WSGI entry point
geos = dict() #for building and caching geo data

#################
# api endpoints #
#################

# return aggregated data for the given time period (in minutes, called by refine)
@app.route('/api/refine/<n>')
def refine(n):
    global DB_MANAGER
    try:
        response = make_response(jsonify({"bursts": GetBursts(n), "macMan": MacMan(), "manDev": ManDev(), "impacts": GetImpacts(n), "usage": GenerateUsage()}))
            
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except:
        print("Unexpected error:", sys.exc_info())
        traceback.print_exc()
        sys.exit(-1)                    

# get the mac address, manufacturer, and custom name of every device
@app.route('/api/devices')
def devices():
    global DB_MANAGER
    return jsonify({"macMan": MacMan(), "manDev": ManDev()})

# set the custom name of a device with a given mac
@app.route('/api/setdevice/<mac>/<name>')
def set_device(mac, name):
    global DB_MANAGER
    mac_format = re.compile('^(([a-fA-F0-9]){2}:){5}[a-fA-F0-9]{2}$')
    if mac_format.match(mac) is not None:
        DB_MANAGER.execute("UPDATE devices SET name=%s WHERE mac=%s", (name, mac))
        return jsonify({"message": "Device with mac " + mac + " now has name " + name})
    else:
        return jsonify({"message": "Invalid mac address given"})

@app.route('/api/aretha/counterexample/<question>')
def counterexample(question):
    ce = GetCounterexample(question)
    if ce:
        return jsonify({"name": ce[0], "traffic": ce[1]})
    else:
        return jsonify({"name": "", "traffic": 0})

# open an event stream for database updates
@app.route('/stream')
def stream():
    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

####################
# internal methods #
####################

#return a dictionary of mac addresses to manufacturers
def MacMan():
    macMan = dict()
    devices = DB_MANAGER.execute("SELECT * FROM devices", ())
    for device in devices:
        mac,manufacturer,_ = device
        macMan[mac] = manufacturer
    return macMan

#return a dictionary of mac addresses to custom device names
def ManDev():
    manDev = dict()
    devices = DB_MANAGER.execute("SELECT * FROM devices", ())
    for device in devices:
        mac,_,name = device
        manDev[mac] = name
    return manDev

#get geo data for an ip
def GetGeo(ip):
    #print("Get Geo ", ip)
    try:
        lat,lon,c_code,c_name = DB_MANAGER.execute("SELECT lat, lon, c_code, c_name FROM geodata WHERE ip=%s LIMIT 1", (ip,), False)
        geo = {"latitude": lat, "longitude": lon, "country_code": c_code, "companyName": c_name}
        return geo
    except:
        geo = {"latitude": 0, "longitude": 0, "country_code": 'XX', "companyName": 'unknown'}
        return geo

#get bursts for the given time period (in days)
def GetBursts(n, units="MINUTES"):
    bursts = DB_MANAGER.execute("SELECT MIN(time), MIN(mac), burst, MIN(categories.name) FROM packets JOIN bursts ON bursts.id = packets.burst JOIN categories ON categories.id = bursts.category WHERE time > (NOW() - INTERVAL %s) GROUP BY burst ORDER BY burst", ("'" + str(n) + " " + units + "'",)) #  " DAY'",))
    result = []
    epoch = datetime(1970, 1, 1, 0, 0)
    for burst in bursts:
        unixTime = int((burst[0] - epoch).total_seconds() * 1000.0)
        device = burst[1]
        category = burst[3]
        result.append({"value": unixTime, "category": category, "device": device })
    return result

def GetCounterexample(question):
    options = []
    if int(question) == 1:
        options = DB_MANAGER.execute("SELECT c_name, count(p.len) FROM packets AS p INNER JOIN geodata AS g ON p.src = g.ip WHERE g.c_name LIKE '*%%' GROUP BY c_name ORDER BY count(p.len) DESC LIMIT 5;", ())
   
    blacklist = ["*Amazon.com, Inc.", "*Google LLC", "*Facebook, Inc."]
    for option in options:
        if option[0] not in blacklist:
            return option

    return False

#setter method for impacts
def _update_impact(impacts, mac, ip, impact):
    if mac in impacts:
        if ip in impacts[mac]:
            impacts[mac][ip] += impact
        else:
            impacts[mac][ip] = impact #impact did not exist
    else:
        impacts[mac] = dict()
        impacts[mac][ip] = impact #impact did not exist


def packet_to_impact(impacts, packet):
    global geos
    #determine if the src or dst is the external ip address
    pkt_id, pkt_time, pkt_src, pkt_dst, pkt_mac, pkt_len, pkt_proto, pkt_burst = packet["id"], packet.get('time'), packet["src"], packet["dst"], packet["mac"], packet["len"], packet.get("proto"), packet.get("burst")
    
    local_ip_mask = rutils.make_localip_mask() #so we can filter for local ip addresses
    ip_src = local_ip_mask.match(pkt_src) is not None
    ip_dst = local_ip_mask.match(pkt_dst) is not None
    ext_ip = None
    
    if (ip_src and ip_dst) or (not ip_src and not ip_dst):
        return #shouldn't happen, either 0 or 2 internal hosts
    
    #remember which ip address was external
    elif ip_src:
        ext_ip = pkt_dst
    else:
        ext_ip = pkt_src
    
    #make sure we have geo data, then update the impact
    if ext_ip not in geos:
        geos[ext_ip] = GetGeo(ext_ip)

    _update_impact(impacts, pkt_mac, ext_ip, pkt_len)

def CompileImpacts(impacts, packets):
    # first run packet_to_impact
    [packet_to_impact(impacts, packet) for packet in packets]

    result = []
    for mmac, ipimpacts in impacts.items():
        for ip, impact in ipimpacts.items():
            item = geos.get(ip, None)
            if item is None:  # we might have just killed the key 
                continue
            item = item.copy() 
            # note: geos[ip] should never be none because the invariant is that packet_to_impact has been
            # called BEFORE this point, and that populates the geos. Yeah, ugly huh. I didn't write this
            # code, don't blame me!
            item['impact'] = impact
            item['companyid'] = ip
            item['appid'] = mmac
            if item['impact'] > 0:
                result.append(item)
            pass
    return result

def GetImpacts(n, units="MINUTES"):
    global geos
    #print("GetImpacts: ::", n, ' ', units)
    #we can only keep the cache if we're looking at the same packets as the previous request

    impacts = dict() # copy.deepcopy(_impact_cache) 
    # get all packets from the database (if we have cached impacts from before, then only get new packets)
    packetrows = DB_MANAGER.execute("SELECT * FROM packets WHERE time > (NOW() - INTERVAL %s)", ("'" + str(n) + " " + units + "'",)) 
    packets = [dict(zip(['id', 'time', 'src', 'dst', 'mac', 'len', 'proto', 'burst'], packet)) for packet in packetrows]
    #print("got ", len(packets), "packets")

    result = CompileImpacts(impacts, packets)
    return result #shipit

# Generate fake usage for devices (a hack so they show up in refine)
def GenerateUsage():
    usage = []
    counter = 1
    for mac in MacMan():
        usage.append({"appid": mac, "mins": counter})
        counter += 1
    return usage

_events = []

def event_stream():
    import time

    def packets_insert_to_impact(packets):        
        impacts = CompileImpacts(dict(),packets)
        #print("packets insert to pitt ", len(packets), " resulting impacts len ~ ", len(impacts))
        return impacts
    
    try:
        while True:
            time.sleep(0.5)
            insert_buf = []
            geo_updates = []
            device_updates = []

            while len(_events) > 0:
                event_str = _events.pop(0)
                event = json.loads(event_str)
                if event["operation"] in ['UPDATE','INSERT'] and event["table"] == 'packets':
                    event['data']['len'] = int(event['data'].get('len'))
                    insert_buf.append(event["data"])
                if event["operation"] in ['UPDATE','INSERT'] and event["table"] == 'geodata':
                    #print("Geodata update", event["data"])
                    geo_updates.append(event["data"])
                if event["operation"] in ['UPDATE','INSERT'] and event["table"] == 'devices':
                    #print("Device update", event["data"])                    
                    device_updates.append(event["data"])

            if len(insert_buf) > 0: 
                yield "data: %s\n\n" % json.dumps({"type":'impact', "data": packets_insert_to_impact(insert_buf)})
            if len(geo_updates) > 0:
                #print("Got a geo updates for %s, must reset GEO cache." % [u["ip"] for u in geo_updates])
                [geos.pop(u["ip"], None) for u in geo_updates]
                yield "data: %s\n\n" % json.dumps({"type":'geodata'})
            if len(device_updates) > 0: 
                yield "data: %s\n\n" % json.dumps({"type":'device', "data": packets_insert_to_impact(insert_buf)})

    except GeneratorExit:
        return;
    except:
        print("Unexpected error:", sys.exc_info())
        traceback.print_exc()                
        return

@app.before_first_request
def init():
    global DB_MANAGER
    DB_MANAGER = databaseBursts.dbManager()
    listenManager = databaseBursts.dbManager()
    listenManager.listen('db_notifications', lambda payload:_events.append(payload))

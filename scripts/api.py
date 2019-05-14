#! /usr/bin/env python3

from flask import Flask, request, jsonify, make_response, Response
import json, re, sys, os, traceback, copy, argparse, subprocess, time
from datetime import datetime, timedelta
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts, rutils

####################
# global variables #
####################

DB_MANAGER = None #for running database queries
app = Flask(__name__) # WSGI entry point
geos = dict() #for building and caching geo data

#################
# api endpoints #
#################

# return impacts per <delta> from <start> to <end>
# delta in seconds, <start>/<end> as unix timestamps
@app.route('/api/impacts/<start>/<end>/<delta>')
def refine(start, end, delta):
    global DB_MANAGER
    try:
        #sanitise inputs
        start = datetime.fromtimestamp(int(start))
        end = datetime.fromtimestamp(int(end))
        delta = timedelta(seconds=abs(int(delta)))
        
        #clip start and end
        start = start if start >= datetime.fromtimestamp(0) else datetime.fromtimestamp(0)
        end = end if end < datetime.now() else datetime.now()

        #get all packets between <start> and <end>
        impacts = dict()

        #get a list of buckets to aggregate impacts into
        buckets = generate_buckets(start, end, delta)
        impacts = dict()
        print(buckets)

        #process impacts per bucket
        for i in range(len(buckets) - 1):
            #get all of the packets in the bucket
            packets = DB_MANAGER.execute("SELECT * FROM packets WHERE time < timestamp %s AND time > timestamp %s", (buckets[i].isoformat(), buckets[i+1].isoformat()))
            bucket_impacts = dict()
            
            #calculate impacts per ip per device
            for packet in packets:
                time = packet[1]
                ip = get_external_address(packet[2], packet[3])
                mac = packet[4]
                if ip not in bucket_impacts:
                    bucket_impacts[ip] = dict()
                if mac not in bucket_impacts[ip]:
                    bucket_impacts[ip][mac] = 0
                bucket_impacts[ip][mac] += packet[5]
                packets.remove(packet)
            impacts[str(buckets[i].isoformat())] = bucket_impacts

        response = make_response(jsonify(impacts))
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
@app.route('/api/devices/set/<mac>/<name>')
def set_device(mac, name):
    global DB_MANAGER
    mac_format = re.compile('^(([a-fA-F0-9]){2}:){5}[a-fA-F0-9]{2}$')
    if mac_format.match(mac) is not None:
        DB_MANAGER.execute("UPDATE devices SET name=%s WHERE mac=%s", (name, mac))
        return jsonify({"message": "Device with mac " + mac + " now has name " + name})
    else:
        return jsonify({"message": "Invalid mac address given"})

# return a counter example to a question posed by aretha
# 1 == trackers/advertisers
# 2 == unencrypted http traffic (not yet implemented)
# 3 == haveibeenpwned (not yet implemented)
@app.route('/api/aretha/counterexample/<question>')
def counterexample(question):
    ce = GetCounterexample(question)
    if ce:
        return jsonify({"destination": ce[0], "traffic": ce[1], "device": ce[2]})
    else:
        return jsonify({"destination": "", "traffic": 0, "device": 0})

# add a firewall rule as dictated by aretha
@app.route('/api/aretha/enforce/<destination>')
def enforce_dest(destination):
    if DB_MANAGER.execute('INSERT INTO rules(c_name) VALUES(%s); SELECT id FROM rules WHERE c_name = %s', (destination,destination)):
        return jsonify({"message": f"destination only rule added for {destination}", "success": True})
    else:
        return jsonify({"message": f"error while creating destination only rule for {destination}", "success": False})
    pass

# add a firewall rule as dictated by aretha
@app.route('/api/aretha/enforce/<destination>/<device>')
def enforce_dest_dev(destination, device):
    if DB_MANAGER.execute('INSERT INTO rules(device, c_name) VALUES(%s, %s); SELECT id FROM rules WHERE c_name = %s AND device = %s', (device, destination, destination, device)):
        return jsonify({"message": f"device to destination rule added for {device} to {destination}", "success": True})
    else:
        return jsonify({"message": f"error while creating device to destination rule for {device} to {destination}", "success": False})

# remove a firewall rule as dictated by aretha
@app.route('/api/aretha/unenforce/<destination>')
def unenforce_dest(destination):
    blocked_ips = DB_MANAGER.execute("SELECT r.c_name, r.device, b.ip FROM rules AS r RIGHT JOIN blocked_ips AS b ON r.id = b.rule WHERE r.c_name = %s AND r.device IS NULL", (destination,))

    for ip in blocked_ips:
        if sys.platform.startswith("linux"):
            if ip[1] is None:
                subprocess.run(["sudo", "iptables", "-D", "INPUT", "-s", ip[2], "-j", "DROP"])
                subprocess.run(["sudo", "iptables", "-D", "OUTPUT", "-d", ip[2], "-j", "DROP"])
        else:
            print(f"ERROR: platform {sys.platform} is not linux - cannot remove block on {ip[2]}")
            return jsonify({"message": f"error removing rule for {destination}", "success": False})
    DB_MANAGER.execute("DELETE FROM rules WHERE c_name = %s AND device IS NULL", (destination,))
    return jsonify({"message": f"rule removed for {destination}", "success": True})

# remove a firewall rule as dictated by aretha
@app.route('/api/aretha/unenforce/<destination>/<device>')
def unenforce_dest_dev(destination, device):
    blocked_ips = DB_MANAGER.execute("SELECT r.c_name, r.device, b.ip FROM rules AS r RIGHT JOIN blocked_ips AS b ON r.id = b.rule WHERE r.c_name = %s and r.device = %s", (destination, device))

    for ip in blocked_ips:
        if sys.platform.startswith("linux") or True:
            if ip[1] is not None:
                subprocess.run(["sudo", "iptables", "-D", "FORWARD", "-d", ip[2], "-m", "mac", "--mac-source", ip[1], "-j", "DROP"])
        else:
            print(f"ERROR: platform {sys.platform} is not linux - cannot remove block on {ip[2]}")
            return jsonify({"message": f"error removing rule for {destination}/{device}", "success": False})
    DB_MANAGER.execute("DELETE FROM rules WHERE c_name = %s AND device = %s", (destination,device))
    return jsonify({"message": f"rule removed for {destination}/{device}", "success": True})

# open an event stream for database updates
@app.route('/stream')
def stream():
    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

####################
# internal methods #
####################

#generate a list of buckets from a start, end, and delta
def generate_buckets(start, end, delta):
    buckets = []
    buckets.append(end)

    #loop through making <delta> sized buckets until we've accounted for the whole period
    while end > start:
        end = end - delta if (end - delta) > start else start
        buckets.append(end)

    return buckets

def get_external_address(pkt_src, pkt_dst):

    #get the mask and apply it to both addresses
    local_ip_mask = rutils.make_localip_mask() 
    ip_src = local_ip_mask.match(pkt_src) is not None
    ip_dst = local_ip_mask.match(pkt_dst) is not None
    
    if ip_src:
        return pkt_dst
    else:
        return pkt_src

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

def GetCounterexample(question):
    options = []
    if int(question) == 1:
        options = DB_MANAGER.execute("select c_name, count(p.len), d.name from packets as p inner join geodata as g on p.src = g.ip inner join devices as d on p.mac = d.mac where g.c_name like '*%%' group by g.c_name, d.name order by count(p.len) desc limit 5;", ())
   
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


#def packet_to_impact(impacts, packet):
#    global geos
#    #determine if the src or dst is the external ip address
#    pkt_id, pkt_time, pkt_src, pkt_dst, pkt_mac, pkt_len, pkt_proto, pkt_burst = packet["id"], packet.get('time'), packet["src"], packet["dst"], packet["mac"], packet["len"], packet.get("proto"), packet.get("burst")
#    
#    local_ip_mask = rutils.make_localip_mask() #so we can filter for local ip addresses
#    ip_src = local_ip_mask.match(pkt_src) is not None
#    ip_dst = local_ip_mask.match(pkt_dst) is not None
#    ext_ip = None
#    
#    if (ip_src and ip_dst) or (not ip_src and not ip_dst):
#        return #shouldn't happen, either 0 or 2 internal hosts
#    
#    #remember which ip address was external
#    elif ip_src:
#        ext_ip = pkt_dst
#    else:
#        ext_ip = pkt_src
#    
#    #make sure we have geo data, then update the impact
#    if ext_ip not in geos:
#        geos[ext_ip] = GetGeo(ext_ip)
#
#    _update_impact(impacts, pkt_mac, ext_ip, pkt_len)
#
#def CompileImpacts(impacts, packets):
#    # first run packet_to_impact
#    [packet_to_impact(impacts, packet) for packet in packets]
#
#    result = []
#    for mmac, ipimpacts in impacts.items():
#        for ip, impact in ipimpacts.items():
#            item = geos.get(ip, None)
#            if item is None:  # we might have just killed the key 
#                continue
#            item = item.copy() 
#            # note: geos[ip] should never be none because the invariant is that packet_to_impact has been
#            # called BEFORE this point, and that populates the geos. Yeah, ugly huh. I didn't write this
#            # code, don't blame me!
#            item['impact'] = impact
#            item['companyid'] = ip
#            item['appid'] = mmac
#            if item['impact'] > 0:
#                result.append(item)
#            pass
#    return result

#def GetImpacts(n, units="MINUTES"):
#    global geos
#    impacts = dict() 
#    # get relevant packets from the database 
#    packetrows = DB_MANAGER.execute("SELECT * FROM packets WHERE time > (NOW() - INTERVAL %s)", ("'" + str(n) + " " + units + "'",)) 
#    packets = [dict(zip(['id', 'time', 'src', 'dst', 'mac', 'len', 'proto', 'burst'], packet)) for packet in packetrows]
#    result = CompileImpacts(impacts, packets)
#    return result #shipit

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

## This is run using Flask
## export FLASK_APP=apy
## export FLASK_DEBUG=1
## export FLASK_PORT=X
## flask run


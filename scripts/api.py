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
def impacts(start, end, delta):
    global DB_MANAGER
    try:
        #convert inputs to minutes
        start = round(int(start)/60)
        end = round(int(end)/60)
        delta = abs(round(int(delta)))

        #refresh view and get per minute impacts from <start> to <end>
        raw_impacts = DB_MANAGER.execute("REFRESH MATERIALIZED VIEW impacts; SELECT * FROM impacts WHERE mins >= %s AND mins <= %s", (start, end))

        #process impacts per bucket
        impacts = dict()
        bucket_impacts = dict()
        pointer = start
            
        for impact in raw_impacts:
            mac = impact[0]
            ip = impact[1]
            mins = impact[2]
            total = int(impact[3])

            #fast forward to correct bucket
            while  mins > pointer + delta:
                impacts[str(pointer)] = bucket_impacts
                pointer += delta

            #add impacts
            if ip not in bucket_impacts:
                bucket_impacts[ip] = dict()
            if mac not in bucket_impacts[ip]:
                bucket_impacts[ip][mac] = 0
            bucket_impacts[ip][mac] += total
        impacts[str(pointer)] = bucket_impacts

        #add geo and device data
        geos = get_geodata()
        devices = get_device_info()

        response = make_response(jsonify({"impacts": impacts, "geodata": geos, "devices": devices}))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except:
        print("Unexpected error:", sys.exc_info())
        traceback.print_exc()
        sys.exit(-1)                    

# return aggregated impacts from <start> to <end>
# <start>/<end> as unix timestamps
@app.route('/api/impacts/<start>/<end>')
def impacts_aggregated(start, end):
    global DB_MANAGER
    try:
        #convert inputs to minutes
        start = round(int(start)/60)
        end = round(int(end)/60)

        #refresh view and get per minute impacts from <start> to <end>
        raw_impacts = DB_MANAGER.execute("REFRESH MATERIALIZED VIEW impacts; SELECT mac, ext, sum(impact) FROM impacts WHERE mins > %s AND mins < %s group by mac, ext", (start, end))

        impacts = dict()

        for impact in raw_impacts:
            mac = impact[0]
            ip = impact[1]
            total = int(impact[2])

            if ip not in impacts:
                impacts[ip] = dict()
            if mac not in impacts[ip]:
                impacts[ip][mac] = 0
            impacts[ip][mac] += total
       
        result = []
        for ip in impacts:
            for mac in impacts[ip]:
                result.append({"company": ip, "impact": impacts[ip][mac], "device": mac})

        #add geo and device data
        geos = get_geodata()
        devices = get_device_info()

        response = make_response(jsonify({"impacts": result, "geodata": geos, "devices": devices}))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except:
        print("Unexpected error:", sys.exc_info())
        traceback.print_exc()
        sys.exit(-1)                    

#get the mac address, manufacturer, and custom name of every device
@app.route('/api/devices')
def devices():
    return jsonify({"devices": get_device_info()})

#get geodata about all known ips
@app.route('/api/geodata')
def geodata():
    return jsonify({"geodata": get_geodata()})

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

# return examples to be used for educational components
@app.route('/api/example/<question>')
def counterexample(question):
    example = GetExample(question)
    if "text" in example:
        response = make_response(jsonify({"text": example["text"], "impacts": example["impacts"], "geodata": example["geodata"], "devices": example["devices"]}))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    else:
        return jsonify({"message": f"Unable to find a match for requested example"})

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
@app.route('/api/stream')
def stream():
    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# return a list of live but not completed content
@app.route('/api/content')
def content():
    response = make_response(jsonify(DB_MANAGER.execute("select * from content where live < current_timestamp and complete = false", ())))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/api/content/set/<name>')
def contentSet(name):
    DB_MANAGER.execute("update content set complete = true where name = %s", (name,))
    response = make_response(jsonify({"message": "Request processed", "success": "unknown"}))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

####################
# internal methods #
####################

#return a dictionary of mac addresses to manufacturers and names
def get_device_info():
    devices = dict()
    raw_devices = DB_MANAGER.execute("SELECT * FROM devices", ())
    for device in raw_devices:
        mac, manufacturer, name = device
        devices[mac] = {"manufacturer": manufacturer, "name": name}
    return devices

#get geo data for all ips
def get_geodata():
    geos = DB_MANAGER.execute("SELECT ip, lat, lon, c_code, c_name FROM geodata", ())
    records = []
    for geo in geos:
        records.append({"ip": geo[0], "latitude": geo[1], "longitude": geo[2], "country_code": geo[3], "company_name": geo[4]})
    return records

def GetExample(question):
    result = dict()
    if question == "encryption":
        example = DB_MANAGER.execute("select ext, mac, sum(len) from packets where proto = 'HTTP' group by ext, mac order by sum(len) desc limit 1;", ())[0]
        dest = example[0]
        mac = example[1]
        geo = DB_MANAGER.execute("select lat, lon, c_name, c_code from geodata where ip = %s limit 1", (dest,))[0]
        device = DB_MANAGER.execute("select name from devices where mac = %s", (mac,))[0][0]
        lat = geo[0]
        lon = geo[1]
        company = geo[2]
        country = geo[3]

        result["text"] = f"Did you know that your {device} sends unencrypted data to {company} (in {country})?"
        result["impacts"] = [{"company": dest, "device": mac, "impact": example[2]}]
        result["geodata"] = [{"latitude": lat, "longitude": lon, "ip": dest}] #, "company_name": company, "country_code", }]
        result["devices"] = [mac]
    return result
        #options = DB_MANAGER.execute("select c_name, count(p.len), d.name from packets as p inner join geodata as g on p.src = g.ip inner join devices as d on p.mac = d.mac where g.c_name like '*%%' group by g.c_name, d.name order by count(p.len) desc limit 5;", ())
   
    #blacklist = ["*Amazon.com, Inc.", "*Google LLC", "*Facebook, Inc."]
    #for option in options:
        #if option[0] not in blacklist:
            #return option

@app.before_first_request
def init():
    global DB_MANAGER
    DB_MANAGER = databaseBursts.dbManager()
    listenManager = databaseBursts.dbManager()
    listenManager.listen('db_notifications', lambda payload:event_queue.append(payload))

################
# event stream #
################

event_queue = []
def event_stream():
    import time

    try:
        while True:
            time.sleep(0.1)
            packet_buf = []
            geo_buf = []
            device_buf = []

            while len(event_queue) > 0:
                event_str = event_queue.pop(0)
                event = json.loads(event_str)
                if event["operation"] in ['UPDATE','INSERT'] and event["table"] == 'packets':
                    event['data']['len'] = int(event['data'].get('len'))
                    packet_buf.append(event["data"])
                if event["operation"] in ['UPDATE','INSERT'] and event["table"] == 'geodata':
                    geo_buf.append(event["data"])
                if event["operation"] in ['UPDATE','INSERT'] and event["table"] == 'devices':
                    device_buf.append(event["data"])

            if len(packet_buf) > 0: 
                impacts = dict()
            
                for packet in packet_buf:
                    mac = packet['mac']
                    ip = packet['ext']
                    impact = packet['len']

                    if ip not in impacts:
                        impacts[ip] = dict()
                    if mac not in impacts[ip]:
                        impacts[ip][mac] = 0
                    impacts[ip][mac] += impact

                yield "data: %s\n\n" % json.dumps({"type": "impact", "time": round(time.time()/60)-1, "data": impacts})

            if len(geo_buf) > 0:
                [geos.pop(geo["ip"], None) for geo in geo_buf]
                for geo in geo_buf:
                    yield "data: %s\n\n" % json.dumps({"type":"geodata", "data": geo})

            if len(device_buf) > 0: 
                for device in device_buf:
                    yield "data: %s\n\n" % json.dumps({"type":'device', "data": device})

    except GeneratorExit:
        return;
    except:
        print("Unexpected error:", sys.exc_info())
        traceback.print_exc()                
        return

## This is run using Flask
## export FLASK_APP=apy
## export FLASK_DEBUG=1
## export FLASK_PORT=X
## flask run


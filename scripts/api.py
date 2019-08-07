#! /usr/bin/env python3

import json
import os
import re
import subprocess
import sys
import traceback
import urllib
import configparser
import socket
from datetime import datetime
from flask import Flask, jsonify, make_response, Response

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts

####################
# global variables #
####################

DB_MANAGER = None  # for running database queries
app = Flask(__name__)  # WSGI entry point
geos = dict()  # for building and caching geo data
IOTR_BASE = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
CONFIG_PATH = IOTR_BASE + "/config/config.cfg"
CONFIG = None


#################
# api endpoints #
#################
# return impacts per <delta> from <start> to <end>
# delta in seconds, <start>/<end> as unix timestamps
@app.route('/api/impacts/<start>/<end>/<delta>')
def impacts(start, end, delta):
    global DB_MANAGER
    try:
        # convert inputs to minutes
        start = round(int(start)/60)
        end = round(int(end)/60)
        delta = abs(round(int(delta)))

        # refresh view and get per minute impacts from <start> to <end>
        raw_impacts = DB_MANAGER.execute("SELECT * FROM impacts WHERE mins >= %s AND mins <= %s", (start, end))

        # process impacts per bucket
        impacts = dict()
        pointer = start
            
        for impact in raw_impacts:
            mac = impact[0]
            ip = impact[1]
            mins = int(impact[2])
            total = int(impact[3])

            # fast forward to correct bucket
            while mins > pointer + delta:
                pointer += delta
            
            # load current state of that bucket
            if str(pointer) not in impacts:
                impacts[str(pointer)] = dict()
            bucket_impacts = impacts[str(pointer)]

            # add impacts to bucket
            if mac not in bucket_impacts:
                bucket_impacts[mac] = dict()
            if ip not in bucket_impacts[mac]:
                bucket_impacts[mac][ip] = 0
            bucket_impacts[mac][ip] += total

            # save bucket state
            impacts[str(pointer)] = bucket_impacts
        
        # add geo and device data
        geos = get_geodata()
        devices = get_device_info()
        response = make_response(jsonify({"impacts": impacts, "geodata": geos, "devices": devices}))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except:
        return jsonify({"message": "There was an error processing the request"})


# return aggregated impacts from <start> to <end>
# <start>/<end> as unix timestamps
@app.route('/api/impacts/<start>/<end>')
def impacts_aggregated(start, end):
    global DB_MANAGER
    try:
        # convert inputs to minutes
        start = round(int(start)/60)
        end = round(int(end)/60)

        # refresh view and get per minute impacts from <start> to <end>
        raw_impacts = DB_MANAGER.execute("SELECT mac, ext, sum(impact) FROM impacts WHERE mins > %s AND mins < %s group by mac, ext", (start, end))

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

        # add geo and device data
        geos = get_geodata()
        devices = get_device_info()

        response = make_response(jsonify({"impacts": result, "geodata": geos, "devices": devices}))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except:
        return jsonify({"message": "There was an error processing the request"})


# get the mac address, manufacturer, and custom name of every device
@app.route('/api/devices')
def devices():
    response =  make_response(jsonify({"devices": get_device_info()}))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


# get geodata about all known ips
@app.route('/api/geodata')
def geodata():
    response = make_response(jsonify({"geodata": get_geodata()}))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


# set the custom name of a device with a given mac
@app.route('/api/devices/set/<mac>/<name>')
def set_device(mac, name):
    global DB_MANAGER
    mac_format = re.compile('^(([a-fA-F0-9]){2}:){5}[a-fA-F0-9]{2}$')
    if mac_format.match(mac) is not None:
        DB_MANAGER.execute("UPDATE devices SET name=%s WHERE mac=%s", (name, mac))
        response = make_response(jsonify({"message": "Device with mac " + mac + " now has name " + name}))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    else:
        return jsonify({"message": "Invalid mac address given"})


# return examples to be used for educational components
@app.route('/api/example/<question>')
def counterexample(question):
    example = GetExample(question)
    if example is not False:
        response = make_response(jsonify({"text": example["text"], "impacts": example["impacts"], "geodata": example["geodata"], "devices": example["devices"]}))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    else:
        response = make_response(jsonify({"message": f"Unable to find a match for requested example"}))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response


# return a list of firewall rules
@app.route('/api/aretha/list')
def list_rules():
    fw_on = DB_MANAGER.execute("select complete from content where name = 'S3'", ())[0][0]
    rules = DB_MANAGER.execute("select r.id, r.device, d.name, r.c_name from rules as r inner join devices as d on r.device = d.mac", ())
    response = make_response(jsonify({"rules": rules, "enabled": fw_on}))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


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
        response = jsonify({"message": f"device to destination rule added for {device} to {destination}", "success": True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    else:
        return jsonify({"message": f"error while creating device to destination rule for {device} to {destination}", "success": False})


# remove a firewall rule as dictated by aretha
@app.route('/api/aretha/unenforce/<destination>')
def unenforce_dest(destination):
    blocked_ips = DB_MANAGER.execute("SELECT r.c_name, r.device, b.ip FROM rules AS r RIGHT JOIN blocked_ips AS b ON r.id = b.rule WHERE r.c_name = %s AND r.device IS NULL", (destination,))

    if sys.platform.startswith("linux"):
        for ip in blocked_ips:
            if ip[1] is None:
                subprocess.run(["sudo", "iptables", "-D", "INPUT", "-s", ip[2], "-j", "DROP"])
                subprocess.run(["sudo", "iptables", "-D", "OUTPUT", "-d", ip[2], "-j", "DROP"])
                subprocess.run(["sudo", "dpkg-reconfigure", "-p", "critical", "iptables-persistent"])
    
    DB_MANAGER.execute("DELETE FROM rules WHERE c_name = %s AND device IS NULL", (destination,))
    response = jsonify({"message": f"rule removed for {destination}", "success": True})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


# remove a firewall rule as dictated by aretha
@app.route('/api/aretha/unenforce/<destination>/<device>')
def unenforce_dest_dev(destination, device):
    blocked_ips = DB_MANAGER.execute("SELECT r.c_name, r.device, b.ip FROM rules AS r RIGHT JOIN blocked_ips AS b ON r.id = b.rule WHERE r.c_name = %s and r.device = %s", (destination, device))

    if sys.platform.startswith("linux"):
        for ip in blocked_ips:
            if ip[1] is not None:
                subprocess.run(["sudo", "iptables", "-D", "FORWARD", "-d", ip[2], "-m", "mac", "--mac-source", ip[1], "-j", "DROP"])
                subprocess.run(["sudo", "iptables", "-D", "FORWARD", "-s", ip[2], "-m", "mac", "--mac-source", ip[1], "-j", "DROP"])
                subprocess.run(["sudo", "dpkg-reconfigure", "-p", "critical", "iptables-persistent"])
    
    DB_MANAGER.execute("DELETE FROM rules WHERE c_name = %s AND device = %s", (destination,device))
    response = jsonify({"message": f"rule removed for {destination}/{device}", "success": True})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


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


# mark content as set, and record the pre and post responses
@app.route('/api/content/set/<name>/<pre>/<post>')
def contentSet(name, pre, post):
    DB_MANAGER.execute("update content set complete = true, pre = %s, post = %s where name = %s", (pre[:200], post[:200], name))
    response = make_response(jsonify({"message": "Request processed", "success": "unknown"}))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


# return records for the redaction interface
@app.route('/api/redact')
def getRedact():
    response = make_response(jsonify(DB_MANAGER.execute("select distinct c_name from geodata", ())))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


# remove records for the redaction interface
@app.route('/api/redact/set/<company>')
def setRedact(company):
    ips = DB_MANAGER.execute("select ip from geodata where c_name = %s", (company,));
    for ip in ips:
        DB_MANAGER.execute("delete from packets where ext = %s", (ip[0],))
        DB_MANAGER.execute("delete from geodata where ip = %s", (ip[0],))
    response = make_response(jsonify({"message": "operation successful"}))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/api/pid')
def getPid():
    global CONFIG
    if CONFIG is not None and 'general' in CONFIG and 'id' in CONFIG['general']:
        response = make_response(jsonify({"pid": CONFIG['general']['id']}))
    else:
        response = make_response(jsonify({"pid": "unknown"}))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/api/activity/<pid>/<category>/<action>')
def activity(pid, category, action):
    DB_MANAGER.execute("insert into activity(pid, category, description) values(%s, %s, %s)", (pid, category, action))
    response = make_response(jsonify({"message": "activity logged"}))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

####################
# internal methods #
####################
# return a dictionary of mac addresses to manufacturers and names
def get_device_info():
    devices = dict()
    raw_devices = DB_MANAGER.execute("SELECT * FROM devices", ())
    for device in raw_devices:
        mac, manufacturer, name = device
        devices[mac] = {"manufacturer": manufacturer, "name": name}
    return devices


# get geo data for all ips
def get_geodata():
    geos = DB_MANAGER.execute("SELECT ip, lat, lon, c_code, c_name, domain FROM geodata", ())
    records = []    

    for geo in geos:
        # try:
        #     subdomain = socket.gethostbyaddr(geo[0]) if geo[5] == 'unknown' else geo[5]
        #     print("subdomain", geo[0], subdomain)
        # except:
        #     print("Unexpected error:", sys.exc_info()[0])
        records.append({"ip": geo[0], "latitude": geo[1], "longitude": geo[2], "country_code": geo[3], "company_name": geo[4], "domain":geo[5]})
    return records


def GetExample(question):
    result = dict()
    result["text"] = []
    result["impacts"] = []
    result["geodata"] = []
    result["devices"] = []

    if question == "S1" or question == "S2":
        result["text"] = "Some content will be illustrated with examples from your home network. When they do, they'll appear here."

    elif question == "B4":
        try:
            example = DB_MANAGER.execute("select ext, mac, sum(len) from packets where proto = 'HTTP' group by ext, mac order by sum(len) desc limit 1;", ())[0]
        except:
            return False
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
        result["geodata"] = [{"latitude": lat, "longitude": lon, "ip": dest}]
        result["devices"] = [mac]

    elif question == "D2":
        example = DB_MANAGER.execute("select d.name, count(distinct g.ip) from packets as p inner join geodata as g on p.ext = g.ip inner join devices as d on p.mac = d.mac where g.tracker = true group by d.name order by count(distinct g.ip) desc", ())
        if len(example) < 1:
            return False
        device = example[0][0]
        single_tracker = example[0][1]
        total_tracker = 0
        for record in example:
            total_tracker += record[1]
        result["text"] = f"Across the devices connected to the privacy assistant there are connections to {total_tracker} different companies that have been known to track users across the internet. Did you know that your {device} sends data to {single_tracker} of these companies?"

    elif question == "D3":
        example1 = DB_MANAGER.execute("select count(mac) from devices", ())[0][0]
        example2 = DB_MANAGER.execute("select count(distinct d.mac) from devices as d inner join packets as p on d.mac = p.mac inner join geodata as g on p.ext = g.ip where g.c_name = 'Google LLC'", ())[0][0]
        result["text"] = f"Of the {example1} devices connected to Aretha, {example2} of them send data to Google."
   
    elif question == "D4":
        example = DB_MANAGER.execute("select distinct g.c_name, d.name from geodata as g left join packets as p on g.ip = p.ext left join devices as d on p.mac = d.mac", ())
        req = urllib.request.Request("https://haveibeenpwned.com/api/v2/breaches", headers={"User-Agent" : "IoT-Refine"})
        with urllib.request.urlopen(req) as url:
            data = json.loads(url.read().decode())
            for company in example:
                device = company[1]
                for breach in data:
                    if company[0].strip(" LLC").strip(", Inc.").strip(" Inc.") == breach["Name"]:
                        result["text"] = f"Did you know that {company[0]} (that communicates with your {device}) was the victim of a data breach on {breach['BreachDate']} where {breach['PwnCount']} records were stolen? If you didn't know about this, you might want to change your passwords with the company."
                        break
        if not result["text"]:
            result["text"] = "Thankfully, none of your devices communicate with companies on our data breach list."

    elif question == "frequency":
        example1 = DB_MANAGER.execute("select d.mac, d.name, count(p.id) from packets as p inner join devices as d on p.mac = d.mac group by d.mac order by count(id) desc limit 1", ())
        if len(example1) == 0:
            return False
        example2 = DB_MANAGER.execute("select time from packets where mac = %s order by time asc limit 1", (example1[0][0],))
        example3 = DB_MANAGER.execute("select time from packets where mac = %s order by time desc limit 1", (example1[0][0],))
        _, device, count = example1[0]
        start = datetime.fromisoformat(str(example2[0][0]))
        end = datetime.fromisoformat(str(example3[0][0]))
        result["text"] = f"Your {device} has sent {'{:,}'.format(count)} 'packets' of data in the last {(end - start).days} days. On average, that's once every {((end - start) / count).seconds}.{((end - start) / count).microseconds} seconds."

    elif question == "B2":
        example = DB_MANAGER.execute("select name,c_name,ext from packets as p inner join devices as d on p.mac = d.mac inner join geodata as g on p.ext = g.ip order by time desc limit 1;", ())
        result["text"] = f"For example, your {example[0][0]} just received a packet from {example[0][1]} which has an IP address of {example[0][2]}."

    else:
        result = False

    return result


@app.before_first_request
def init():
    global DB_MANAGER
    global CONFIG

    # open database connections
    DB_MANAGER = databaseBursts.dbManager()
    listenManager = databaseBursts.dbManager()
    listenManager.listen('db_notifications', lambda payload:event_queue.append(payload))

    # load config from file
    sys.stdout.write("Loading config...")
    try:
        CONFIG = configparser.ConfigParser()
        CONFIG.read(CONFIG_PATH)
        print("ok")
    except Exception as e:
        print("error")


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
        return
    except:
        print("Unexpected error:", sys.exc_info())
        traceback.print_exc()                
        return

# This is run using Flask
# export FLASK_APP=apy
# export FLASK_DEBUG=1
# export FLASK_PORT=X
# flask run


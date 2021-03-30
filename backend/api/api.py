#! /usr/bin/env python3

import re, os, json, subprocess, math, sys, traceback, urllib, configparser, socket, logging
from datetime import datetime
from functools import reduce
from flask import Flask, jsonify, make_response, Response, g
from scripts.databaseBursts import DbManager, TransEpoch, TransmissionMerger
from logger import getArethaLogger
from config import config as CONFIG
from project_variables import CONFIG_PATH
from models import init_models, db
from api import questions

# there's no command line... yet so just read config from config_path
CONFIG.read(CONFIG_PATH)

models = init_models(config=CONFIG['postgresql'])
Transmissions = models['transmissions']
Exposures = models['exposures']
Geodata = models['geodata']
Devices = models['devices']
Content = models['content']
Rules = models['rules']

# Important API changes:
#
# Responses have the following type
# response = { data } | { error }
# data = JSON | primitive
# error = { message }
# message = string


####################
# global variables #
####################
API_VERSION = "2.0"
DB_MANAGER = None  # for running database queries

log = getArethaLogger("api_test", debug=True)
app = Flask(__name__)  # WSGI entry point
app.config.DEBUG = True
app.config.TESTING = True

geos = dict()  # for building and caching geo data 

class ArethaAPIException(Exception):
    default_message = "There was an error processsing this request"
    def __init__(self, message=default_message, status=400, internal=None):
        if internal is not None:
            log.error("ArethaAPIException", exc_info=internal)
        self.message = message # human friendly message
        self.status = status

def send_response(response_data, status):
    log.debug(f"status={status}")
    log.debug(f"response_data={response_data}")

    if status is None:
        raise Exception("Missing status code")

    # append any "global" fields TODO see what other fields we might
    # want to add (e.g. id to correlate client and server logs)
    response_data['apiVersion'] = API_VERSION

    # convert response contents to json
    # response = make_response(response_data, status)

    return response_data, status

# error response
@app.errorhandler(ArethaAPIException)
def handle_api_error(e):
    response = {
        "error": {
            "message": e.message
        }
    }

    return response
    #return send_response(response, e.status)

@app.before_request
def before_request():
    g.db = db
    g.db.connect()

@app.after_request
def after_response(response):
    # close db connection
    g.db.close()

    # format reponse
    data = response.get_json()
    new_res_data = {
        "apiVersion": API_VERSION,
        "data": data
    }
    response.data = json.dumps(new_res_data)

    # add headers
    response.headers['Access-Control-Allow-Origin'] = '*' # CORS
    response.headers['Content-Type'] = 'application/json'

    return response

#################
# api endpoints #
#################
@app.route('/api/impacts/<start>/<end>/<delta>')
def impacts2(start, end, delta):
    try:
        start = datetime.fromtimestamp(int(start))
        end = datetime.fromtimestamp(int(end))
        ex, tr = Exposures, Transmissions

        tr1 = tr.select().limit(1).order_by(tr.id.desc())

        if len(tr1):
            interval = math.floor(tr.end_date - tr.start_date).total_seconds()                
            if interval > 0 and delta % interval > 0:
                raise ArethaAPIException(f"Delta must be multiple of resolution {interval} seconds", 422)
                            
            matches = tr.select().join(ex).where(ex.start_time >= start, ex.end_time <= end)
            tMerger = TransmissionMerger(mins=delta)
            impacts = {}
            if len(matches) > 0:
                [tMerger.merge(t) for t in matches]
                impacts = tMerger.to_dict()

        # add geo and device data
        geos = get_geodata()
        devices = get_device_info()

        return {
            "impacts": impacts,
            "geodata": geos,
            "devices": devices
        }
    except Exception as ae:
        raise ArethaAPIException(internal=ae)

# return aggregated impacts from <start> to <end>
# <start>/<end> as unix timestamps
@app.route('/api/impacts/<start>/<end>')
def impacts2_aggregated(start, end):
    try:
        start, end = datetime.fromtimestamp(int(start)), datetime.fromtimestamp(int(end))
        matches = (Transmissions
                   .select()
                   .join(Exposures)
                   .where(Exposures.start_time >= start, Exposures.end_time <= end))
        result = []
        
        if len(matches) > 0:
            te = reduce(lambda tres, t: tres.merge(t), matches[1:], TransEpoch(matches[0]))
            for (mac, tm) in te.by_mac.items():
                for (ext, extp) in tm.by_ext.items():
                    d = extp.to_dict()
                    d.update({"company": ext, "impact": extp.bytes, "device": mac})
                    result.append(d)

        # add geo and device data
        geos = get_geodata()
        devices = get_device_info()

        return {
            "impacts": result,
            "geodata": geos,
            "devices": devices
        }
    except Exception as ae:
        raise ArethaAPIException(internal=ae)


# get the mac address, manufacturer, and custom name of every device
@app.route('/api/devices')
def devices():
    return {
        "device": get_device_info()
    }

# get geodata about all known ips
@app.route('/api/geodata')
def geodata():
    return {
        "geodata": get_geodata()
    }

# set the custom name of a device with a given mac
@app.route('/api/devices/set/<mac>/<name>')
def set_device(mac, name):
    mac_format = re.compile('^(([a-fA-F0-9]){2}:){5}[a-fA-F0-9]{2}$')
    if mac_format.match(mac) is None:
        raise ArethaAPIException("Invalid mac address given")

    Devices.update(name=name).where(Devices.mac == mac)

    return {
        "message": "Device with mac " + mac + " now has name " + name
    }


# return examples to be used for educational components
@app.route('/api/example/<question>')
def counterexample(question):
    try:
        example = questions.get_example(question)
    
        if example is False:
            raise ArethaAPIException("Unable to find a match for requested example")

        return api_data({
            "text": example["text"],
            "impacts": example["impacts"],
            "geodata": example["geodata"],
            "devices": example["devices"]
        })
    except Exception as e:
        raise ArethaAPIException("Internal error while fetching example", status=500, internal=e)
    

# return a list of firewall rules
@app.route('/api/aretha/list')
def list_rules():
    [(fw_on)] = Content.select(Content.complete).where(Content.name=="S3").tuples()
    rules = (Rules
             .select(Rules.id, Rules.device, Devices.name, Rules.c_name)
             .join(Devices, on=(Rules.device == Devices.mac))
             .tuples())

    return {
        "rules": rules,
        "enabled": fw_on
    }

# add a firewall rule as dictated by aretha
@app.route('/api/aretha/enforce/<destination>')
def enforce_dest(destination):
    inserted = Rules.create({
        Rules.c_name: destination
    })
    
    if not inserted:
        raise ArethaAPIException(f"error while creating destination only rule for {destination}")

    return {"message": f"destination only rule added for {destination}", "success": True}


# add a firewall rule as dictated by aretha
@app.route('/api/aretha/enforce/<destination>/<device>')
def enforce_dest_dev(destination, device):

    inserted = Rules.create({
        Rules.device: device,
        Rules.c_name: destination
    })
    
    if not inserted:
        raise ArethaAPIException(f"error while creating device to destination rule for {device} to {destination}")

    return {"message": f"device to destination rule added for {device} to {destination}", "success": True}


# remove a firewall rule as dictated by aretha
@app.route('/api/aretha/unenforce/<destination>')
def unenforce_dest(destination):
    
    blocked_ips = DB_MANAGER.execute("""
    SELECT r.c_name, r.device, b.ip 
    FROM rules AS r 
    RIGHT JOIN blocked_ips AS b 
    ON r.id = b.rule 
    WHERE r.c_name = %s AND r.device IS NULL
    """, (destination,))


    # TODO handle other machines
    if sys.platform.startswith("linux"):
        for ip in blocked_ips:
            if ip[1] is None:
                subprocess.run(["sudo", "iptables", "-D", "INPUT", "-s", ip[2], "-j", "DROP"])
                subprocess.run(["sudo", "iptables", "-D", "OUTPUT", "-d", ip[2], "-j", "DROP"])
                subprocess.run(["sudo", "dpkg-reconfigure", "-p", "critical", "iptables-persistent"])
    
    DB_MANAGER.execute("DELETE FROM rules WHERE c_name = %s AND device IS NULL", (destination,))

    return {"message": f"rule removed for {destination}", "success": True}

# remove a firewall rule as dictated by aretha
@app.route('/api/aretha/unenforce/<destination>/<device>')
def unenforce_dest_dev(destination, device):
    
    blocked_ips = DB_MANAGER.execute("""
    SELECT r.c_name, r.device, b.ip 
    FROM rules AS r 
    RIGHT JOIN blocked_ips AS b 
    ON r.id = b.rule 
    WHERE r.c_name = %s and r.device = %s
    """, (destination, device))

    if sys.platform.startswith("linux"):
        for ip in blocked_ips:
            if ip[1] is not None:
                subprocess.run(["sudo", "iptables", "-D", "FORWARD", "-d", ip[2], "-m", "mac", "--mac-source", ip[1], "-j", "DROP"])
                subprocess.run(["sudo", "iptables", "-D", "FORWARD", "-s", ip[2], "-m", "mac", "--mac-source", ip[1], "-j", "DROP"])
                subprocess.run(["sudo", "dpkg-reconfigure", "-p", "critical", "iptables-persistent"])
    
    DB_MANAGER.execute("DELETE FROM rules WHERE c_name = %s AND device = %s", (destination,device))
    return {"message": f"rule removed for {destination}/{device}", "success": True}


# open an event stream for database updates
# TODO handle stream responses in api_data
@app.route('/api/stream')
def stream():
    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


# return a list of live but not completed content
@app.route('/api/content')
def content():
    content = DB_MANAGER.execute("select * from content where live < current_timestamp and complete = false", ())
    return content


# mark content as set, and record the pre and post responses
@app.route('/api/content/set/<name>/<pre>/<post>')
def contentSet(name, pre, post):
    DB_MANAGER.execute("update content set complete = true, pre = %s, post = %s where name = %s", (pre[:200], post[:200], name))
    return api_data({"message": "Request processed", "success": "unknown"})

# return records for the redaction interface
@app.route('/api/redact')
def getRedact():
    geodata = DB_MANAGER.execute("select distinct c_name from geodata", ())
    return geodata


# remove records for the redaction interface
@app.route('/api/redact/set/<company>')
def setRedact(company):
    ips = DB_MANAGER.execute("select ip from geodata where c_name = %s", (company,));
    for ip in ips:
        DB_MANAGER.execute("delete from packets where ext = %s", (ip[0],))
        DB_MANAGER.execute("delete from geodata where ip = %s", (ip[0],))

    return {"message": "operation successful"}


@app.route('/api/pid')
def getPid():
    pid = "unknown"
    if CONFIG is not None and 'general' in CONFIG and 'id' in CONFIG['general']:
        pid = CONFIG['general']['id']
        
    return {"pid": pid}


@app.route('/api/activity/<pid>/<category>/<action>')
def activity(pid, category, action):
    DB_MANAGER.execute("""
    INSERT INTO activity(pid, category, description) 
    VALUES(%s, %s, %s)
    """, (pid, category, action))
    
    return {"message": "activity logged"}


####################
# internal methods #
####################
# return a dictionary of mac addresses to manufacturers and names
def get_device_info():
    devices = dict()
    raw_devices = Devices.select().tuples()

    for mac, manufacturer, name in raw_devices:
        devices[mac] = {
            "manufacturer": manufacturer,
            "name": name
        }
        
    return devices


# get geo data for all ips
def get_geodata():
    geos = (
        Geodata.select(
            Geodata.ip,
            Geodata.lat,
            Geodata.lon,
            Geodata.c_code,
            Geodata.c_name,
            Geodata.domain)
        .dicts())

    return geos


@app.before_first_request
def init():
    global DB_MANAGER

    db = DbManager()
    # open database connections
    DB_MANAGER = db
    listenManager = db
    
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

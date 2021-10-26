#! /usr/bin/env python3

import json, sys, traceback

from flask import Flask, jsonify, make_response, Response, g

from api.routes import impacts, firewall, devices, content, redact, geodata, activity
from api.api_exceptions import ArethaAPIException

# Important API changes:
#
# Responses have the following type
# response = { data } | { error }
# data = JSON | primitive
# error = { message }
# message = 

api_version = 2.0

# used by event stream
event_queue = []

# for building and caching geo data 
geos = dict()

def handle_api_error(e):
    response = {
        "error": {
            "message": e.message
        }
    }

    return response

def before_request(db):
    def do_before_request():
        g.db = db
        g.db.connect()
        
    return do_before_request

def after_request(db, api_version):
    def do_after_request(response):
        # close db connection
        g.db.close()

        # format reponse
        data = response.get_json()

        new_res_data = {
            "apiVersion": api_version,
            "data": data
        }

        response.data = json.dumps(new_res_data)

        # add headers
        response.headers['Access-Control-Allow-Origin'] = '*' # CORS
        response.headers['Content-Type'] = 'application/json'

        return response

    return do_after_request


def create_app(debug, db, models, pid, log):
    app = Flask('aretha_api')
    app.config.DEBUG = debug # TODO can we pass this as argument to Flask constructor?

    # models
    Transmissions = models['transmissions']
    Exposures = models['exposures']
    Geodata = models['geodata']
    Devices = models['devices']
    Content = models['content']
    Rules = models['rules']
    Activity = models['activity']
    
    app.register_error_handler(ArethaAPIException, handle_api_error)
    app.before_request(before_request(db))
    app.after_request(after_request(db, api_version))

    # TODO reduce code duplication 
    # impacts
    impacts_blueprint = impacts.create_blueprint(Transmissions, Exposures, Geodata, Devices)
    app.register_blueprint(impacts_blueprint, url_prefix='/api/impacts')

    # firewall
    firewall_blueprint = firewall.create_blueprint(Rules, Content, Devices)
    app.register_blueprint(firewall_blueprint, url_prefix="/api/aretha")

    # devices
    devices_blueprint = devices.create_blueprint(Devices)
    app.register_blueprint(devices_blueprint, url_prefix="/api/devices/")

    # content
    content_blueprint = content.create_blueprint(Content)
    app.register_blueprint(content_blueprint, url_prefix="/api/content")

    # redact
    redact_blueprint = redact.create_blueprint(Transmissions, Geodata)
    app.register_blueprint(redact_blueprint, url_prefix="/api/redact")

    # geodata
    geodata_blueprint = geodata.create_blueprint(Geodata)
    app.register_blueprint(geodata_blueprint, url_prefix="/api/geodata")

    # activity
    activity_blueprint = activity.create_blueprint(Activity)
    app.register_blueprint(activity_blueprint, url_prefix="/api/activity")

    # open an event stream for database updates
    # TODO handle stream responses in api_data
    @app.route('/api/stream')
    def stream():
        response = Response(event_stream(), mimetype="text/event-stream")
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    # returns "id" of aretha
    @app.route('/api/pid')
    def get_pid():
        pid = "5"
        
        return {"pid": pid}

    # DB_MANAGER.listen('db_notifications', lambda payload: event_queue.append(payload))
    return app


################
# event stream #
################

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

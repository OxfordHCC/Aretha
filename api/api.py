#! /usr/bin/python3

from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import json
import re
import logging
from datetime import datetime

app = Flask(__name__)
api = Api(app)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class Digest(Resource):
    def get(self):
        refresh()

        print('Route /api/digest')
        digest = jsonify("TODO")
        return digest

class Devices(Resource):
    def get(self):
        refresh()
        print('Route /api/devices')
        devices = jsonify(getDevices())
        return devices

class Destinations(Resource):
    def get(self):
        refresh()
        print('Route /api/destinations')
        destinations = jsonify(calculateImpacts())
        return destinations

def refresh():
    global lastLoad
    global iotData
    if (datetime.now() - lastLoad).total_seconds() > 60:
        print("Refreshing data")
        lastLoad = datetime.now()
        with open('../ui/src/assets/data/iotData.json') as raw:
            iotData = json.load(raw)

def getDevices():
    refresh()
    global iotData

    devices = {}
    for device in iotData['manDev']:
        name = re.search('(?<= : )[a-z0-9:]*', device).group(0)
        if name not in devices:
            devices[name] = iotData['manDev'][device]

    return devices

def calculateImpacts(device=''):
    refresh()
    global iotData

    data = iotData['impacts']
    impacts = {}

    if device == '':
        for impact in data:
            if impact['companyName'] in impacts:
                impacts[impact['companyName']] += impact['impact']
            else:
                impacts[impact['companyName']] = impact['impact']
    else:
        pass

    return impacts

if __name__ == '__main__':
    api.add_resource(Digest, '/api/digest')
    api.add_resource(Devices, '/api/devices')
    api.add_resource(Destinations, '/api/destinations')

    iotData = ""
    lastLoad = datetime.min

    app.run(port=4201, threaded=True)

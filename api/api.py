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

REFRESH_INTERVAL = 60

#Produce a summary of the main traffic destinations, and (in future) notify of any alerts that have been triggered
class Digest(Resource):
    def get(self):
        refresh()

        impacts = calculateImpacts()
        results = impacts['results']
        total = impacts['total']
        destinations = impacts['destinations']

        topDest = {'name':'','impact':-1,'country':''}
        for dest in destinations:
            if dest['impact'] > topDest['impact']:
                topDest = dest

        digest = "Tracking " + str(int(total/1000)) + " megabytes of traffic to " + str(results) + " different destinations."
        digest += " The top destination was " + topDest['name'] + ' with ' + str(int((topDest['impact']/total)*100)) + '% of all traffic.'
        digest += " No alerts have been triggered in the last 24 hours."

        print('Route /api/digest')
        return jsonify(digest)

#Return a list of device names
class Devices(Resource):
    def get(self):
        refresh()
        print('Route /api/devices')
        devices = jsonify(getDevices())
        return devices

#Return a list of traffic destinations, along with which country they are in and how much data was sent there
class Destinations(Resource):
    def get(self):
        refresh()
        print('Route /api/destinations')
        destinations = jsonify(calculateImpacts())
        return destinations

#As for Destinations, but for a specific device name
class DestinationsByDevice(Resource):
    def get(self, device):
        refresh()
        print('Route /api/destinations/' + device)
        destinations = jsonify(calculateImpacts(device))
        return destinations

#If iotData.json was last checked more than REFRESH_INTERVAL seconds ago, reload it now
def refresh():
    global lastLoad
    global iotData
    if (datetime.now() - lastLoad).total_seconds() > REFRESH_INTERVAL:
        print("Refreshing data")
        lastLoad = datetime.now()
        with open('../ui/src/assets/data/iotData.json') as raw:
            iotData = json.load(raw)

#Return a list of devices in the iotData.json file
def getDevices():
    refresh()
    global iotData

    devices = {}
    for device in iotData['manDev']:
        name = re.search('(?<= : )[a-z0-9:]*', device).group(0)
        if name not in devices:
            devices[name] = iotData['manDev'][device]

    return devices

#Return a list of impacts for the entire data set, or from a specific device
def calculateImpacts(device=''):
    refresh()
    global iotData

    data = iotData['impacts']
    geos = iotData['geos']
    returnObject = {}
    destinations = []
    results = 0
    total = 0

    for impact in data:
        found = False
        for destination in destinations:
            if device == '' or device == impact['appid']:
                if destination['name'] == impact['companyName']:
                    destination['impact'] += impact['impact']
                    found = True
                    break
        if not found:
            country = 'Unknown'
            for geo in geos:
                if geo['geo']['organisation'] == impact['companyName']:
                    country = geo['geo']['country_name']
            destinations.append({'name':impact['companyName'], 'impact':impact['impact'], 'country':country})
            results += 1
            total += impact['impact']

    returnObject['results'] = results
    returnObject['total'] = total
    returnObject['destinations'] = destinations
    return returnObject

if __name__ == '__main__':
    #Register the API endpoints with flask
    api.add_resource(Digest, '/api/digest')
    api.add_resource(Devices, '/api/devices')
    api.add_resource(Destinations, '/api/destinations')
    api.add_resource(DestinationsByDevice, '/api/destinations/<device>')

    #Initialise variables
    iotData = ""
    lastLoad = datetime.min

    #Start the flask server
    app.run(port=4201, threaded=True, host='0.0.0.0')

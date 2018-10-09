#! /usr/bin/python3

from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import json
import logging

global iotData

app = Flask(__name__)
api = Api(app)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class Digest(Resource):
    def get(self):
        print('Route /api/digest')
        digest = jsonify("digest")
        return digest

class Devices(Resource):
    def get(self):
        print('Route /api/devices')
        devices = jsonify({
            "00:00:00:00:00:00":"device1",
            "00:00:00:00:00:01":"device2"
                })
        return devices

class Destinations(Resource):
    def get(self):
        print('Route /api/destinations')
        destinations = jsonify({
            "Google LLC":["www.a.com", "www.b.com"],
            "NUTTY CORP":["www.mcnu.tty"]
                })
        return destinations

class dataHandler:
    def refresh():
    def loadData():
        with open('../ui/src/assets/data/iotData.json') as raw:
            iotData = json.load(raw)

api.add_resource(Digest, '/api/digest')
api.add_resource(Devices, '/api/devices')
api.add_resource(Destinations, '/api/destinations')

if __name__ == '__main__':




    app.run(port=4201, threaded=True)

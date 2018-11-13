#! /usr/bin/python3

from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import json
import re
import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts
DB_MANAGER = databaseBursts.dbManager()

app = Flask(__name__)
api = Api(app)

#=============
#api endpoints

#return aggregated data for the given time period (called by refine)
class Refine(Resource):
    def get(self, days):
        return jsonify({"bursts": GetBursts(days), "macMan": MacMan(), "manDev": ManDev()})

#get the mac addresse, manufacturer, and custom name of every device
class Devices(Resource):
    def get(self):
        return jsonify({"macMan": MacMan(), "manDev": ManDev()})

#set the custom name of a device with a given mac
class SetDevice(Resource):
    def get(self, mac, name):
        DB_MANAGER.execute("UPDATE devices SET name=%s WHERE mac=%s", (name, mac))
        return jsonify({"message": "Device with mac " + mac + " now has name " + name})

#================
#internal methods

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
    _,lat,lon,c_code = DB_MANAGER.execute("SELECT * FROM geodata WHERE ip=%s LIMIT 1", (ip,), False)
    geo = {"latitude": lat, "longitude": lon, "country_code": c_code}
    return geo

#get bursts for the given time period in days
def GetBursts(days):
    pass

if __name__ == '__main__':
    #Register the API endpoints with flask
    api.add_resource(Refine, '/api/refine/<days>')
    api.add_resource(Devices, '/api/devices')
    api.add_resource(SetDevice, '/api/setdevice/<mac>/<name>')

    #Initialise variables
    iotData = ""
    lastLoad = datetime.min

    #Start the flask server
    app.run(port=4201, threaded=True, host='0.0.0.0')

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
CACHE_TIMEOUT = 10
ID_POINTER = 0
impacts = []
geos = dict()

#=============
#api endpoints

#return aggregated data for the given time period (called by refine)
class Refine(Resource):
    def get(self, days):
        return jsonify({"bursts": GetBursts(days), "macMan": MacMan(), "manDev": ManDev(), "impacts": GetImpacts(days), "usage": GenerateUsage()})

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
    lat,lon,c_code,c_name = DB_MANAGER.execute("SELECT lat, lon, c_code, c_name FROM geodata WHERE ip=%s LIMIT 1", (ip,), False)
    geo = {"latitude": lat, "longitude": lon, "country_code": c_code, "company_name": c_name}
    return geo

#get bursts for the given time period in days
def GetBursts(days):
    bursts = DB_MANAGER.execute("SELECT MIN(time), MIN(mac), burst, MIN(categories.name) FROM packets JOIN bursts ON bursts.id = packets.burst JOIN categories ON categories.id = bursts.category WHERE time > (NOW() - INTERVAL %s) GROUP BY burst ORDER BY burst", ("'" + str(days) + " DAY'",))
    
    result = []
    #epoch = datetime.datetime.utcfromtimestamp(0)
    epoch = datetime(1970, 1, 1, 0, 0)
    for burst in bursts:
        unixTime = int((burst[0] - epoch).total_seconds() * 1000.0)
        device = burst[1]
        category = burst[3]
        result.append({"value": unixTime, "category": category, "device": device })
    return result

def GetImpacts(days):
    global geos, ID_POINTER
    packets = DB_MANAGER.execute("SELECT * FROM packets WHERE id > %s AND time > (NOW() - INTERVAL %s) ORDER BY id", (str(ID_POINTER), "'" + str(days) + " DAY'"))
    result = []
    local_ip_mask = re.compile('^(192\.168|10\.|255\.255\.255\.255).*')

    #[0] id
    #[1] timestamp
    #[2] src
    #[3] dst
    #[4] mac
    #[5] len
    #[6] proto
    #[7] burst

    for packet in packets:
        #determine if the src or dst is the external ip address
        ip_src = local_ip_mask.match(packet[2]) is not None
        ip_dst = local_ip_mask.match(packet[3]) is not None
        ext_ip = None
        if (ip_src and ip_dst) or (not ip_src and not ip_dst):
            continue #shouldn't happen, either 0 or 2 internal hosts
        elif ip_src:
            ext_ip = packet[3]
        else:
            ext_ip = packet[2]
        #make sure we have geo data, then update the impact
        if ext_ip not in geos:
            geos[ext_ip] = GetGeo(ext_ip)
        UpdateImpact(packet[4], ext_ip)
        if ID_POINTER < packet[0]:
            ID_POINTER = packet[0]

    #build a list of all device/ip impacts and geo data
    for ip,geo in geos.items():
        for mac,_ in ManDev().items():
            item = geo
            item['impact'] = GetImpact(mac, ip)
            item['ip'] = ip
            item['device'] = mac
            result.append(item)
    return result

def UpdateImpact(mac, ip):
    global impacts

def GetImpact(mac, ip):
    global impacts
    return 4

def GenerateUsage():
    return []

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

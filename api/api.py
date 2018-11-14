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

DB_MANAGER = databaseBursts.dbManager() #for running database queries
app = Flask(__name__) #initialise the flask server
api = Api(app) #initialise the flask server
ID_POINTER = 0 #so we know which packets we've seen (for caching)
impacts = dict() #for building and caching impacts
geos = dict() #for building and caching geo data
lastDays = 0 #timespan of the last request (for caching)

#=============
#api endpoints

#return aggregated data for the given time period (in days, called by refine)
class Refine(Resource):
    def get(self, days):
        return jsonify({"bursts": GetBursts(days), "macMan": MacMan(), "manDev": ManDev(), "impacts": GetImpacts(days), "usage": GenerateUsage()})

#get the mac address, manufacturer, and custom name of every device
class Devices(Resource):
    def get(self):
        return jsonify({"macMan": MacMan(), "manDev": ManDev()})

#set the custom name of a device with a given mac
class SetDevice(Resource):
    def get(self, mac, name):
        mac_format = re.compile('^(([a-fA-F0-9]){2}:){5}[a-fA-F0-9]{2}$')
        if mac_format.match(mac) is not None:
            DB_MANAGER.execute("UPDATE devices SET name=%s WHERE mac=%s", (name, mac))
            return jsonify({"message": "Device with mac " + mac + " now has name " + name})
        else:
            return jsonify({"message": "Invalid mac address given"})

#return all traffic bursts for the given time period (in days)
class Bursts(Resource):
    def get(self, days):
        return jsonify(GetBursts(days))

#return all impacts for the given time period (in days)
class Impacts(Resource):
    def get(self, days):
        return jsonify(GetImpactss(days))

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

#get bursts for the given time period (in days)
def GetBursts(days):
    bursts = DB_MANAGER.execute("SELECT MIN(time), MIN(mac), burst, MIN(categories.name) FROM packets JOIN bursts ON bursts.id = packets.burst JOIN categories ON categories.id = bursts.category WHERE time > (NOW() - INTERVAL %s) GROUP BY burst ORDER BY burst", ("'" + str(days) + " DAY'",))
    result = []
    epoch = datetime(1970, 1, 1, 0, 0)
    for burst in bursts:
        unixTime = int((burst[0] - epoch).total_seconds() * 1000.0)
        device = burst[1]
        category = burst[3]
        result.append({"value": unixTime, "category": category, "device": device })
    return result

#get impact (traffic) of every device/external ip combination for the given time period (in days)
def GetImpacts(days):
    global geos, ID_POINTER, lastDays

    #we can only keep the cache if we're looking at the same packets as the previous request
    if days is not lastDays:
        ResetImpactCache() 

    #get all packets from the database (if we have cached impacts from before, then only get new packets)
    packets = DB_MANAGER.execute("SELECT * FROM packets WHERE id > %s AND time > (NOW() - INTERVAL %s) ORDER BY id", (str(ID_POINTER), "'" + str(days) + " DAY'"))
    result = []
    local_ip_mask = re.compile('^(192\.168|10\.|255\.255\.255\.255).*') #so we can filter for local ip addresses

    for packet in packets:
        #determine if the src or dst is the external ip address
        ip_src = local_ip_mask.match(packet[2]) is not None
        ip_dst = local_ip_mask.match(packet[3]) is not None
        ext_ip = None
        
        if (ip_src and ip_dst) or (not ip_src and not ip_dst):
            continue #shouldn't happen, either 0 or 2 internal hosts
        
        #remember which ip address was external
        elif ip_src:
            ext_ip = packet[3]
        else:
            ext_ip = packet[2]
        
        #make sure we have geo data, then update the impact
        if ext_ip not in geos:
            geos[ext_ip] = GetGeo(ext_ip)
        UpdateImpact(packet[4], ext_ip, packet[5])

        #fast forward the id pointer so we know this packet is cached
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
    lastDays = days
    return result #shipit

#setter method for impacts
def UpdateImpact(mac, ip, impact):
    global impacts
    if mac in impacts:
        if ip in impacts[mac]:
            impacts[mac][ip] += impact
        else:
            impacts[mac][ip] = impact #impact did not exist
    else:
        impacts[mac] = dict()
        impacts[mac][ip] = impact #impact did not exist

#getter method for impacts
def GetImpact(mac, ip):
    global impacts
    if mac in impacts:
        if ip in impacts[mac]:
            return impacts[mac][ip]
        else:
            return 0 #impact does not exist
    else:
        return 0 #impact does not exist

#clear impact dictionary and packet id pointer
def ResetImpactCache():
    global impacts, ID_POINTER
    impacts = dict()
    ID_POINTER = 0

#generate fake usage for devices (a hack so they show up in refine)
def GenerateUsage():
    return []

#=======================
#main part of the script
if __name__ == '__main__':
    #Register the API endpoints with flask
    api.add_resource(Refine, '/api/refine/<days>')
    api.add_resource(Devices, '/api/devices')
    api.add_resource(Bursts, '/api/bursts/<days>')
    api.add_resource(Impacts, '/api/impacts/<days>')
    api.add_resource(SetDevice, '/api/setdevice/<mac>/<name>')

    #Start the flask server
    app.run(port=4201, threaded=True, host='0.0.0.0')

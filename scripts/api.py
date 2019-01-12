#! /usr/bin/env python3

from flask import Flask, request, jsonify, make_response, Response
from flask_restful import Resource, Api
import json, re, sys, os, traceback, copy, argparse
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts

LOCAL_IP_MASK = re.compile('^(192\.168|10\.|255\.255\.255\.255).*') #so we can filter for local ip addresses
DB_MANAGER = databaseBursts.dbManager() #for running database queries
app = Flask(__name__) #initialise the flask server
api = Api(app) #initialise the flask server
geos = dict() #for building and caching geo data

#=============
#api endpoints

#return aggregated data for the given time period (in days, called by refine)
class Refine(Resource):
    def get(self, n):
        try:
            response = make_response(jsonify({"bursts": GetBursts(n), "macMan": MacMan(), "manDev": ManDev(), "impacts": GetImpacts(n), "usage": GenerateUsage()}))
            # response = make_response(jsonify({"bursts": GetBursts(days), "macMan": MacMan(), "manDev": ManDev(), "impacts": GetImpacts(days), "usage": GenerateUsage()}))
            
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        except:
            print("Unexpected error:", sys.exc_info())
            traceback.print_exc()
            sys.exit(-1)                    

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
    def get(self, n):
        return jsonify(GetBursts(n))

#return all impacts for the given time period (in days)
class Impacts(Resource):
    def get(self, n):
        return jsonify(GetImpacts(n))

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
    print("Get Geo ", ip)
    try:
        lat,lon,c_code,c_name = DB_MANAGER.execute("SELECT lat, lon, c_code, c_name FROM geodata WHERE ip=%s LIMIT 1", (ip,), False)
        geo = {"latitude": lat, "longitude": lon, "country_code": c_code, "companyName": c_name}
        return geo
    except:
        geo = {"latitude": 0, "longitude": 0, "country_code": 'XX', "companyName": 'unknown'}
        return geo

#get bursts for the given time period (in days)
def GetBursts(n, units="MINUTES"):
    bursts = DB_MANAGER.execute("SELECT MIN(time), MIN(mac), burst, MIN(categories.name) FROM packets JOIN bursts ON bursts.id = packets.burst JOIN categories ON categories.id = bursts.category WHERE time > (NOW() - INTERVAL %s) GROUP BY burst ORDER BY burst", ("'" + str(n) + " " + units + "'",)) #  " DAY'",))
    result = []
    epoch = datetime(1970, 1, 1, 0, 0)
    for burst in bursts:
        unixTime = int((burst[0] - epoch).total_seconds() * 1000.0)
        device = burst[1]
        category = burst[3]
        result.append({"value": unixTime, "category": category, "device": device })
    return result


#get impact (traffic) of every device/external ip combination for the given time period (in days)

#setter method for impacts
def _update_impact(impacts, mac, ip, impact):
    if mac in impacts:
        # print("updateimpact existing mac ", mac)
        if ip in impacts[mac]:
            # print("updateimpact existing ip, updating impact for mac ", mac, " ip ", ip, " impact: ", impacts[mac][ip])        
            impacts[mac][ip] += impact
        else:
            # print("updateimpact no existing ip for mac ", mac, " ip ", ip, " impact: ", impact)                    
            impacts[mac][ip] = impact #impact did not exist
    else:
        # print("updateimpact unknown mac, creating new entry for  ", mac, ip)        
        impacts[mac] = dict()
        impacts[mac][ip] = impact #impact did not exist


def packet_to_impact(impacts, packet):
    #determine if the src or dst is the external ip address
    pkt_id, pkt_time, pkt_src, pkt_dst, pkt_mac, pkt_len, pkt_proto, pkt_burst = packet["id"], packet.get('time'), packet["src"], packet["dst"], packet["mac"], packet["len"], packet.get("proto"), packet.get("burst")
    
    ip_src = LOCAL_IP_MASK.match(pkt_src) is not None
    ip_dst = LOCAL_IP_MASK.match(pkt_dst) is not None
    ext_ip = None
    
    if (ip_src and ip_dst) or (not ip_src and not ip_dst):
        return #shouldn't happen, either 0 or 2 internal hosts
    
    #remember which ip address was external
    elif ip_src:
        ext_ip = pkt_dst
    else:
        ext_ip = pkt_src
    
    #make sure we have geo data, then update the impact
    if ext_ip not in geos:
        geos[ext_ip] = GetGeo(ext_ip)

    _update_impact(impacts, pkt_mac, ext_ip, pkt_len)

def CompileImpacts(impacts, packets):
    # first run packet_to_impact
    [packet_to_impact(impacts, packet) for packet in packets]

    # compute the updated impacts resulting from these packets

    # old way
    # geos -> { ip -> { geo }, ip2 -> { { }
    # impacts { mac -> { ip1: xx, ip2: xx, ip3: xx }, mac2 -> { } }
    
    # iterate over ip in geos whereas now what we want to do is return
    # impacts generated by these packets across all of the macs that we see
    # macs are gonna be unique in impacts 

    # iterating over impacts [should be] safe at this point
    
    result = []
    for mmac, ipimpacts in impacts.items():
        for ip, impact in ipimpacts.items():
            item = geos[ip].copy() # hard crash here if geos[ip] is none, we should be careful about this
            # note: geos[ip] should never be none because the invariant is that packet_to_impact has been
            # called BEFORE this point, and that populates the geos. Yeah, ugly huh. I didn't write this
            # code, don't blame me!
            item['impact'] = impact
            item['companyid'] = ip
            item['appid'] = mmac
            if item['impact'] > 0:
                result.append(item)
            pass

    # for ip,geo in geos.items():
    #     for mac,_ in ManDev().items():
    #         item = geo.copy() # emax added .copy here() this is so gross
    #         item['impact'] = GetImpact(mac, ip, impacts)
    #         # print("Calling getimpact mac::", mac, " ip::", ip, 'impact result ', item['impact']);            
    #         item['companyid'] = ip
    #         item['appid'] = mac
    #         if item['impact'] > 0:
    #             result.append(item)
    #         pass
    #     pass    
    return result



def GetImpacts(n, units="MINUTES"):
    global geos
    print("GetImpacts: ::", n, ' ', units)
    #we can only keep the cache if we're looking at the same packets as the previous request

    impacts = dict() # copy.deepcopy(_impact_cache) 
    # get all packets from the database (if we have cached impacts from before, then only get new packets)
    packetrows = DB_MANAGER.execute("SELECT * FROM packets WHERE time > (NOW() - INTERVAL %s) ORDER BY id", ("'" + str(n) + " " + units + "'",)) 
    packets = [dict(zip(['id', 'time', 'src', 'dst', 'mac', 'len', 'proto', 'burst'], packet)) for packet in packetrows]

    # pkt_id, pkt_time, pkt_src, pkt_dst, pkt_mac, pkt_len, pkt_proto, pkt_burst = packet
     # {'id': '212950', 'dst': '224.0.0.251', 'len': '101', 'mac': '78:4f:43:64:62:01', 'src': '192.168.0.24', 'burst': None}

    result = CompileImpacts(impacts, packets)
    return result #shipit

# Getter method for impacts - nb: i think this is no longer used
def GetImpact(mac, ip, impacts):
    if mac in impacts:
        if ip in impacts[mac]:
            return impacts[mac][ip]
        else:            
            return 0 #impact does not exist
    else:
        return 0 #impact does not exist

# Generate fake usage for devices (a hack so they show up in refine)
def GenerateUsage():
    usage = []
    counter = 1
    for mac in MacMan():
        usage.append({"appid": mac, "mins": counter})
        counter += 1
    return usage

_events = []

def event_stream():
    import time

    def packets_insert_to_impact(packets):        
        impacts = CompileImpacts(dict(),packets)
        print("packets insert to pitt ", len(packets), " resulting impacts len ~ ", len(impacts))
        return impacts
    
    try:
        while True:
            time.sleep(0.5)
            insert_buf = []
            geo_updates = []
            device_updates = []

            while len(_events) > 0:
                event_str = _events.pop(0)
                event = json.loads(event_str)
                if event["operation"] in ['UPDATE','INSERT'] and event["table"] == 'packets':
                    event['data']['len'] = int(event['data'].get('len'))
                    insert_buf.append(event["data"])
                if event["operation"] in ['UPDATE','INSERT'] and event["table"] == 'geodata':
                    print("Geodata update", event["data"])
                    geo_updates.append(event["data"])
                if event["operation"] in ['UPDATE','INSERT'] and event["table"] == 'devices':
                    print("Device update", event["data"])                    
                    device_updates.append(event["data"])

            if len(insert_buf) > 0: 
                yield "data: %s\n\n" % json.dumps({"type":'impact', "data": packets_insert_to_impact(insert_buf)})
            if len(geo_updates) > 0:
                # ResetImpactCache()
                # updated ip should be 
                for update in geo_updates:
                    print("Got a geo update for %s, must reset GEO cache." % update["ip"])
                    geos.pop(update["ip"], None)
                yield "data: %s\n\n" % json.dumps({"type":'geodata'})
            if len(device_updates) > 0: 
                yield "data: %s\n\n" % json.dumps({"type":'device', "data": packets_insert_to_impact(insert_buf)})

    except GeneratorExit:
        return;
    except:
        print("Unexpected error:", sys.exc_info())
        traceback.print_exc()                
        return
        # sys.exit(-1)                

@app.route('/stream')
def stream():
    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

#=======================
#main part of the script
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--localip', dest="localip", type=str, help="Specify local IP addr (if not 192.168.x.x/10.x.x.x)")    
    args = parser.parse_args()

    if args.localip is not None:
        localipmask = '^(192\.168|10\.|255\.255\.255\.255|%s).*' % args.localip.replace('.','\.')
        LOCAL_IP_MASK = re.compile(localipmask) #so we can filter for local ip addresses
        print("Using local IP mask %s" % localipmask)    

    #Register the API endpoints with flask
    api.add_resource(Refine, '/api/refine/<n>')
    api.add_resource(Devices, '/api/devices')
    api.add_resource(Bursts, '/api/bursts/<days>')
    api.add_resource(Impacts, '/api/impacts/<n>')
    api.add_resource(SetDevice, '/api/setdevice/<mac>/<name>')

    # watch for listen events -- not sure if this has to be on its own connection
    listenManager = databaseBursts.dbManager()
    listenManager.listen('db_notifications', lambda payload:_events.append(payload))

    #Start the flask server
    app.run(port=4201, threaded=True, host='0.0.0.0')

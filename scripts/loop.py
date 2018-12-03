#! /usr/bin/env python3

import sys
import time
import os
import signal
import requests
import re
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "categorisation"))
import databaseBursts
import predictions

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
DB_MANAGER = databaseBursts.dbManager()
INTERVAL = 5
config = {"EchoFlowNumberCutoff":10,"burstNumberCutoffs":{"Echo":20,"Google Home":60,"Philips Hue Bridge":2,"Unknown":10},"burstTimeIntervals":{"Echo":1,"Google Home":1,"Philips Hue Bridge":1,"Unknown":1}}

#handler for signals (don't want to stop processing packets halfway through)
class sigTermHandler:
    exit = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    def shutdown(self, signum, frame):
        self.exit = True

def packetBurstification(devices):
    unBinned = DB_MANAGER.getNoBurst()

    allBursts = []  # List of list of ids
    allIds = set()  # Set of ids considered already
    nextBurst = []  # Ids to go in next burst
    burstPacketNoCutoff = 0

    # Get ids of all the packets we want in bursts
    for counter, row in enumerate(unBinned):
        id = row[0]
        mac = row[4]
        burstTimeInterval = int(config["burstTimeIntervals"]["Unknown"])
        burstPacketNoCutoff = int(config["burstNumberCutoffs"]["Unknown"])
        try:
            burstTimeInterval = int(config["burstTimeIntervals"][devices[mac]])
        except KeyError:
            pass
        try:
            burstPacketNoCutoff = int(config["burstNumberCutoffs"][devices[mac]])
        except KeyError:
            pass
        
        if id not in allIds:
            nextBurst = [id]
            allIds.add(id)
            currentTime = row[1]

            try:
                for otherRow in unBinned[counter+1:]:
                    if otherRow[0] not in allIds:
                        if otherRow[4] == mac and burstTimeInterval > (otherRow[1] - currentTime).total_seconds():
                            # If less than TIME_INTERVAL away, add to this burst
                            nextBurst.append(otherRow[0])
                            # Don't need to look at this one again, it's in this potential burst
                            allIds.add(otherRow[0])
                            currentTime = otherRow[1]

                        elif otherRow[4] == mac and burstTimeInterval < (otherRow[1] - currentTime).total_seconds():
                            if len(nextBurst) > burstPacketNoCutoff:
                                allBursts.append(nextBurst)
                            # If same device, but too far away, we can stop, there won't be another burst here
                            break
                            # Can't add to considered, might be the start of the next burst

                        elif otherRow[4] != mac:
                            continue
                            # If it's a different device, we can't say anything at this point
            except IndexError:
                continue     

        else:
            # If we've considered it we know it was within interval of another packet and so
            # it's either a valid burst or part of one that is too short
            continue
    if len(nextBurst) > burstPacketNoCutoff:
        allBursts.append(nextBurst)

    # Add each new burst, and add all the packet rows to it
    for burst in allBursts:
        newBurstId = DB_MANAGER.insertNewBurst()
        DB_MANAGER.updatePacketBurstBulk(burst, [newBurstId for _ in range(len(burst))])

def burstPrediction(devices):
    unCat = DB_MANAGER.getNoCat()
    cutoffs = config["burstNumberCutoffs"]
    predictor = predictions.Predictor()

    for burst in unCat:
        rows = DB_MANAGER.getRowsWithBurst(burst[0])

        if len(rows) == 0:
            continue

        device = devices[rows[0][4]]

        if "Echo" in device and len(rows) > cutoffs["Echo"]:
            category = predictor.predictEcho(rows)
        elif "Google" in device:
            category = predictor.predictGoogle(rows)
        elif device == "Philips Hue Bridge" and len(rows) > cutoffs[device]:
            category = predictor.predictHue(rows)
        else:
            category = predictor.predictOther(rows)

        # Get the id of this category, and add if necessary
        newCategoryId = DB_MANAGER.addOrGetCategoryNumber(category)

        # Update the burst with the name of the new category, packets already have a reference to the burst
        DB_MANAGER.updateBurstCategory(burst[0], newCategoryId)

def processGeos():
    raw_ips = DB_MANAGER.execute("SELECT DISTINCT src, dst FROM packets", ())
    raw_geos = DB_MANAGER.execute("SELECT ip FROM geodata", ())
    local_ip_mask = re.compile('^(192\.168|10\.|255\.255\.255\.255).*') #so we can filter for local ip addresses
    known_ips = []

    for row in raw_geos:
        known_ips.append(row[0])

    for dst,src in raw_ips:
        external_ip = None
        if local_ip_mask.match(dst) is not None:
            external_ip = src
        else:
            external_ip = dst

        if external_ip not in known_ips:
            data = requests.get('https://api.ipdata.co/' + external_ip + '?api-key=***REMOVED***')
            if data.status_code==200 and data.json()['latitude'] is not '':
                data = data.json()
                DB_MANAGER.execute("INSERT INTO geodata VALUES(%s, %s, %s, %s, %s)", (external_ip, data['latitude'], data['longitude'], data['country_code'], data['organisation'][:20]))
            else:
                DB_MANAGER.execute("INSERT INTO geodata VALUES(%s, %s, %s, %s, %s)", (external_ip, "0", "0", "XX", "unknown"))
        known_ips.append(external_ip)

def processMacs():
    raw_macs = DB_MANAGER.execute("SELECT DISTINCT mac FROM packets", ())
    known_macs = DB_MANAGER.execute("SELECT mac FROM devices", ())
    for mac in raw_macs:
        if mac not in known_macs:
            manufacturer = requests.get("https://api.macvendors.com/" + mac[0]).text
            if "errors" not in manufacturer:
                DB_MANAGER.execute("INSERT INTO devices VALUES(%s, %s, 'unknown')", (mac[0], manufacturer[:20]))
            else:
                DB_MANAGER.execute("INSERT INTO devices VALUES(%s, 'unknown', 'unknown')", (mac[0]))

#============
#loop control
if __name__ == '__main__':
    #register the signal handler
    handler = sigTermHandler() 

    #loop through categorisation tasks
    while(True):
        processGeos()
        processMacs()
        devices = requests.get(url='http://localhost:4201/api/devices').json()["manDev"]
        packetBurstification(devices)
        burstPrediction(devices)

        #exit gracefully if we were asked to shutdown
        if handler.exit:
            break
        
        time.sleep(INTERVAL)

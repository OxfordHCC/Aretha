#! /usr/bin/env python3

import sys, time, os, signal, requests, re, argparse, json
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "categorisation"))
import databaseBursts, rutils
import predictions
import configparser

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
DB_MANAGER = databaseBursts.dbManager()
INTERVAL = 1
LOCAL_IP_MASK = rutils.make_localip_mask() # re.compile('^(192\.168|10\.|255\.255\.255\.255).*') #so we can filter for local ip addresses
DEBUG = False
RAW_IPS = None
_events = [] # async db events
modelDefaults = {"EchoFlowNumberCutoff":10,"burstNumberCutoffs":{"Echo":20,"Google Home":60,"Philips Hue Bridge":2,"Unknown":10},"burstTimeIntervals":{"Echo":1,"Google Home":1,"Philips Hue Bridge":1,"Unknown":1}}
config = configparser.ConfigParser()
config.read(os.path.split(os.path.dirname(os.path.abspath(__file__)))[0] + "/config/config.cfg")

#handler for signals (don't want to stop processing packets halfway through)
class sigTermHandler:
    exit = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    def shutdown(self, signum, frame):
        print("caught signal")
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
        burstTimeInterval = int(modelDefaults["burstTimeIntervals"]["Unknown"])
        burstPacketNoCutoff = int(modelDefaults["burstNumberCutoffs"]["Unknown"])
        try:
            burstTimeInterval = int(modelDefaults["burstTimeIntervals"][devices[mac]])
        except KeyError:
            pass
        try:
            burstPacketNoCutoff = int(modelDefaults["burstNumberCutoffs"][devices[mac]])
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
    cutoffs = modelDefaults["burstNumberCutoffs"]
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
    # raw_ips = DB_MANAGER.execute("SELECT DISTINCT src, dst FROM packets", ())
    global RAW_IPS

    if not RAW_IPS:
        print("Preloading RAW_IPS")
        RAW_IPS = set( [r[0] for r in DB_MANAGER.execute("SELECT DISTINCT src FROM packets", ())]).union([r[0] for r in DB_MANAGER.execute("SELECT DISTINCT dst FROM packets", ())])
        print(" Done ", len(RAW_IPS), " known ips ")
        
    # print("raw_ips", raw_ips)
    
    raw_geos = DB_MANAGER.execute("SELECT ip FROM geodata", ())
    known_ips = []

    for row in raw_geos:
        known_ips.append(row[0])

    for ip in RAW_IPS:
        if LOCAL_IP_MASK.match(ip) is not None:
            # local ip, so skip
            continue
        if ip not in known_ips:
            data = requests.get('https://api.ipdata.co/' + ip + '?api-key=' + config['macvendors']['key'])
            if data.status_code==200 and data.json()['latitude'] is not '':
                data = data.json()
                DB_MANAGER.execute("INSERT INTO geodata VALUES(%s, %s, %s, %s, %s)", (ip, data['latitude'], data['longitude'], data['country_code'] or data['continent_code'], data['organisation'][:20]))
            else:
                DB_MANAGER.execute("INSERT INTO geodata VALUES(%s, %s, %s, %s, %s)", (ip, "0", "0", "XX", "unknown"))
            known_ips.append(ip)

            if DEBUG: print("Adding to known IPs ", ip)

def processMacs():
    raw_macs = DB_MANAGER.execute("SELECT DISTINCT mac FROM packets", ())
    known_macs = DB_MANAGER.execute("SELECT mac FROM devices", ())
    for mac in raw_macs:
        if mac not in known_macs:
            manufacturer = requests.get("https://api.macvendors.com/" + mac[0]).text
            if "errors" not in manufacturer:
                DB_MANAGER.execute("INSERT INTO devices VALUES(%s, %s, 'unknown')", (mac[0], manufacturer[:20]))
            else:
                DB_MANAGER.execute("INSERT INTO devices VALUES(%s, 'unknown', 'unknown')", (mac[0],))


#

def processEvents():
    global _events
    cur_events = _events.copy()
    _events.clear()
    for evt in cur_events:
        evt = json.loads(evt)
        if RAW_IPS and evt["operation"] in ['UPDATE','INSERT'] and evt["table"] == 'packets':
            # print("adding to raw ips %s %s" % (evt["data"]["src"],evt["data"]["dst"]))
            RAW_IPS.add(evt["data"]["src"])
            RAW_IPS.add(evt["data"]["dst"])
        pass


#============
#loop control
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    
    # parser.add_argument('--localip', dest="localip", type=str, help="Specify local IP addr (if not 192.168.x.x/10.x.x.x)")    
    parser.add_argument('--sleep', dest="sleep", type=float, help="Specify sleep in sec (can be fractions)")
    parser.add_argument('--burstify', dest='burst', action="store_true", help='Do packet burstification (Default off)')
    parser.add_argument('--predict', dest='predict', action="store_true", help='Do burst prediction (Default off)')
    parser.add_argument('--debug', dest='debug', action="store_true", help='Turn debug output on (Default off)')
    args = parser.parse_args()

    # if args.localip is not None:
    #     localipmask = '^(192\.168|10\.|255\.255\.255\.255|%s).*' % args.localip.replace('.','\.')
    #     print("Using local IP mask %s" % localipmask)    
    #     LOCAL_IP_MASK = re.compile(localipmask) #so we can filter for local ip addresses

    if args.sleep is not None:
        print("Setting sleep interval %s seconds." % args.sleep)    
        INTERVAL = args.sleep

    DEBUG = args.debug

    #register the signal handler
    handler = sigTermHandler() 

    # watch for listen events -- not sure if this has to be on its own connection
    listener_thread_stopper = DB_MANAGER.listen('db_notifications', lambda payload:_events.append(payload))

    #loop through categorisation tasks
    while(True):
        processEvents()
        processGeos()
        processMacs()
        apiUrl = config['api']['url'] + '/devices'
        devices = requests.get(url=apiUrl).json()["manDev"]
        if args.burst:
            print("Doing burstification")
            packetBurstification(devices)
        if args.predict:
            print("Doing prediction")
            burstPrediction(devices)

        #exit gracefully if we were asked to shutdown
        if handler.exit:
            listener_thread_stopper()
            break
        
        time.sleep(INTERVAL)

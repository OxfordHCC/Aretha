import requests
import urllib.parse
import datetime
import sys
import os

DEBUG = True
TRAFFIC_THRESHOLD = 10 #% increase or decrease that will trigger an alert

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts
DB_MANAGER = databaseBursts.dbManager()
timestamp = datetime.datetime.now().isoformat()
current_models = dict()

#Get raw list iof devices from the API
devices = requests.get(url='http://localhost:4201/api/devices').json()

#Filter out devices which are unknown
devices_filtered = []
for device in devices:
    if 'Unknown' not in device:
        devices_filtered.append(device)

#Get a list of destinations for each device and store this as a model in the DB
for device in devices_filtered:
    destinations = requests.get(url='http://localhost:4201/api/destinations/' + urllib.parse.quote(device)).json()
    if destinations['total'] == 0:
        print("Skipping model for " + device)
    else:
        for destination in destinations['destinations']:
            current_models[(device[:20],destination['name'][:20])] = (destination['country'], destination['impact'])
            if DEBUG:
                print("INSERT INTO models VALUES(" + device[:20] + ", " + timestamp + ", " + destination['name'][:20] + ", " + destination['country'][:20] + ", " + str(destination['impact']) + ")")
            else:
                DB_MANAGER.execute("INSERT INTO models(name, time, destination, location, impact) VALUES(%s, %s, %s, %s, %s)", (device[:20], timestamp, destination['name'][:20], destination['country'][:20], destination['impact']))

#Get models for these devices that were made in the last 24-48 hours
oneday = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
#twoday = (datetime.datetime.now() - datetime.timedelta(days=2)).isoformat()
twoday = (datetime.datetime.now() - datetime.timedelta(days=20)).isoformat()

#build up a string of devices to get previous models for (no point in comparing devices not currently active
query_string = "SELECT * FROM models where time > %s AND time < %s AND name = ''"
for device in devices_filtered:
    query_string += " OR name = %s"
results = DB_MANAGER.execute(query_string, (twoday, oneday) + tuple(devices_filtered))
for row in results:
    #calculate traffic differentials
    diff = int((current_models[(row[1],row[3])][1] / row[5]) * 100)

    if abs(diff - 100) > TRAFFIC_THRESHOLD:
        if diff > 100:
            diff_text = str(diff - 100) + "% more traffic to "
        if diff < 100:
            diff_text = str(100 - diff) + "% less traffic to "

        print(row[1] + " has sent " + diff_text + row[3] + " since yesterday.")

#We need a way of specifying a time period to the API, so that we can actually compare these, otherwise they will only increase
#But iotdata.json doesn't make the distinction, which is a bit awkward - perhaps we need a filter in categorise loop to only
#consider packets that were captured in the last 24 hours?

#Also need to decide how this is going to be used

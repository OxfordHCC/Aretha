import requests
import urllib.parse
import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts
DB_MANAGER = databaseBursts.dbManager()

#Get raw list iof devices from the API
devices = requests.get(url='http://localhost:4201/api/devices').json()

#Filter out devices which are unknown
devices_filtered = []
for device in devices:
    if 'Unknown' not in device:
        devices_filtered.append(device)

#Get a list of destinations for each device
for device in devices_filtered:
    destinations = requests.get(url='http://localhost:4201/api/destinations/' + urllib.parse.quote(device)).json()
    timestamp = datetime.datetime.now().isoformat()
    if destinations['total'] == 0:
        print("Skipping model for " + device)
    else:
        for destination in destinations['destinations']:
            print("INSERT INTO models VALUES(" + device[:20] + ", " + timestamp + ", " + destination['name'][:20] + ", " + destination['country'][:20] + ", " + str(destination['impact']) + ")")
            DB_MANAGER.execute("INSERT INTO models(name, time, destination, location, impact) VALUES(%s, %s, %s, %s, %s)", (device[:20], timestamp, destination['name'][:20], destination['country'][:20], destination['impact']))

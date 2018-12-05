#! /usr/bin/env python3

import requests
import urllib.parse
import datetime
import sys
import os

DEBUG = False
TRAFFIC_THRESHOLD = 10 #% increase or decrease that will trigger an alert
WINDOW = 50 #number of days to calculate impacts over

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts
DB_MANAGER = databaseBursts.dbManager()
timestamp = datetime.datetime.now().isoformat()
destinations_new = set()
destinations_old = set()
per_device = dict()

#Get list of devices and destinations from the API
devices = requests.get(url="http://localhost:4201/api/devices").json()["manDev"]
impacts = requests.get(url=f"http://localhost:4201/api/impacts/{WINDOW}").json()

impacts.append({"appid":"30:35:ad:d3:2c:f2","companyName":"Auazon.com, Inc.","companyid":"54.246.110.97","country_code":"RU","impact":2334,"latitude":53.3331,"longitude":-6.2489})

#Generate a snapshot for each device 
for impact in impacts:
    device = impact["appid"]
    destination = impact["companyName"]
    country = impact["country_code"]
    if device not in per_device:
        per_device[device] = dict()
    if destination not in per_device[device]:
        per_device[device][destination] = dict()
        per_device[device][destination]["country"] = country
        per_device[device][destination]["impact"] = impact["impact"]
        destinations_new.add(f"{device}*{destination}")
        destinations_new.add(f"{device}*{country}")
    else:
        per_device[device][destination]["impact"] += impact["impact"]

if DEBUG:
    print(per_device)

#Save those snapshots
for device in per_device:
    for destination in per_device[device]:
        sql_string = f"INSERT INTO models(device, time, destination, location, impact) VALUES('{device}', '{timestamp}', '{destination[:20]}', '{per_device[device][destination]['country']}', {per_device[device][destination]['impact']})"
        if DEBUG:
            print(sql_string)
        else:
            DB_MANAGER.execute(sql_string,())

#Get models for these devices that were made in the last 24-48 hours
query_string = f"SELECT * FROM models where time < now() - interval '2 day' AND time > now() - interval '1 day' AND (device = ''"
for device in per_device:
    query_string += f" OR device = '{device}'"
query_string += ")"
if DEBUG:
    print(query_string)
else:
    #calculate traffic differentials
    results = DB_MANAGER.execute(query_string, ())
    for row in results:
        _,device,_,destination,country,impact = row
        diff = (impact/per_device[device][destination]["impact"]) * 100
        destinations_old.add(f"{device}*{destination}")
        destinations_old.add(f"{device}*{country}")

        if abs(diff - 100) > TRAFFIC_THRESHOLD:
            if diff > 100:
                diff_text = str(diff - 100) + "% more traffic to "
            if diff < 100:
                diff_text = str(100 - diff) + "% less traffic to "

            print(f"{device} has sent {diff}{diff_text}{destination} since yesterday.")
    if len(destinations_new - destinations_old) > 0:
        for item in destinations_new - destinations_old:
            device,destination = item.split("*")
            print(f"{device} has started sending data to new destination {destination}")

#TODO: Need to log these alerts somewhere, probably a new table?

#! /usr/bin/env python3

import sys, os, configparser, time
from flask import Flask, request, jsonify, make_response, Response
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts

app = Flask(__name__) # WSGI entry point
IOTR_BASE = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
CONFIG_PATH = IOTR_BASE + "/config/config.cfg"
CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_PATH)
DB_MANAGER = None
KEY = None
queue = dict()

@app.route('/beacon', methods=['GET', 'POST'])
def beacon():
    global KEY
    i = request.form.get("i")
    k = request.form.get("k")
    p = request.form.get("p")
    g = request.form.get("g")
    f = request.form.get("f")
    if KEY == k:
        DB_MANAGER.execute("INSERT INTO beacon(source, packets, geodata, firewall) VALUES(%s, %s, %s, %s)", (int(i), int(p), int(g), int(f)))
        return(signal(i))
    return "Request handled unsuccessfully", 403

@app.route('/admin/connect/<gid>', methods=['GET', 'POST'])
def connect(gid):
    global KEY
    print("CN for " + gid + ", open secure connection")
    k = request.form.get("k")
    if KEY == k:
        if not gid in queue:
            queue[gid] = []
        queue[gid].append("CN")
        return "Request handled successfully"
    else:
        return "Request handled unsuccessfully", 403

@app.route('/admin/restart/<gid>', methods=['GET', 'POST'])
def restart(gid):
    global KEY
    print("RB for " + gid + ", reboot NUC")
    k = request.form.get("k")
    if KEY == k:
        if not gid in queue:
            queue[gid] = []
        queue[gid].append("RB")
        return "Request handled successfully"
    else:
        return "Request handled unsuccessfully", 403

@app.route('/admin/reset/<gid>', methods=['GET', 'POST'])
def reset(gid):
    global KEY
    print("RS for " + gid + ", reset IoT Refine")
    k = request.form.get("k")
    if KEY == k:
        if not gid in queue:
            queue[gid] = []
        queue[gid].append("RS")
        return "Request handled successfully"
    else:
        return "Request handled unsuccessfully", 403

@app.route('/admin/expr/<gid>', methods=['GET', 'POST'])
def stage(gid):
    global KEY
    print("EX for " + gid + ", update " + name + " to " + value)
    
    k = request.form.get("k")
    name = request.form.get("n")
    value = request.form.get("v")
    if KEY == k:
        if not gid in queue:
            queue[gid] = []
        queue[gid].append("EX " + name "; " + value)
        return "Request handled successfully"
    else:
        return "Request handled unsuccessfully", 403

@app.before_first_request
def init():
    global DB_MANAGER
    global KEY
    DB_MANAGER = databaseBursts.dbManager()
    KEY = CONFIG['beacon']['key']

def signal(source):
    if queue.get(source, None) is None or queue.get(source, None) == []:
        return "Request handled successfully"
    else:
        return queue[source].pop()

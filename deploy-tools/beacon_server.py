import sys, os, configparser
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

@app.route('/beacon/<k>/<p>/<g>/<f>')
def beacon(k, p, g, f):
    global KEY
    if KEY == k:
        DB_MANAGER.execute("INSERT INTO beacon(source, packets, geodata, firewall) VALUES(%s, %s, %s, %s)", (request.remote_addr, p, g, f))
        return "Request handled successfully"
    return "Request handled unsuccessfully"

@app.before_first_request
def init():
    global DB_MANAGER
    global KEY
    DB_MANAGER = databaseBursts.dbManager()
    KEY = CONFIG['beacon']['key']

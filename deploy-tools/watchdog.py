#! /usr/bin/env python3

import logging, os, sys
IOTR_BASE = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', filename=IOTR_BASE + "/config/log.txt", level=logging.DEBUG)
logging.info("===starting IoT-Refine watchdog pass===")

import subprocess, datetime, configparser, urllib.request
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts

DB_MANAGER = databaseBursts.dbManager()
CONFIG_PATH = IOTR_BASE + "/config/config.cfg"
CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_PATH)
restart = False

logging.info("done config and setup")

# check status of data capture
logging.info("checking data capture")
packets_now = DB_MANAGER.execute("SELECT COUNT(id) FROM packets", (), all=False)[0]
packets_past = int(CONFIG['watchdog']['packets'])
if packets_past == packets_now:
    restart = True
    try:
        urllib.request.urlopen(f"{CONFIG['beacon']['url']}/{CONFIG['beacon']['key']}/error/capture")
        logging.warning("no change in packet count since last pass - reset queued and beacon sent")
    except:
        logging.warning("no change in packet count since last pass - reset queued but error sending beacon")
else:
    CONFIG['watchdog']['packets'] = str(packets_now)
    logging.info("data capture ok")

# check status of ipdata
logging.info("checking access to ipdata api")
try:
    urllib.request.urlopen(f"https://api.ipdata.co/8.8.8.8?api-key={CONFIG['ipdata']['key']}")
    logging.info("ipdata api access ok")
except:
    restart = True
    try:
        urllib.request.urlopen(f"{BEACON_URL}/{BEACON_KEY}/error/ipdata")
        logging.warning("cannot access ipdata api - reset queued and beacon sent")
    except:
        logging.warning("cannot access ipdata api - reset queued but error sending beacon")

# mitigate angular problems
if datetime.datetime.now().hour > 2 and datetime.datetime.now().hour < 4:
    restart = True
    logging.info("scheduling restart to mitigate angular problems")

# restart if required
if restart:
    logging.info("restart scheduled")
    subprocess.run(["sudo", "systemctl", "restart", "iotreifne"])
    logging.info("restart completed")
else:
    logging.info("no restart scheduled")

# write measurments back to config file
with open(CONFIG_PATH, 'w') as configfile:
    CONFIG.write(configfile)
    logging.info("written packet count back to log file")

logging.info("watchdog pass complete")

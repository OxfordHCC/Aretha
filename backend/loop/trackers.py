import os
import socket
import tldextract
from config import config

TRACKERS = []
initialised = False

# again, we defer any use of config until after reading config file in
# main function
def init():
    global initialised
    try:
        trackers_path = os.path.join(ARETHA_BASE, config['loop']['trackers'])
        with open(trackers_path) as trackers_file:
            for line in trackers_file.readlines():
                TRACKERS.append(line.strip('\n'))
        print("ok")
        initialised = True
    except:
        print("error while reading trackers from file...")
    
    
def is_tracker(ip):
    if not initialised:
        init()
        
    if len(TRACKERS) == 0:
        return False
    
    try:
        domain = tldextract.extract(socket.gethostbyaddr(ip)[0])
        if domain.registered_domain in TRACKERS:
            return True
        return False
    except:
        return False



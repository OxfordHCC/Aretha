from os.path import join, normpath, isabs
import socket
import tldextract
from loop import log
from util.project_variables import ARETHA_BASE

TRACKERS = []
initialised = False

# again, we defer any use of config until after reading config file in
# main function
def init_trackers(trackers_path):
    global initialised

    resolve_path = trackers_path
    if(not isabs(trackers_path)):
        resolved_path = normpath(join(ARETHA_BASE, trackers_path))

    try:
        log.debug(f"Trying to init trackers file {resolved_path}")
        with open(resolved_path) as trackers_file:
            for line in trackers_file.readlines():
                TRACKERS.append(line.strip('\n'))
        initialised = True
        log.debug(f"Initialized tracker file {resolved_path}.")
    except Exception as e:
        log.debug("Error while reading trackers from file.", exc_info=e)
    
    
def is_tracker(ip):
    if not initialised:
        log.warn("Trackers lib not initialized. You may want to call trackers.init_trackers before calling is_tracker.")

    if len(TRACKERS) == 0:
        return False
    
    try:
        domain = tldextract.extract(socket.gethostbyaddr(ip)[0])
        if domain.registered_domain in TRACKERS:
            return True
        return False
    except:
        return False



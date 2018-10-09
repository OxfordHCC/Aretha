import sys
import time
import os
import signal

INTERVAL = 5

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "categorisation"))
from burstProcessing import packetBurstification, burstPrediction # pylint: disable=C0413, E0401
 
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import refineJsonData # pylint: disable=C0413, E0401

class sigTermHandler:
    exit = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    def shutdown(self, signum, frame):
        self.exit = True

if __name__ == '__main__':
    handler = sigTermHandler()
    while(True):
        print("Loop start")
        packetBurstification()
        burstPrediction()
        refineJsonData.compileUsageImpacts()
        if handler.exit:
            break
        time.sleep(INTERVAL)
    print("Graceful shutdown")


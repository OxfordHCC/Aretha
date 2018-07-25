import sys
import time
import os

INTERVAL = 5

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "categorisation"))
from burstProcessing import packetBurstification, burstPrediction # pylint: disable=C0413, E0401
 
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import refineJsonData # pylint: disable=C0413, E0401

while(True):
    print("Loop start")
    packetBurstification()
    burstPrediction()
    refineJsonData.compileUsageImpacts()
    time.sleep(INTERVAL)


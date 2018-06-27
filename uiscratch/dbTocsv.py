import psycopg2, os, sys, csv
from collections import defaultdict
from ipwhois import IPWhois

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts # pylint: disable=C0413, E0401

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "categorisation"))
from burstProcessing import getDeviceFromMac # pylint: disable=C0413, E0401

LOCAL_IP_MASK_16 = "192.168."
LOCAL_IP_MASK_24 = "10."


getAll = """ SELECT * FROM bursts ORDER BY id"""
print ( databaseBursts.execute(getAll, ""))

getAll = """ SELECT * FROM categories ORDER BY id"""
print ( databaseBursts.execute(getAll, ""))

getALL = """ SELECT * FROM packets ORDER BY id """
result = databaseBursts.execute(getALL, "")

macs = """ SELECT DISTINCT mac FROM packets """
macRes = databaseBursts.execute(macs, "")

print(macRes)

allMacs = []

for tuple in macRes:
    allMacs.append(tuple[0])

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"packetData.csv"), 'w', newline='') as csvfile: 
    writer = csv.writer(csvfile, delimiter=',')

    titles = ["ipdest"]

    for mac in allMacs:
        dev = getDeviceFromMac(mac)
        titles.append(dev)

    writer.writerow(titles)

    lengthsPerIpPerMac = defaultdict(int)

    allDests = set()

    for row in result:
        if (LOCAL_IP_MASK_16 in row[2] or LOCAL_IP_MASK_24 in row[2]) and \
        (LOCAL_IP_MASK_16 in row[3] or LOCAL_IP_MASK_24 in row[3]):
            # internal comms so ignore
            continue
        if (LOCAL_IP_MASK_16 in row[2] or LOCAL_IP_MASK_24 in row[2]):
            destination = row[3]
        else:
            destination = row[2]

        allDests.add(destination)
        
        lengthsPerIpPerMac[destination+row[4]] += 1 #length

    for dest in allDests:
        try:
            obj = IPWhois(dest)
            res = obj.lookup_whois()
            newRow = [res["nets"][0]['description']]
            #print(res)
        except:
            newRow = [dest]
        
        for mac in allMacs:
            try:
                newRow.append(lengthsPerIpPerMac[dest+mac])
            except:
                newRow.append("0")

        writer.writerow(newRow)
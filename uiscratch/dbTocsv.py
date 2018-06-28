import psycopg2, os, sys, csv, json
from collections import defaultdict
from ipwhois import IPWhois

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts # pylint: disable=C0413, E0401

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "categorisation"))
from burstProcessing import getDeviceFromMac # pylint: disable=C0413, E0401

dataPath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "src", "assets", "data")

LOCAL_IP_MASK_16 = "192.168."
LOCAL_IP_MASK_24 = "10."

with open(os.path.join(dataPath, "iotData.json"), 'r') as fp:
    data = json.load(fp)

getALL = """ SELECT * FROM packets WHERE id > """ + str(data["idSoFar"]) + """ORDER BY id """
result = databaseBursts.execute(getALL, "")

macs = """ SELECT DISTINCT mac FROM packets """
macRes = databaseBursts.execute(macs, "")

print(result)
print(macRes)

allMacs = []

for tuple in macRes:
    allMacs.append(tuple[0])

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"packetData.csv"), 'w', newline='') as csvfile: 
    writer = csv.writer(csvfile, delimiter=',')

    titles = ["ipdest"]

    TOREFINE = []
    REFINEUSAGE = []

    for mac in allMacs:
        dev = getDeviceFromMac(mac)
        REFINEUSAGE.append({"appid":dev, "mins":15})
        titles.append(dev)

    writer.writerow(titles)

    lengthsPerIpPerMac = defaultdict(int)

    allDests = set()
    if len(result) > 0:
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
            newRow = [dest]
            
            for mac in allMacs:
                try:
                    newRow.append(lengthsPerIpPerMac[dest+mac])
                    if(lengthsPerIpPerMac[dest+mac] !=0):
                        TOREFINE.append({"appid":getDeviceFromMac(mac), "companyid":newRow[0],"impact":lengthsPerIpPerMac[dest+mac]})
                except:
                    newRow.append("0")

            writer.writerow(newRow)

#print(TOREFINE)
#print(REFINEUSAGE)


if len(result) > 0:
    bigDictionary = {"usage": REFINEUSAGE, "impacts": TOREFINE, "idSoFar":result[-1][0]}

    with open(os.path.join(dataPath,"iotData.json"), 'w') as fp:
        json.dump(bigDictionary, fp, sort_keys=True, indent=4)
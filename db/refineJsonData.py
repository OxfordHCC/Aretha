import psycopg2, os, sys, json, csv
from collections import defaultdict
from ipwhois import IPWhois

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts # pylint: disable=C0413, E0401

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "macHelpers"))
from macHelpMethods import getDeviceFromMac # pylint: disable=C0413, E0401

dataPath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "src", "assets", "data")

LOCAL_IP_MASK_16 = "192.168."
LOCAL_IP_MASK_24 = "10."

def updateImpact(impacts, device, destination, number):
    """
    For an impact that is already, update the value to number
    """
    for impact in impacts:
        if impact["appid"] == device:
            toRemove = impact
            break
    impacts.remove(impact)
    impacts.append({"appid":device, "companyid":destination, "impact":number})
    return impacts
    

def compileUsageImpacts():
    
    ## Get any impacts and usage if we already have some 

    with open(os.path.join(dataPath, "iotData.json"), 'r') as fp:
        data = json.load(fp)
    try:
        impacts = data["impacts"]
    except:
        impacts = []
    try:
        usage = data["usages"]
    except:
        usage = []

    ## If the data was reset by script, start over

    resetted = False
    if data["dbreset"]:
        getALL = """ SELECT * FROM packets ORDER BY id """
        usage = []
        impacts = []
        resetted = True
    else:
        getALL = """ SELECT * FROM packets WHERE id > """ + str(data["idSoFar"]) + """ORDER BY id """

    result = databaseBursts.execute(getALL, "")

    macs = """ SELECT DISTINCT mac FROM packets """
    macRes = databaseBursts.execute(macs, "")

    #print(result)
    #print(macRes)

    ## Get all the mac address 

    allMacs = []

    for tuple in macRes:
        allMacs.append(tuple[0])

    ## For each mac address put a fake usage in, so that it displays
    
    for mac in allMacs:
        dev = getDeviceFromMac(mac)
        miss = False
        for thisUsage in usage:
            if dev == thisUsage["appid"]:
                miss = True
        if not miss:
            usage.append({"appid":dev, "mins":15})

    ## Check to see if we already have impacts for any new mac and destination
    ## If we have an impact for the mac, store mac and dest, and that value 

    alreadyHaveEntry = []

    lengthsPerIpPerMac = defaultdict(int)

    for mac in allMacs:
        dev = getDeviceFromMac(mac)
        for impact in impacts:
            if impact["appid"] == dev:
                alreadyHaveEntry.append((impact["companyid"],dev))
                lengthsPerIpPerMac[impact["companyid"] + mac] = impact["impact"]
        


    allDests = set()
    if len(result) > 0:
        
        ## Get every external destination, and count them for that mac 

        for row in result:
            print(row)
            if (LOCAL_IP_MASK_16 in row[2] or LOCAL_IP_MASK_24 in row[2]) and \
            (LOCAL_IP_MASK_16 in row[3] or LOCAL_IP_MASK_24 in row[3]):
                # internal comms so ignore
                continue
            if (LOCAL_IP_MASK_16 in row[2] or LOCAL_IP_MASK_24 in row[2]):
                destination = row[3]
            else:
                destination = row[2]

            allDests.add(destination)
            
            #count data transfered in mbytes
            lengthsPerIpPerMac[destination+row[4]] += row[5]

        ## For each destination we have to add a row to the json
        ## Want to add the device, destination and number to make stacked bars

        for dest in allDests:
            for mac in allMacs:
                try:
                    if(lengthsPerIpPerMac[dest+mac] !=0):

                        if (dest,getDeviceFromMac(mac)) in alreadyHaveEntry:
                            impacts = updateImpact(impacts, getDeviceFromMac(mac), dest, lengthsPerIpPerMac[dest+mac])
                        else:
                            impacts.append({"appid":getDeviceFromMac(mac), "companyid":dest, "impact":lengthsPerIpPerMac[dest+mac]})

                except KeyError:
                    print("Key error, but not sure why")
                


    #print(impacts)
    #print(usage)


    if len(result) > 0:
        bigDictionary = {"usage": usage, "impacts": impacts, "idSoFar":result[-1][0]}

        with open(os.path.join(dataPath, "iotData.json"), 'r') as fp:
            data = json.load(fp)

        if resetted:
            data["dbreset"] = False

        data["usage"] = bigDictionary["usage"]
        data["impacts"] = bigDictionary["impacts"]
        data["idSoFar"] = bigDictionary["idSoFar"]

        with open(os.path.join(dataPath,"iotData.json"), 'w') as fp:
            json.dump(data, fp, sort_keys=True, indent=4)

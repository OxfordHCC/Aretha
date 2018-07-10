import psycopg2, os, sys, json, csv
from collections import defaultdict
from ipwhois import IPWhois
from ipdata import ipdata

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts # pylint: disable=C0413, E0401

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "macHelpers"))
from macHelpMethods import getDeviceFromMac # pylint: disable=C0413, E0401

dataPath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "src", "assets", "data")

LOCAL_IP_MASK_16 = "192.168."
LOCAL_IP_MASK_24 = "10."
FAKE_GEO = {
                "asn": "X",
                "calling_code": "1",
                "city": "Unknown",
                "continent_code": "Unknown",
                "continent_name": "Unknown",
                "count": "1",
                "country_code": "Unknown",
                "country_name": "Unknown",
                "flag": "Unknown",
                "ip": "0",
                "is_eu": False,
                "languages": [
                    {
                        "name": "English",
                        "native": "English"
                    }
                ],
                "latitude": 0,
                "longitude": 0,
                "organisation": "Unknown",
                "postal": "Unknown",
                "region": "Unknown",
                "region_code": "Unknown",
                "threat": {
                    "is_anonymous": False,
                    "is_bogon": False,
                    "is_known_abuser": False,
                    "is_known_attacker": False,
                    "is_proxy": False,
                    "is_threat": False,
                    "is_tor": False
                },
                "time_zone": {
                    "abbr": "PDT",
                    "current_time": "2018-07-09T08:27:30.360976-07:00",
                    "is_dst": True,
                    "name": "America/Los_Angeles",
                    "offset": "-0700"
                }
}

def getFake(ip):
    res = FAKE_GEO
    res["ip"] = ip
    return res

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
    
def getGeoFromIp(ip):
    _ip = ipdata.ipdata(apikey="a1d902ad33fcd325dc6f5c94e93bb3d3c8337194a9738855b682b7f4")
    data = _ip.lookup(ip)
    if data['status']==200:
        data["response"].pop("emoji_flag", None)
        data["response"].pop("emoji_unicode", None)
        data["response"].pop("currency", None)
        return data['response']
    else:
        return data['response']

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

    
    ## Add everything to the dictinoary of data that is stored in assets
                

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

    ## Now get the geo data and store that also 

    #print(data["impacts"])
    #print(data["geos"][0])

    ## Get all the IP addresses that need looking up 

    try:
        ipsToIgnore = data["ipsToIgnore"]
    except KeyError:
        ipsToIgnore = []

    impactsToDo = []
    duffImpacts = [] # those with IPs that don't work 

    for impact in data["impacts"]:
        try:
            miss = False
            ip = impact["companyid"]
            for geo in data["geos"]:
                #print(geo)
                if geo["geo"] == """{\"message\": \"0 does not appear to be an IPv4 or IPv6 address\"}""":
                    miss = True
                elif ip == geo["geo"]["ip"]:
                    miss = True
            
            for difIP in ipsToIgnore:
                if ip == difIP:
                    # Only add a fake geo if we don't already have it 
                    if not miss:
                        duffImpacts.append(impact)
                    miss = True
                    
            
            if not miss:
                impactsToDo.append(impact)
        except KeyError:
            impactsToDo.append(impact)

    print(impactsToDo)

    ## Get geo for each impact and add it 

    try:
        newGeos = data["geos"]
    except KeyError:
        newGeos = []

    for impact in impactsToDo:
        geo = getGeoFromIp(impact["companyid"])
        print("Calling")
        if geo != """{\"message\": \"0 does not appear to be an IPv4 or IPv6 address\"}""":
            newGeos.append({"appid": impact["appid"], "impact": impact["impact"], "geo": geo})
        else:
            # store duff IPs so that they aren't called again
            ipsToIgnore.append(impact["companyid"])

    for impact in duffImpacts:
        geo = getFake(impact["companyid"])
        newGeos.append({"appid": impact["appid"], "impact": impact["impact"], "geo": geo})

    data["geos"] = newGeos
    data["ipsToIgnore"] = ipsToIgnore

    with open(os.path.join(dataPath,"iotData.json"), 'w') as fp:
            json.dump(data, fp, sort_keys=True, indent=4)


    ## TODO: Now using this data just gained, give names for each organisation on impacts
    newImpacts = data["impacts"]
    for impact in data["impacts"]:
        
        for geo in data["geos"]:
            
            if impact["companyid"] == geo["geo"]["ip"]:
                
                newImpact = impact
                newImpact["companyName"] = geo["geo"]["organisation"]
                newImpacts.remove(impact)
                newImpacts.append(newImpact)
                break
    
    for impact in data["impacts"]:
        try:
            org = impact["companyName"]
        except KeyError:
            impact["companyName"] = "Unknown"

    data["impacts"] = newImpacts
    with open(os.path.join(dataPath,"iotData.json"), 'w') as fp:
            json.dump(data, fp, sort_keys=True, indent=4)
        
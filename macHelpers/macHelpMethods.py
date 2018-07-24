import requests, os, pickle, json, sys

FILE_PATH = os.path.dirname(os.path.abspath(__file__))

DATAPATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "src", "assets", "data")

def getManufactFromMac(mac):
    """ 
    Gets a device manufacturer from a mac
    Uses a pickled dict to relate mac addresses to manufacturers from the api
    """
    with open(os.path.join(DATAPATH, "iotData.json"), 'r') as fp:
        data = json.load(fp)
    try:
        manDict = data["macMan"]
    except:
        manDict = {}

    if mac in manDict.keys():
        return manDict[mac]

    else:
        r = requests.get("https://api.macvendors.com/" + mac)
        manufacturer = r.text

        if "errors" in manufacturer:
            counter = 1
            for value in manDict.items():
                if "Unknown" in value and value[-1] >= counter:
                    counter = value[-1] + 1
            manDict[mac] = "Unknown" + str(counter)
        else:
            manDict[mac] = manufacturer

        data["macMan"] = manDict

        with open(os.path.join(DATAPATH,"iotData.json"), 'w') as fp:
            json.dump(data, fp, sort_keys=True, indent=4)

        return manDict[mac]
    

def getDeviceFromMac(mac):
    """ 
    Gets a device name from a mac 
    Relates manufacturer names to devices via a json dictionary
    """
    
    manufact = getManufactFromMac(mac)

    with open(os.path.join(DATAPATH, "iotData.json"), 'r') as f:
        data = json.load(f)

    manDev = data["manDev"]

    try:
        dev = manDev[manufact + " : " + mac]
    except:
        if "Unknown" in manufact:
            dev = manufact
            manDev[manufact + " : " + mac] = manufact
        else:
            dev = "Unknown - " + manufact
            manDev[manufact + " : " + mac] = "Unknown - " + manufact

        data["manDev"] = manDev

        with open(os.path.join(DATAPATH,"iotData.json"), 'w') as fp:
            json.dump(data, fp, sort_keys=False, indent=4)


    return dev
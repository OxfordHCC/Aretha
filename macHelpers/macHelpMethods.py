import requests, os, pickle, json, sys

FILE_PATH = os.path.dirname(os.path.abspath(__file__))

DATAPATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "src", "assets", "data")


class MacHelper():

    def __init__(self):
        with open(os.path.join(DATAPATH, "iotData.json"), 'r') as fp:
            self.data = json.load(fp)

    def getManufactFromMac(self, mac):
        """ 
        Gets a device manufacturer from a mac
        Uses a pickled dict to relate mac addresses to manufacturers from the api
        """
                
        try:
            manDict = self.data["macMan"]
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

            self.data["macMan"] = manDict

            with open(os.path.join(DATAPATH,"iotData.json"), 'w') as fp:
                json.dump(self.data, fp, sort_keys=True, indent=4)

            return manDict[mac]
        

    def getDeviceFromMac(self, mac):
        """ 
        Gets a device name from a mac 
        Relates manufacturer names to devices via a json dictionary
        """
        
        manufact = self.getManufactFromMac(mac)

       

        manDev = self.data["manDev"]

        try:
            dev = manDev[manufact + " : " + mac]
        except:
            if "Unknown" in manufact:
                dev = manufact
                manDev[manufact + " : " + mac] = manufact
            else:
                dev = "Unknown - " + manufact
                manDev[manufact + " : " + mac] = "Unknown - " + manufact

            self.data["manDev"] = manDev

            with open(os.path.join(DATAPATH,"iotData.json"), 'w') as fp:
                json.dump(self.data, fp, sort_keys=False, indent=4)


        return dev
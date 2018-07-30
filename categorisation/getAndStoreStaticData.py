import psycopg2, os, time, datetime, sys, socket, json
from scapy.all import rdpcap, IP, TCP # pylint: disable=C0413, E0611

INTERVAL = 5

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "categorisation"))
from burstProcessing import packetBurstification, burstPrediction # pylint: disable=C0413, E0401

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts # pylint: disable=C0413, E0401
 
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import refineJsonData # pylint: disable=C0413, E0401


DATAPATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "src", "assets", "data")
FILE_PATH = os.path.dirname(os.path.abspath(__file__))

MAC_IP_DICT = {"Alexa":("88:71:e5:e9:9e:6c", "192.168.4.2"), 
               "Google":("20:df:b9:37:b2:70","192.168.4.2"),
               "Hue":("00:17:88:7b:dd:8c","192.168.4.16"),
               "WeMoSwitch":("08:86:3b:c9:ac:f5","192.168.4.6"),
               "Nokia":("00:24:e4:66:6b:4c","192.168.4.12"),
               "WeMoMotion":("08:86:3b:c9:c0:bd","192.168.4.18")}

DB_MANAGER = databaseBursts.dbManager()

def test():
    print("Test")

first = True

def putDataIntoDB(filename):
    # Put data into db
    results = []

    for packet in rdpcap(os.path.join(os.path.dirname(FILE_PATH),"staticData", filename)):
        if first:
            #first = False
            try:
                

                t = datetime.datetime.utcfromtimestamp(packet.time)
                strTime = t.strftime('%d/%m/%Y %H:%M:%S.%f')
                scr = packet[IP].src
                dst = packet[IP].dst
                """
                if "192.168" in packet[IP].src:
                    mac = packet.src
                else:
                    mac = packet.dst """
                # Mac bodge cause of range extenders 

                for key in MAC_IP_DICT.keys():
                    if key in filename:
                        mac = MAC_IP_DICT[key][0]                

                        length = str( int(packet.len) + 14 )

                        proto = packet[TCP].dport

                        # The following ignores noise in the pcaps 
                        if MAC_IP_DICT[key][1] == packet[IP].src or MAC_IP_DICT[key][1] == packet[IP].dst:
                            #results.append((strTime, scr, dst, mac, length, proto))
                            results.append(strTime)
                            results.append(scr) 
                            results.append(dst) 
                            results.append(mac)
                            results.append(length)
                            results.append(proto)

                        break # Should only match one key

            except IndexError:
                pass # This fires if the packet doesn't have an IP layer

    sql = """INSERT INTO packets(time, src, dst, mac, len, proto) VALUES(%s, %s, %s, %s, %s, %s)""" + ", (%s, %s, %s, %s, %s, %s)"*(int(len(results)/6)-1) + """ RETURNING id;"""   
    #print(sql)
    #print(results)
    #print(len(results))
    #print((int(len(results)/6)-1))
    DB_MANAGER.execute(sql, results, all=False)
    
def main():
    
    DB_MANAGER.execute(open(os.path.join(os.path.dirname(FILE_PATH), "db", "schema.sql"), "rb").read(), "")

    with open(os.path.join(DATAPATH,"iotData.json"), 'r') as fp:
        data = json.load(fp)
        data["dbreset"] = True
    with open(os.path.join(DATAPATH,"iotData.json"), 'w') as fp:
        json.dump(data, fp, sort_keys=True, indent=4)

    f = []
    for (dirpath, dirnames, filenames) in os.walk(os.path.join(os.path.dirname(FILE_PATH), "staticData")):
        f.extend(filenames)
        break

    for file in f:
        putDataIntoDB(file)
        print("Done: " + file)

    packetBurstification()
    print("Burstification complete")
    burstPrediction()
    print("Prediction complete")

    refineJsonData.compileUsageImpacts()
    print("JSON extraction complete")

def onlyBurst():
    
    packetBurstification()
    print("Burstification complete")
    burstPrediction()
    print("Prediction complete")

    refineJsonData.compileUsageImpacts()
    print("JSON extraction complete")

def updateWithNew(filename):
    putDataIntoDB(filename)
    print("Done: " + filename)

    packetBurstification()
    print("Burstification complete")
    burstPrediction()
    print("Prediction complete")

    refineJsonData.compileUsageImpacts()
    print("JSON extraction complete")

if __name__ == "__main__":
    try:
        filename = sys.argv[1]
        updateWithNew(filename)
    except:
        main()
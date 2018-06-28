import psycopg2, os, time, datetime, sys, socket, json
from scapy.all import rdpcap, IP, TCP # pylint: disable=C0413, E0611

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts # pylint: disable=C0413, E0401

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "categorisation"))
from burstProcessing import packetBurstification, burstPrediction # pylint: disable=C0413, E0401



DATAPATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "src", "assets", "data")
FILE_PATH = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(DATAPATH,"iotData.json"), 'r') as fp:
    data = json.load(fp)
    data["dbreset"] = True
with open(os.path.join(DATAPATH,"iotData.json"), 'w') as fp:
    json.dump(data, fp, sort_keys=True, indent=4)


databaseBursts.execute(open(os.path.join(os.path.dirname(FILE_PATH), "db", "schema.sql"), "rb").read(), "")

first = True

for packet in rdpcap(os.path.join(os.path.join(os.path.dirname(FILE_PATH),"tests"), "testData", "AlexaTime1")):
    if first:
        #first = False
        try:
            sql = """INSERT INTO packets(time, src, dst, mac, len, proto) VALUES(%s, %s, %s, %s, %s, %s) RETURNING id;"""

            t = datetime.datetime.utcfromtimestamp(packet.time)
            strTime = t.strftime('%d/%m/%Y %H:%M:%S.%f')
            scr = packet[IP].src
            dst = packet[IP].dst
            if "192.168" in packet[IP].src:
                mac = packet.src
            else:
                mac = packet.dst
                

            length = str( int(packet.len) + 14 )

            proto = packet[TCP].dport

            databaseBursts.execute(sql, (strTime, scr, dst, mac, length, proto), all=False)

        except IndexError:
            pass

getAll = """ SELECT * FROM packets ORDER BY id"""
result = databaseBursts.execute(getAll, "")

for row in result:
    print(row)

packetBurstification()
burstPrediction()
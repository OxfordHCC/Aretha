import psycopg2, os, time, datetime
from scapy.all import rdpcap, IP, TCP
import databaseBursts


FILE_PATH = os.path.dirname(os.path.abspath(__file__))

databaseBursts.execute(open(os.path.join(FILE_PATH, "schema.sql"), "rb").read(), "")

first = True

for packet in rdpcap(os.path.join(FILE_PATH, "testData", "AlexaTime1")):
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
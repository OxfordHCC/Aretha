import psycopg2, os, time, datetime, sys
from scapy.all import rdpcap, IP, TCP # pylint: disable=C0413, E0611

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts # pylint: disable=C0413, E0401

DB_MANAGER = databaseBursts.dbManager()

FILE_PATH = os.path.dirname(os.path.abspath(__file__))

DB_MANAGER.execute(open(os.path.join(os.path.dirname(FILE_PATH), "db", "schema.sql"), "rb").read(), "")

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

            DB_MANAGER.execute(sql, (strTime, scr, dst, mac, length, proto), all=False)

        except IndexError:
            pass

getAll = """ SELECT * FROM packets ORDER BY id"""
result = DB_MANAGER.execute(getAll, "")

for row in result:
    print(row)
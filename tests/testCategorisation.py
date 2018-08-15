import psycopg2, os, sys, datetime 

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts # pylint: disable=C0413, E0401
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "categorisation"))
from burstProcessing import packetBurstification, burstPrediction # pylint: disable=C0413, E0401

packetBurstification()
burstPrediction()

DB_MANAGER = databaseBursts.dbManager()

getAll = """ SELECT * FROM bursts ORDER BY id"""
print ( DB_MANAGER.execute(getAll, ""))

getAll = """ SELECT * FROM categories ORDER BY id"""
print ( DB_MANAGER.execute(getAll, ""))

getALL = """ SELECT MIN(time), MIN(mac), burst, MIN(categories.name) FROM packets JOIN bursts ON bursts.id = packets.burst JOIN categories ON categories.id = bursts.category GROUP BY burst ORDER BY burst"""
result = DB_MANAGER.execute(getALL, "")

for row in result:
    print(row)



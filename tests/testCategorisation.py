import psycopg2, os, sys, datetime 

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import databaseBursts # pylint: disable=C0413, E0401
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "categorisation"))
from burstProcessing import packetBurstification, burstPrediction # pylint: disable=C0413, E0401

packetBurstification()
burstPrediction()

getAll = """ SELECT * FROM bursts ORDER BY id"""
print ( databaseBursts.execute(getAll, ""))

getAll = """ SELECT * FROM categories ORDER BY id"""
print ( databaseBursts.execute(getAll, ""))

getALL = """ SELECT MIN(time), MIN(mac), burst, MIN(categories.name) FROM packets JOIN bursts ON bursts.id = packets.burst JOIN categories ON categories.id = bursts.category GROUP BY burst ORDER BY burst"""
result = databaseBursts.execute(getALL, "")

for row in result:
    print(row)

epoch = datetime.datetime.utcfromtimestamp(0)

print((result[-1][0] - epoch).total_seconds() * 1000.0)
print(datetime.datetime.fromtimestamp(float(1380854103662)/1000.))
print(datetime.datetime.fromtimestamp(float(1526466410775)/1000.))
#-------------------------------------------1531219868115.278

print(datetime.datetime.fromtimestamp(float(1526466394738)/1000.))

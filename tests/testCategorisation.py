import psycopg2, os, sys

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

getALL = """ SELECT MIN(time), MIN(mac), burst FROM packets GROUP BY burst ORDER BY burst  """
result = databaseBursts.execute(getALL, "")

for row in result:
    print(row)

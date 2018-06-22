import databaseBursts, psycopg2
from burstProcessing import packetBurstification, burstPrediction

packetBurstification()
burstPrediction()

getAll = """ SELECT * FROM bursts ORDER BY id"""
print ( databaseBursts.execute(getAll, ""))

getAll = """ SELECT * FROM categories ORDER BY id"""
print ( databaseBursts.execute(getAll, ""))

getALL = """ SELECT * FROM packets WHERE burst = 7 ORDER BY id """
result = databaseBursts.execute(getALL, "")

for row in result:
    print(row)

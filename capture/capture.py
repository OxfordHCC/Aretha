#! /usr/bin/python3

import pyshark
import datetime
import psycopg2

#initialise vars
timestamp = 0 
queue = []

def DatabaseInsert(packets):
	global timestamp

	#open db connection
	conn = psycopg2.connect("dbname=testdb user=postgres password=password")
	cur = conn.cursor()
	
	#insert packets into table
	for packet in packets:
		cur.execute("INSERT INTO packets (time, src, dst, mac, len, proto) VALUES (%s, %s, %s, %s, %s, %s)", (timestamp + datetime.timedelta(seconds=float(packet.time)), packet.source, packet.destination, 'aa:aa:aa:aa:aa:aa', packet.length, packet.protocol))
		
	#commit the new records and close db connection
	conn.commit()
	cur.close()
	conn.close()

def QueuedCommit(packet):
	#commit packets to the database in 5 sec intervals
	#in an attempt to avoid db dying during high use periods

	now = datetime.datetime.now()
	global timestamp
	global queue

	#first packet in new queue
	if timestamp == 0:
		timestamp = now
	
	queue.append(packet)
	
	#time to commit to db
	if (now - timestamp).total_seconds() > 5:
		DatabaseInsert(queue)
		queue = []
		timestamp = 0
	
#configure capture object
capture = pyshark.LiveCapture(interface='wlp58s0', only_summaries=True)
capture.set_debug()

#start capturing
capture.apply_on_packets(QueuedCommit) #, timeout=30)
capture.close();

#! /usr/bin/python3

import pyshark
import datetime
import psycopg2

#constants
COMMIT_INTERVAL = 5
LOCAL_IP_MASK = "192"

#initialise vars
timestamp = 0 
queue = []

def DatabaseInsert(packets):
	global timestamp

	#open db connection
	conn = psycopg2.connect("dbname=testdb user=postgres password=password")
	cur = conn.cursor()
	
	for packet in packets:
		#clean up packet info before entry
		mac = ''
		src = ''
		dst = ''
		proto = ''

		try:
			if LOCAL_IP_MASK in packet['ip'].dst and LOCAL_IP_MASK not in packet['ip'].src:
				mac = packet['eth'].dst
			else:
				mac = packet['eth'].src
		except KeyError:
			mac = packet['eth'].src

		try:
			src = packet['ip'].src
			dst = packet['ip'].dst
		except KeyError:
			src = 0
			dst = 0

		if len(packet.highest_layer) > 10:
			proto = packet.highest_layer[:10]
		else:
			proto = packet.highest_layer

		#insert packets into table
		cur.execute("INSERT INTO packets (time, src, dst, mac, len, proto) VALUES (%s, %s, %s, %s, %s, %s)", (packet.sniff_time, src, dst, mac, packet.length, proto))
		
	#commit the new records and close db connection
	conn.commit()
	cur.close()
	conn.close()

def QueuedCommit(packet):
	#commit packets to the database in COMMIT_INTERVAL second intervals

	now = datetime.datetime.now()
	global timestamp
	global queue

	#first packet in new queue
	if timestamp == 0:
		timestamp = now
	
	queue.append(packet)
	
	#time to commit to db
	if (now - timestamp).total_seconds() > COMMIT_INTERVAL:
		DatabaseInsert(queue)
		queue = []
		timestamp = 0

#configure capture object
capture = pyshark.LiveCapture(interface='wlp58s0')#, only_summaries=True)
capture.set_debug()

#start capturing
capture.apply_on_packets(QueuedCommit) #, timeout=30)
capture.close();
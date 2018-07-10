#! /usr/bin/python3

import pyshark
import datetime
import psycopg2
import threading
import sys, os

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "categorisation"))
from burstProcessing import packetBurstification, burstPrediction # pylint: disable=C0413, E0401

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"))
import refineJsonData # pylint: disable=C0413, E0401

#constants
COMMIT_INTERVAL = 5
LOCAL_IP_MASK_16 = "192.168."
LOCAL_IP_MASK_24 = "10."

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
			src = packet['ip'].src
			dst = packet['ip'].dst
		except KeyError:
			src = 0
			dst = 0

		try:
			srcLocal = LOCAL_IP_MASK_16 in src or LOCAL_IP_MASK_24 in src
			dstLocal = LOCAL_IP_MASK_16 in dst or LOCAL_IP_MASK_24 in dst
		except:
			srcLocal = False
			dstLocal = False

		if dstLocal and not srcLocal:
			mac = packet['eth'].dst
		else:
			mac = packet['eth'].src

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

def Categorise():
	packetBurstification()
	burstPrediction()

def RefineData():
	refineJsonData.compileUsageImpacts()

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
		t = threading.Thread(target=Categorise)
		t = threading.Thread(target=RefineData)
		t.start()
		queue = []
		timestamp = 0

#configure capture object
capture = pyshark.LiveCapture(interface='2')#, only_summaries=True)
capture.set_debug()

#start capturing
capture.apply_on_packets(QueuedCommit) #, timeout=30)
capture.close();

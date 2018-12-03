#! /usr/bin/python3

import pyshark
import datetime
import psycopg2
import re

#constants
COMMIT_INTERVAL = 5

#initialise vars
timestamp = 0 
queue = []

def DatabaseInsert(packets):
    global timestamp
    local_ip_mask = re.compile('^(192\.168|10\.|255\.255\.255\.255).*') #so we can filter for local ip addresses

    #open db connection
    conn = psycopg2.connect("dbname=testdb user=postgres password=password")
    cur = conn.cursor()
    counter = 0
    
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
            src = ''
            dst = ''

        srcLocal = local_ip_mask.match(src)
        dstLocal = local_ip_mask.match(dst)
        
        if (not dstLocal and not srcLocal) or (dstLocal and srcLocal):
            continue #internal packet that we don't care about, or no local host (should never happen)
        elif not dstLocal:
            mac = packet['eth'].src
        else:
            mac = packet['eth'].dst

        if len(packet.highest_layer) > 10:
            proto = packet.highest_layer[:10]
        else:
            proto = packet.highest_layer

        #insert packets into table
        cur.execute("INSERT INTO packets (time, src, dst, mac, len, proto) VALUES (%s, %s, %s, %s, %s, %s)", (packet.sniff_time, src, dst, mac, packet.length, proto))
        counter += 1
        
    #commit the new records and close db connection
    conn.commit()
    cur.close()
    conn.close()
    print("Captured " + str(counter) + " packets this tick")

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
capture = pyshark.LiveCapture(interface='1')
capture.set_debug()

#start capturing
capture.apply_on_packets(QueuedCommit) #, timeout=30)
capture.close();

#! /usr/bin/env python3

import pyshark, datetime, psycopg2, re, argparse, sys, traceback

#constants
COMMIT_INTERVAL = 5
DEBUG = False

#initialise vars
timestamp = 0 
queue = []

def DatabaseInsert(packets):
    global timestamp
    print("packets ", len(packets))
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
        except KeyError as ke:
            src = ''
            dst = ''
            print("error", ke)
            # print(packet)
            continue

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
        try:
            cur.execute("INSERT INTO packets (time, src, dst, mac, len, proto) VALUES (%s, %s, %s, %s, %s, %s)", (packet.sniff_time, src, dst, mac, packet.length, proto))
        except:
            print("Unexpected error on insert:", sys.exc_info())
            traceback.print_exc()
            sys.exit(-1)  
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

def log(*args):
    if DEBUG:
        print(*args)
        

if __name__=='__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--interface', dest="interface", type=str, help="Interface to listen to")
    parser.add_argument('--cinterval', dest="cinterval", type=int, help="Commit interval in seconds", default=5)
    parser.add_argument('--debug', dest='debug', action='store_true')
    args = parser.parse_args()

    DEBUG = args.debug

    if args.interface is None:
        print(parser.print_help())
        sys.exit(-1)

    log("Configuring capture on ", args.interface)
    
    if args.cinterval is not None:
        COMMIT_INTERVAL = args.cinterval
        log("Setting commit interval as ", COMMIT_INTERVAL)

    capture = pyshark.LiveCapture(interface=args.interface)

    if DEBUG:
        capture.set_debug()

    log("Starting capture")

    capture.apply_on_packets(QueuedCommit) #, timeout=30)
    capture.close();

    

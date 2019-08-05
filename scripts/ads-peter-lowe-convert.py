#! /usr/bin/env python3

import argparse
import configparser
import dns.resolver
import json
import os
import random
import requests
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime
import tldextract
import urllib
import ipaddress

IOTR_BASE = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
LIST_PATH = os.path.join(IOTR_BASE, "support", "peter-lowes-blocklist.txt")
OUT_PATH = os.path.join(IOTR_BASE, "ui", "src", "assets", "data", "peter-ads.json")

print("Loading from ", LIST_PATH, ' dumping to ', OUT_PATH)
lines = open(LIST_PATH, 'r').readlines()
print("got ", len(lines), ' hosts')

res = dns.resolver.Resolver()
res.nameservers = ['8.8.8.8', '8.8.4.4']

iptohost = {}

for l in lines:
    print(l)
    if l[0] == '#': 
        continue
    try:
        hostname = l.split(' ')[1].strip()
        print(" domain ", hostname, " -- ")
        dns_ans = res.query(hostname)
        iptohost[hostname] = [str(x) for x in dns_ans]
        print(iptohost[hostname], type(iptohost[hostname]))
    except:
        print("Exception ", sys.exc_info()[0])

tojson = json.dumps(iptohost)
outfile = open(OUT_PATH, 'w')
outfile.write(tojson)
outfile.close()

    

# data = json.loads(text);
# domains = [d for d in data.keys()]


# resolved = {}

# for domain in domains:    
#     try:
#         dns_ans = res.query(domain)
#         ips = str([str(x) for x in dns_ans])
#         print(" domain ", domain, " -- ", str(dns_ans[0]), len(dns_ans))
#         resolved[domain] = ips
#         # raw_domain = str(dns_ans[0])
#     except:
#         # print("Exception ", sys.exc_info[0])
#         print(" failure for ", domain)
#         resolved[domain] = []
#         pass

# tojson = json.dumps(resolved)
# outfile = open(sys.argv[2], 'w')
# outfile.write(tojson)
# outfile.close()

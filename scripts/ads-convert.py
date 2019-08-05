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

filename = sys.argv[1];
print("Loading from ", filename, ' dumping to ', sys.argv[2]);
text = open(filename, 'r').read()
data = json.loads(text);
domains = [d for d in data.keys()]

res = dns.resolver.Resolver()
res.nameservers = ['8.8.8.8', '8.8.4.4']

resolved = {}

for domain in domains:    
    try:
        dns_ans = res.query(domain)
        ips = str([str(x) for x in dns_ans])
        print(" domain ", domain, " -- ", str(dns_ans[0]), len(dns_ans))
        resolved[domain] = ips
        # raw_domain = str(dns_ans[0])
    except:
        # print("Exception ", sys.exc_info[0])
        print(" failure for ", domain)
        resolved[domain] = []
        pass

tojson = json.dumps(resolved)
outfile = open(sys.argv[2], 'w')
outfile.write(tojson)
outfile.close()

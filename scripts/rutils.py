import re
import ipaddress

def is_multicast(ip):
    address = ipaddress.ip_address(ip)
    return address.is_multicast

def is_private(ip):
    address = ipaddress.ip_address(ip)
    return address.is_private


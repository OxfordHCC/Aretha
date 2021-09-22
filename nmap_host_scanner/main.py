import os
import sys
import subprocess
import xml.etree.ElementTree as xml_et
from collections import namedtuple

PROCFS_ROUTE_GATEWAY_FLAG = 0x0002

Either = namedtuple("Either", ["left", "right"])

def eitherify(func):
    def wrapper(*args, **kwargs):
        args_list = list(args)
        for (i, arg) in enumerate(args_list):
            if type(arg) is Either:
                if(arg.left != None):
                    return Either(arg.left, None)
                args_list[i] = arg.right

        # cast returned tuple to Either just in case
        # functions can then return (err, res) instead of Either(err, res)
        err, res = func(*tuple(args_list), **kwargs)
        return Either(err, res)
    return wrapper
    

@eitherify
def get_interface():
    interface = os.environ.get("ARETHA_INTERFACE")
    if(interface is None):
        return "Interface not specified...", None
    return None, interface

def chunk(str_input, n):
    return [str_input[i:i+n] for i in range(0, len(str_input), n)]

def hex_addr_to_str(hex_addr):
    hex_chunks = chunk(hex_addr, 2)
    dec_chunks = [str(int(hex_chunk, 16)) for hex_chunk in hex_chunks]
    reversed_chunks = list(reversed(dec_chunks))
    string_address = ".".join(reversed_chunks)
    return string_address

def parse_routes(procfs_route):
    def parse_row(row):
        row_arr = row.split('\t')
        row_dict = {
            "interface": row_arr[0],
            "destination": row_arr[1],
            "gateway": row_arr[2],
            "flags": row_arr[3],
            "mask": row_arr[7]
        }
        return row_dict
    
    route_rows = procfs_route.split("\n")
    return [parse_row(row) for row in route_rows[1:]]

@eitherify
def get_subnet(interface):
    def is_gateway(route):
        hex_flag = int(route['flags'], 16)
        return hex_flag & PROCFS_ROUTE_GATEWAY_FLAG == PROCFS_ROUTE_GATEWAY_FLAG
        
    if interface is None:
        return ("Invalid interface specified", None)

    cat_procfs = subprocess.run(['cat', '/proc/net/route'], capture_output=True)
    if cat_procfs.returncode != 0:
        return cat_procfs.stderr.decode('UTF-8'), None
    
    procfs_net_route = cat_procfs.stdout.decode("UTF-8").strip()
    routes = parse_routes(procfs_net_route)
    interface_routes = [route for route in routes if route['interface'] == interface]
    non_gateway = [route for route in interface_routes if not is_gateway(route)]
    return None, non_gateway[0]

@eitherify
def nmap_host_discovery(subnet):
    if subnet is None:
        return ("Invalid target", None)

    subnet_ip = hex_addr_to_str(subnet['destination'])
     #TODO this should be read from subnet['mask'] but anything more than 255 and it takes a looong time
    subnet_mask = 24
    target = f"{subnet_ip}/{subnet_mask}"
    nmap = subprocess.run(['nmap', '-oX', '-', '-sn', target], capture_output=True)
    if nmap.returncode != 0:
        return (nmap.stderr.decode("UTF-8"), None)
    
    return None, nmap.stdout.decode("UTF-8")

@eitherify
def parse_nmap(nmap_stdout):
    def parse_host_node(node):
        addrs = node.findall('address')
        addrs_by_type = {}
        for addr in addrs:
            addrs_by_type[addr.get('addrtype')] = addr.get('addr')
        return addrs_by_type

    nmaprun = xml_et.fromstring(nmap_stdout)
    hosts = nmaprun.findall('host')
    return (None, [parse_host_node(host_node) for host_node in hosts])

def append_err(prev, curr):
    if curr is None:
        return prev

    if prev is None:
        return curr

    return prev + curr

def main():
    err, new_hosts = parse_nmap(
        nmap_host_discovery(
            get_subnet(
                get_interface())))
    
    if err != None:
        print(err)
        return 1

    print(new_hosts)
    return 0
    
if __name__ == "__main__":
    sys.exit(main())
    

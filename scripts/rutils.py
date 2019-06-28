
import re

def make_localip_mask(override=None):

    if not override:
        initial_mask = re.compile('^(192\.168|10\.|255\.255\.255\.255).*') #so we can filter for local ip addresses
    else :
        pattern = '^(192\.168|10\.|255\.255\.255\.255|%s).*' % override.replace('.','\.')
        initial_mask = re.compile(pattern) #so we can filter for local ip addresses

    lip = get_local_ip()

    if lip is not None and initial_mask.match(lip[0]) is None:
        print("Fail on initial mask, so adding local interface", lip[0])
        initial_mask = re.compile('^(192\.168|10\.|255\.255\.255\.255|%s).*' % lip[0].replace('.','\.'))

    return initial_mask    

def is_multicast_v4(ipv4):
    splits = ipv4 and ipv4.split('.')
    # print(' checking ', ipv4, ', ismulti? ', splits and int(splits[0]) >= 224 and int(splits[0]) <= 239)
    return splits and int(splits[0]) >= 224 and int(splits[0]) <= 239

def get_local_ip():
    import socket
    x = None
    try:
        x =  [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")] 
    except : 
        pass
    y = [[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]
    return x or y

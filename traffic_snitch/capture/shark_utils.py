import ipaddress
from datetime import datetime, timezone


def is_packet_of_interest(packet):
    # non ip packet blast away
    if 'ip' not in packet:
        return False

    src, dst = packet.ip.src, packet.ip.dst

    # skip multicasts
    if ipaddress.ip_address(src).is_multicast:
        return False
    if ipaddress.ip_address(dst).is_multicast:
        return False

    # skip broadcast eth packets
    if packet['eth'].src == 'ff:ff:ff:ff:ff:ff':
        return False
    if packet['eth'].dst == 'ff:ff:ff:ff:ff:ff':
        return False

    # check locality
    src_is_local = ipaddress.ip_address(src).is_private
    dst_is_local = ipaddress.ip_address(dst).is_private

    # internal packet that we don't care about, or no internal ip
    # (should never happen)
    if src_is_local == dst_is_local:
        return False

    # if all tests passed, it's of interest
    return True


def get_local_tuple(packet):
    src, dst = packet.ip.src, packet.ip.dst
    is_src_local = ipaddress.ip_address(src).is_private
    is_dst_local = ipaddress.ip_address(dst).is_private

    if(is_src_local == is_dst_local):
        raise Exception("No external party in packet.")

    return is_src_local, is_dst_local


def get_internal_mac(packet):
    is_src_local, is_dst_local = get_local_tuple(packet)
    eth_layer = packet['eth']
    
    if is_src_local:
        return eth_layer.src

    return eth_layer.dst

def get_external_ip(packet):
    is_src_local, is_dst_local = get_local_tuple(packet)
    ip_layer = packet['ip']

    if is_src_local:
        return ip_layer.dst

    return ip_layer.src


def fix_sniff_tz(sniff_dt):
    # pyshark doesn't return an aware datetime, so we misinterpret
    # things to being non local what we need to do is figure out what
    # timezone we captured in
    local_tz = datetime.utcnow().astimezone().tzinfo

    # then we need to create a new datetime with the actual
    # timezone... cast back into UTC.
    return datetime.combine(
        sniff_dt.date(),
        sniff_dt.time(),
        local_tz
    ).astimezone(timezone.utc)

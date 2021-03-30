import sys
from loop import iptables_firewall

# check if current platform is linux...
def is_linux():
    return sys.platform.startswith('linux')

# TODO implement bsd/macos firewall controller using pf.conf
PLATFORMS = {
    "linux": {
        "description": "linux firewall via iptables",
        "firewall": iptables_firewall,
        "check": is_linux
    }
}

def init():
    for platform in PLATFORMS.values():
        if platform['check']() is True:
            return platform['firewall']

firewall = init()

# can we just import firewall directly?
def get_firewall():
    return firewall

import subprocess
import urllib
import time
from peewee import fn
from config import config

# command constants
CONNECT = 'CN'
REBOOT = 'RB'
RESET = 'RS'

# we wrap this in a function because we can only access config after
# the config file has been read, which only happens after parsing the
# arguments inside the main function. So we want to defer config
# reading until after that. The global statements of this module are
# executed before that.

# TODO replace config accessors with parameters passed from main fn
def get_beacon_handler(Transmissions, Geodata, Rules):
    try:
        CONFIG_ID = config['general']['id']
    except:
        raise Exception("ERROR: CONFIG id must be set under [general]")

    try:
        cfg_beacon = config['beacon']
        URL = cfg_beacon['url']
        ENDPOINT = cfg_beacon['endpoint']
        KEY = cfg_beacon['key']
        SSH = cfg_beacon['ssh']
        INTERVAL = int(cfg_beacon.get('interval', 3600))
    except KeyError as e:
        raise Exception("Missing or incomplete [beacon] config")

    def run_command(command):
        if command == CONNECT:
            print("open ssh connection")
            return subprocess.run(["ssh", "-i", "~/.ssh/aretha.pem",
                                   "-fTN",
                                   "-R", f"2500:localhost:22",
                                   f"{SSH}"],
                                  timeout=3600,
                                  check=True)

        if command == REBOOT:
            print("reboot machine")
            return subprocess.run(["shutdown", "-r", "now"],
                                  timeout=120,
                                  check=True)

        # TODO this will only work on linux...
        if command == RESET:
            print("reset aretha service")
            return subprocess.run(["systemctl", "restart", "iotrefine"],
                                  timeout=300,
                                  check=True)

    # connect to c&c server
    def beacon(last_beacon = float(0)):
        if time.time() - last_beacon < INTERVAL:
            return

        [(packet_count)] = Transmissions.select(fn.COUNT(Transmissions.id)).tuples()
        [(geodata_count)] = Geodata.select(fn.COUNT(Transmissions.id)).tuples()
        [(rules_count)] = Rules.select(fn.COUNT(Transmissions.id)).tuples()

        post_data = urllib.parse.urlencode({
            'i': CONFIG_ID,
            'k': KEY,
            'p': packet_count,
            'g': geodata_count,
            'f': rules_count
        }).encode('ascii')

        try:
            res = urllib.request.urlopen(
                url=f"https://{URL}:{ENDPOINT}",
                data=post_data)
            
            charset = res.headers.get_content_charset()
            command =  res.read().decode(charset)
            last_beacon = time.time()
            run_command(command)
        except subprocess.SubprocessError:
            print("Error running command")
        except urllib.error.URLError as e:
            print("Error contacting beacon server...")
            print(e.reason)
        except:
            print(f"Unknown beacon exception.")
            
        # return from beacon    
        return last_beacon

    # return from get_beacon_handler
    return beacon

import argparse
import sys
from config import config
from project_variables import CONFIG_PATH
from loop import startLoop
from logger import getArethaLogger
from models import init_models

# We use a separate main function so we can point to it using a
# setuptools setup.py entrypoint declaration
# 
# Note that main's "args=None" declaration may be needed according to
# some poorly written, but popular blog post about setuptools
def main(args=None):
    log = getArethaLogger("loop")
    
    # loop will call c&c server
    is_beacon = False

    # time between loop executions
    interval = None

    # give random names to discovered, unnamed devices
    autogen_device_names = False

    # service to use for geo-related queries
    geoapi_provider = "ip-api"

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config',
        dest="config",
        type=str,
        default=CONFIG_PATH,
        help="Path to config file, default is %s " % CONFIG_PATH)
    
    parser.add_argument(
        '--interval',
        dest="interval",
        type=float,
        help="Specify loop interval in sec (can be fractions)")
    
    parser.add_argument(
        '--debug',
        dest='debug',
        action="store_true",
        help='Turn debug output on (Default off)')
    
    args = parser.parse_args()

    log.info("Loading config from .... %s " % args.config)

    config.read(args.config)
    
    loop_cfg = config['loop'] or {}

    if "autogen-device-names" in loop_cfg:
        autogen_device_names = loop_cfg.getboolean('autogen-device-names')

    if "beacon" in loop_cfg:
        is_beacon = loop_cfg.getboolean('beacon')
        
    if "interval" in loop_cfg:
        interval = loop_cfg.getfloat('interval')

    # (interval) argument overwrites config value
    if args.interval is not None:
        interval = args.interval

    if interval is None:
        log.error("No interval value passed in config or arguments.")
        parser.print_help()
        return 1
    
    # will throw KeyError if doesn't exist TODO print more helpful
    # message explaining what's missing from config
    geoapi_provider = config['geoapi']['provider']

    log.enable_debugging(args.debug)
    models = init_models(config=config['postgresql'])

    startLoop(models, interval, is_beacon, autogen_device_names, geoapi_provider, log)

    # exit with code 0
    return 0

if __name__ == '__main__':
    sys.exit(main())

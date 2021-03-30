#! /usr/bin/env python3
import sys
import logging
import argparse
from collections import namedtuple

from configparser import ConfigParser
from . import startCapture
from project_variables import CONFIG_PATH
from config import config
from models import init_models

def main(args=None):
    parser = argparse.ArgumentParser()
    log = logging.getLogger(__name__)

    parser.add_argument(
        '--config',
        dest="config",
        default=CONFIG_PATH,
        type=str,
        help="Path to config file, default is %s" % CONFIG_PATH)
    
    parser.add_argument(
        '--interface',
        dest="interface",
        type=str,
        help="Interface to listen to")
    
    parser.add_argument(
        '--interval',
        dest="interval",
        type=int,
        help="Commit interval in seconds")
    
    parser.add_argument(
        '--resolution',
        dest="resolution",
        type=int,
        help="Commit resolution in seconds")
    
    parser.add_argument(
        '--debug',
        dest='debug',
        action='store_true')
    
    args = parser.parse_args()

    log.info("Loading config from {config_path}")
    config.read(args.config)

    # default values
    interface = None
    commit_interval_secs = 30
    resolution_secs = 5

    # resolve interface value
    if "capture" in config and "interface" in config['capture']:
        interface = config['capture']['interface']

    if args.interface is not None:
        interface = args.interface

    if interface is None:
        log.error("Cannot find interface in config or argument.")
        sys.exit(1)
        
    # resolve commit interval value
    if "capture" in config and "interval" in config['capture']:  
        commit_interval_secs = int(config['capture']['interval'])

    if args.interval is not None:
        commit_interval_secs = args.interval

        
    # resolve commit resolution value
    if "capture" in config and "resolution" in config['capture']:
        resolution_secs = int(config['capture']['resolution'])

    if args.resolution is not None:
        resolution_secs = args.resolution

    # open long-running database connection and returns peewee
    # abstractions (Models)
    models = init_models(config=config['postgresql'])

    startCapture(models, interface, commit_interval_secs, resolution_secs, args.debug)

    # will probably never reach...
    # TODO handle sigint gracefully (will require packet capture on separate thread)
    return 0
    
if __name__ == '__main__':
    sys.exit(main())
    

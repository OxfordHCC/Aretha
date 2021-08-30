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


capture_default_configuration = {
    "interface": None,
    "interval": 30,
    "resolution": 5,
}

# order of precdence: args > environ > config > defaults
def read_configuration(config_name, env_name, args={}, env={}, config={}, defaults={}, default=None):

    if(config_name in args):
        return args[config_name]

    if(env_name in env):
        return env[config_name]

    if(config_name in config):
        return config[config_name]

    if(config_name in default):
        return defaults[config_name]
    
    return default

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

    dict_args = vars(args)
    capture_config = config.get('capture', None)
    postgres_config = config.get('postgresql', None)

    def read_conf(name, env_name, sub_config):
        return read_configuration(
            name=name,
            env_name=env_name,
            args=dict_args,
            environ=os.environ,
            config=sub_config,
            defaults=capture_default_configuration
        )

    # read capture config
    interface = read_conf("interface", "ARETHA_CAPTURE_INTERFACE", capture_config)
    interval = read_conf("interval", "ARETHA_CAPTURE_INTERVAL", capture_config)
    resolution = read_conf("resolution", "ARETHA_CAPTURE_RESOLUTION", capture_config)

    # read db config
    db_name = read_conf("name", "ARETHA_DB_NAME", postgres_config)
    db_host = read_conf("host", "ARETHA_DB_HOST", postgres_config)
    db_user = read_conf("user", "ARETHA_DB_USER", postgres_config)
    db_pass = read_conf("pass", "ARETHA_DB_PASS", postgres_config)
    db_port = read_conf("port", "ARETHA_DB_PORT", postgres_config)

    if interface is None:
        log.error("Cannot find interface in config or argument.")
        sys.exit(1)
        
    # open long-running database connection and returns peewee
    # abstractions (Models)
    models = init_models(database=db_name,
                         username=db_user,
                         password=db_pass,
                         host=db_host,
                         port=db_port)
    Transmissions = models['transmissions']
    Exposures = models['exposures']
    
    startCapture(interface, interval, resolution, Transmissions, Exposures, args.debug)

    # will probably never reach...
    # TODO handle sigint gracefully (will require packet capture on separate thread)
    return 0
    
if __name__ == '__main__':
    sys.exit(main())
    

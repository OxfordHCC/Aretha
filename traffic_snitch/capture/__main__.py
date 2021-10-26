#! /usr/bin/env python3
import sys
import logging
import argparse
from collections import namedtuple

from capture import log
from capture.capture import startCapture
from util.project_variables import CONFIG_PATH
from util.config import parse_params
from models import init_models

capture_default_configuration = {
    "interface": None,
    "interval": 30,
    "resolution": 5,
}

parameters = [
    {
        "name": "config_path",
        "arg_name": '--config',
        "default": CONFIG_PATH,
        "help": "Path to config file"
    },
    {
        "name":"interface",
        "cfg_path": "capture/interface",
        "type": str,
        "help": "Interface to listen to"
    },
    {
        "name":"interval",
        "cfg_path": "capture/interval", 
        "type": int,
        "help": "Commit interval in seconds"
    },
    
    {
        "name":"resolution",
        "type": int,
        "cfg_path": "capture/resolution",
        "help": "Commit resolution in seconds"
    },
    {
        "name":"debug",
        "type": bool,
        "action": 'store_true'},
    {
        "name": 'db-name',
        "env_name": "ARETHA_DB_NAME",
        "cfg_path": "postgresql/name",
    },
    {
        "name":'db-host',
        "env_name": "ARETHA_DB_HOST",
        "cfg_path": "postgresql/host"
    },
    {
        "name":'db-port',
        "env_name": "ARETHA_DB_PORT",
        "type": int,
        "cfg_path": "postgresql/port"
    },
    {
        "name": "db-user",
        "env_name": "ARETHA_DB_USER",
        "cfg_path": "postgresql/user"
    },
    {
        "name": "db-pass",
        "env_name": "ARETHA_DB_PASS",
        "cfg_path": "postgresql/pass"
    }
]

def main(args=None):
    params = parse_params(parameters)

    # general config
    debug = params['debug']
    log.enable_debugging(debug)
    
    # read capture config
    interface = params['interface']
    interval = params['interval']
    resolution = params['resolution']

    # db params
    db_name = params['db-name']
    db_host = params['db-host']
    db_port = params['db-port']
    db_user = params['db-user']
    db_pass = params['db-pass']

    log.debug(params)

    # TODO add "required" parameter to parameter dict and handle in parse_params function
    if interface is None:
        log.error("Cannot find interface in config or argument.")
        return 1
        
    # open long-running database connection and returns peewee
    # abstractions (Models)
    models = init_models(database=db_name,
                         username=db_user,
                         password=db_pass,
                         host=db_host,
                         port=db_port)
    Transmissions = models['transmissions']
    Exposures = models['exposures']
    
    startCapture(interface, interval, resolution, Transmissions, Exposures, debug)

    # will probably never reach...
    # TODO handle sigint gracefully (will require packet capture on separate thread)
    return 0
    
if __name__ == '__main__':
    sys.exit(main())
    

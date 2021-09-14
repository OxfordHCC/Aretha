import argparse
import sys
from loop import log
from loop.loop import startLoop
from models import init_models
from util.config import parse_params
from util.project_variables import CONFIG_PATH
from loop.trackers import init_trackers

parameters = [
    {
        "name": "config_path",
        "arg_name": "--config",
        "default": CONFIG_PATH,
        "help": "Path to config file"
    },
    {
        "name": "interval",
        "type": float,
        "help": "Specify loop interval in sec (can be fractions)",
        "cfg_path": "loop/interval"
    },
    {
        "name": "debug",
        "action": "store_true",
        "env_name": "ARETHA_DEBUG",
        "type": bool,
        "cfg_path": "general/debug"
    },
    {
        "name": "geoapi_provider",
        "arg_name": "--geoapi",
        "default": "ip-api",
        "cfg_path": "geoapi/provider"
    },
    {
        "name": "beacon",
        "action": "store_true",
        "type": bool,
        "help": "loop will call c&c server",
        "cfg_path": "loop/beacon"
    },
    {
        "name": "autogen_device_names",
        "type": bool,
        "action": "store_true",
        "help": "give random names to discovered, unnamed devices",
        "cfg_path": "loop/autogen-device-names"
    },
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
    },
    {
        "name": "trackers",
        "cfg_path": "loop/trackers"
    }
]


# We use a separate main function so we can point to it using a
# setuptools setup.py entrypoint declaration.
# 
# Note that main's "args=None" declaration may be needed according to
# some poorly written, but popular blog post about setuptools
def main(args=None):
    params = parse_params(parameters)

    # loop params
    interval = params['interval']
    beacon = params['beacon']
    autogen_device_names = params['autogen_device_names']
    geoapi_provider = params['geoapi_provider']
    trackers_path = params['trackers']

    # general params
    debug = params['debug']

    # db params
    db_name = params['db-name']
    db_user = params['db-user']
    db_pass = params['db-pass']
    db_host = params['db-host']
    db_port = params['db-port']
    
    if interval is None:
        log.error("No interval value passed in config or arguments.")
        parser.print_help()
        return 1
    
    log.enable_debugging(debug)
    log.debug(f"params: {params}")
    
    models = init_models(db_name, db_user, db_pass, db_host, db_port)

    # init trackers
    init_trackers(trackers_path)

    # start loop
    startLoop(models, db_name, db_user, db_pass, db_host, db_port, interval, beacon, autogen_device_names, geoapi_provider)

    # exit with code 0
    return 0

if __name__ == '__main__':
    sys.exit(main())

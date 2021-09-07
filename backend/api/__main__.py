from gunicorn.app.base import BaseApplication

from api import create_app, log
from util.config import parse_params
from util.project_variables import CONFIG_PATH
from models import db, init_models

class StandaloneApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


configuration_options = [
    {
        "name": "config_path",
        "arg_name": '--config',
        "default": CONFIG_PATH,
        "help": "Path to config file"
    },
    {
        "name": "host",
        "env_name": "ARETHA_API_HOST",
        "cfg_path": 'api/host',
        "default": "localhost",
        "type": str,
        "help":"Host for server to bind to",
    },
    {
        "name": "port",
        "env_name": "ARETHA_API_PORT",
        "cfg_path": "api/port",
        "type": int,
        "help": "Port for server to bind to"
    },
    {
        "name": 'timeout',
        "env_name": "ARETHA_API_TIMEOUT",
        "cfg_path": "api/timeout",
        "type": int,
        "help": "Gunicorn worker timeout"
    },
    {
        "name": 'workers',
        "env_name": "ARETHA_API_WORKERS",
        "cfg_path": "api/workers",
        "type": int,
        "help": "Gunicorn worker count"
    },
    {
        "name": 'debug',
        "type": bool,
        "env_name": "ARETHA_DEBUG",
        "cfg_path": "general/debug",
        "action": "store_true"
    },
    {
        "name": "aretha_id",
        "env_name": "ARETHA_ID",
        "cfg_path": "general/id"
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
        "type": int,
        "env_name": "ARETHA_DB_PORT",
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

if __name__ == "__main__":
    params = parse_params(configuration_options)

    # general params
    aretha_id = params['aretha_id']
    debug = params['debug']
    
    # api params
    host = params['host']
    port = params['port']
    timeout = params['timeout']
    workers = params['workers']
    
    # db params
    db_name = params['db-name']
    db_host = params['db-host']
    db_port = params['db-port']
    db_user = params['db-user']
    db_pass = params['db-pass']

    log.enable_debugging(debug)
    log.debug(params)

    models = init_models(db_name, db_user, db_pass, db_host, db_port)
    app = create_app(debug, db, models, aretha_id, log)

    server_options = {
        'bind': f"{host}:{port}",
        'timeout': timeout,
        'workers': workers,
    }
    
    StandaloneApplication(app, server_options).run()


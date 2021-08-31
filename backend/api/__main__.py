import sys
import argparse
from gunicorn.app.base import BaseApplication
from api import create_app
from config import config
from project_variables import CONFIG_PATH
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--config',
        type=str,
        dest="config",
        default=CONFIG_PATH,
        help="Path to config file, default is %s" % CONFIG_PATH)
    
    parser.add_argument(
        '--host',
        dest="host",
        type=str,
        help="Host for server to bind to")
    
    parser.add_argument(
        '--port',
        dest="port",
        type=int,
        help="Port for server to bind to")
    
    parser.add_argument(
        '--timeout',
        dest="timeout",
        type=int,
        help="Gunicorn worker timeout")

    parser.add_argument(
        '--workers',
        dest="workers",
        type=int,
        help="Gunicorn worker count")
    
    parser.add_argument(
        '--debug',
        dest='debug',
        action='store_true')

    args = parser.parse_args()
    config.read(args.config)

    dict_args = var(args)
    api_config = config.get('api', None)
    general_config = config.get('general', None)
    postgres_config = config.get('postgresql', None)

    api_default_cfgs = {
        "debug": False
    }

    def read_conf(name, env_name, cfg):
        return read_configuration(
            name=name,
            env_name=env_name,
            args=dict_args,
            environ=os.environ,
            config=cfg,
            defaults=api_default_cfgs
        )

    host = read_conf("host", "ARETHA_API_HOST", api_config)
    port = read_conf("port", "ARETHA_API_PORT", api_port)
    timeout = read_conf("timeout", "ARETHA_API_TIMEOUT", api_config)
    workers = read_conf("workers", "ARETHA_API_WORKERS", api_config)
    debug = read_conf("debug", "ARETHA_DEBUG", api_config)
    aretha_id= read_conf("id", "ARETHA_ID", dict_args, general_config)

    # read db config
    db_name = read_conf("name", "ARETHA_DB_NAME", postgres_config)
    db_host = read_conf("host", "ARETHA_DB_HOST", postgres_config)
    db_user = read_conf("user", "ARETHA_DB_USER", postgres_config)
    db_pass = read_conf("pass", "ARETHA_DB_PASS", postgres_config)
    db_port = read_conf("port", "ARETHA_DB_PORT", postgres_config)

    models = init_models(config=config['postgresql'])

    app = create_app(debug, db, models, pid)

    server_options = {
        'bind': f"{host}:{port}",
        'timeout': timeout,
        'workers': workers,
    }
    
    StandaloneApplication(app, server_options).run()


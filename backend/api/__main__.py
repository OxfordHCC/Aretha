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
    
    try:
        api_config = config['api']
        host = args.host or api_config['host']
        port = args.port or api_config['port']
        timeout = args.timeout or api_config['timeout']
        workers = args.workers or api_config['workers']
        debug = args.debug or False
    except KeyError as ke:
        tb = sys.exc_info()[2]
        raise Exception("Missing config variables...").with_traceback(tb)

    pid = config['general']['id']
    models = init_models(config=config['postgresql'])

    app = create_app(debug, db, models, pid)

    server_options = {
        'bind': f"{host}:{port}",
        'timeout': timeout,
        'workers': workers,
    }
    
    StandaloneApplication(app, server_options).run()


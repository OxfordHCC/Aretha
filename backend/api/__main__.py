from gunicorn.app.base import BaseApplication
from .api import app

# TODO read from config
host = "127.0.0.1"
port = "4201"
timeout = 4
workers = 2


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
    options = {
        'bind': f"{host}:{port}",
        'timeout': timeout,
        'workers': workers,
    }

    StandaloneApplication(app, options).run()


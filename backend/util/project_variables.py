import os

# TODO move to config

ARETHA_BASE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.sep.join((ARETHA_BASE, 'log'))
CONFIG_PATH = os.path.sep.join((ARETHA_BASE, "config", "config.cfg"))

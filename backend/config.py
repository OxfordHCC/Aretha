from configparser import ConfigParser
from project_variables import CONFIG_PATH

config = ConfigParser()

# testing some patterns...
default_config = ConfigParser()
default_config.read(CONFIG_PATH)

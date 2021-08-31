from configparser import ConfigParser
from project_variables import CONFIG_PATH

config = ConfigParser()

# testing some patterns...
default_config = ConfigParser()
default_config.read(CONFIG_PATH)

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

import os
import argparse

from configparser import ConfigParser
from util.project_variables import CONFIG_PATH
from util.fp import first

config = ConfigParser()

# testing some patterns...
default_config = ConfigParser()
default_config.read(CONFIG_PATH)


def add_argument(option, parser):
    return parser.add_argument(
        option.get("arg_name", f"--{option['name']}"),
        default=option.get('default', None),
        dest=option['name'],
        action=option.get('action', "store"),
        help=option.get('help', "")
    )

def parse_sub_cfg(conf_arr, config=None, i=0):
    if i >= (len(conf_arr)):
        return config

    conf_name = conf_arr[i]

    try:
        sub_config = config[conf_name]
        return parse_sub_cfg(conf_arr, sub_config, i+1)
    except:
        return None
        
def parse_cfg(conf_path, config):
    path_arr = conf_path.split('/')
    return parse_sub_cfg(path_arr, config)

def read_cfg(option, cfg):
    if "cfg_path" not in option:
        return None
    
    cfg_path = option['cfg_path']

    return parse_cfg(cfg_path, cfg)

def read_arg(option, args):
    if 'arg_name' not in option:
        return None
        
    arg_name = option.get('name', None)
    if arg_name not in args:
        return None

    return args[arg_name]

def read_env(option, env):
    if 'env_name' not in option:
        return None

    env_name = option['env_name']
    if env_name not in env:
        return None

    return env[env_name]

def parse_param(option, args, env, cfg):
    val = first(
        read_arg(option, args),
        read_env(option, env),
        read_cfg(option, cfg)
    )

    param_type = option.get('type', str)
    return param_type(val)

def parse_params(options, args=None, env=os.environ):
    parser = argparse.ArgumentParser()
    for option in options:
        add_argument(option, parser)
    parsed_args = parser.parse_args(args)
    dict_args = vars(parsed_args)
    config_path = dict_args['config_path']
    config.read(config_path)

    param_keys = [option['name'] for option in options]
    param_values = [parse_param(option, dict_args, env, config) for option in options]
    return dict(zip(param_keys, param_values))

    
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

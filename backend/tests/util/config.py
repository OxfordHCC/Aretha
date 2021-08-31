import sys

from util.config import parse_cfg, parse_params
from util.project_variables import CONFIG_PATH

test_dict = {
    "c_int": 1,
    "b": {
        "b_int": 1,
        "b_str": "test",
    },
    "a": {
        "ab": {
            "abc": {
                "abc_int": 42,
                "abcd": {
                    "abcd_int": 13,
                    "abcd_str": "some string"
                }
            }
        }
    }
}

configuration_options = [
    {
        "name": "config_path",
        "arg_name": '--config',
        "default": CONFIG_PATH,
        "type": str,
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

def test_parse_cfg():
    assert parse_cfg("b/b_int", test_dict) == 1
    assert parse_cfg("a/ab/abc/abcd/abcd_str", test_dict) == "some string"
    assert parse_cfg("c_int", test_dict) == 1

def test_parse_cfg_missing():
    assert parse_cfg("b/c", test_dict) == None
    assert parse_cfg("c/a/b", test_dict) == None
    assert parse_cfg("d", test_dict) == None

def test_parse_params():
    params = parse_params(configuration_options, sys.argv[2:])
    assert params['host'] is not None
    return

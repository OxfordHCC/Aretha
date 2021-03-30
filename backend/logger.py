import logging
import os
from collections import namedtuple

from project_variables import LOG_PATH

# TODO rename file to log_util
# TODO rename to snake_case
def getArethaLogger(module_name, stdout_logs=True, fs_logs=False, debug=False):        
    logger = logging.getLogger(module_name);

    log_level = logging.INFO
    if debug is True:
        log_level = logging.DEBUG

        
    logger.setLevel(log_level)
    
    log_format = "%(asctime)s {}::%(levelname)s %(message)s".format(module_name)
    formatter = logging.Formatter(log_format)

    if(stdout_logs):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    if(fs_logs):
        fs_path = os.path.join(LOG_PATH, "%s.log" % module_name)
        file_handler = logging.FileHandler(fs_path)
        file_handler.setFormatter(formatter);
        logger.addHandler(file_handler)

    def enable_debugging(flag=True):
        if flag is False:
            return logger.setLevel(logging.INFO)
        return logger.setLevel(logging.DEBUG)
        
    # TODO: do we use warn for anything?
    res = namedtuple(f"ArethaLogger", [
        'name',
        'warn',
        'error',
        'info',
        'debug',
        'enable_debugging'
    ])
    
    res.name = module_name
    res.error = logger.error
    res.warn = logger.warn
    res.info = logger.info
    res.debug = logger.debug
    res.enable_debugging = enable_debugging
    
    return res



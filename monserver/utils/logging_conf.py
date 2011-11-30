import logging
import logging.config
import os.path

logging_conf = 'logging.conf'

path_prefix = os.path.dirname(os.path.abspath(__file__)) + os.path.sep

logging.config.fileConfig(path_prefix + logging_conf)


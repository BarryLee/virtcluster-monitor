import logging
import logging.config
import os.path

from utils import current_dir

log_confs = {
        #'default'   :   'logging.conf',
        'server'    :   'logging.conf.server',
        #'models'    :   'logging.conf.models',
        'event'     :   'logging.conf.event',
        }
path_prefix = current_dir(__file__) + os.path.sep
#logging.config.fileConfig(current_dir(__file__) + os.path.sep + 'logging.conf')

def get_logger(name):
    prefix = name.split('.',1)[0]
    conf = log_confs.get(prefix)
    if conf:
        logging.config.fileConfig(path_prefix + conf)

    return logging.getLogger(name)

if __name__ == '__main__':
    logger = logging.getLogger('this')
    count = 7
    while count:
        logger.error('asasfasaddsasfdvxcwergfgerterwf')
        count -= 1

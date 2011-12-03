import os
import re
import time
import logging

from monserver.utils.load_config import load_config 

logger = logging.getLogger('monserver.RRD.cleanup')

config = load_config()
rrdroot = config.get('RRD_root')

def rmrrds(hid):
    path = rrdroot + os.path.sep + hid
    logger.info('removing %s' % path)
    if os.system('rm -r %s' % path):
        logger.error('failed to remove rrds of %s' % hid)


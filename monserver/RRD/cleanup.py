import os
import re
import time
import logging
import logging.handlers

import cloud
from mon_config_manager import global_config

logger = logging.getLogger('cleanuprrds')
logger.setLevel(logging.DEBUG)
LOG = '/tmp/cleanuprrds.log'
fileHandler = logging.handlers.RotatingFileHandler(LOG, maxBytes=2*2**20, \
                                                   backupCount=2)
simpleFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(simpleFormatter)
logger.addHandler(fileHandler)

config = global_config
CYCLETIME = 1800
RETRYTIME = 60
timeout = CYCLETIME
tobermd = []

def set_timeout(t):
    global timeout
    timeout = t

def cleanup():
    set_timeout(CYCLETIME)
    try:
        suc, vmsinfo = cloud.get_vms_info()
    except:
        logger.exception('')
        set_timeout(RETRYTIME)
        return
    if not suc:
        logger.error('call cloud.get_vms_info failed')
        set_timeout(RETRYTIME)
        return
    ids = []
    for vminfo in vmsinfo:
        ids.append(vminfo['guid'])
    print ids
    logger.debug('currently running vms: %s' %(ids,))
    try:
        rrdroot = config.get('db')['root_dir']
    except KeyError, e:
        logger.exception('config error')
        set_timeout(RETRYTIME)
        return
    except TypeError, e:
        logger.exception('read config failed')
        set_timeout(RETRYTIME)
        return
    os.chdir(rrdroot)
    dirs = os.listdir('.')
    dirs.sort()
    print dirs
    logger.debug('in rrd dir: %s' % (dirs,))
        
    for i in dirs:
        if i not in ids and re.search('^\d+$', i):
            if i not in tobermd:
                print 'mark %s as to be removed' % i
                logger.debug('mark %s as to be removed' % i)
                tobermd.append(i)
                print tobermd
            else:
                print 'remove %s' % i
                logger.debug('remove %s' % i)
                if not os.system('rm -r %s' % i):
                    tobermd.remove(i)
                    print tobermd
                else:
                    logger.error('failed to remove rrds of %s' % i)
                    set_timeout(RETRYTIME)

def test_main_process():
    return not os.system('ps ax|grep mon_center|grep -v grep')

def main():
    while test_main_process():
        cleanup()
        time.sleep(timeout)

if __name__ == '__main__':
    main()
    #cleanup()

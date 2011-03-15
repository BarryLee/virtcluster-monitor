import os
import sys
import threading

###############################################################
# temporary solution for importing upper level modules/packages
_ = lambda f: os.path.dirname(os.path.abspath(f))

par_dir = _(_(__file__))
if par_dir not in sys.path:
    sys.path.append(par_dir)
###############################################################

from includes.singletonmixin import Singleton, SingletonException
from rrdtool_wrapper import *
from utils.get_logger import get_logger
from models.interface import host_metric_conf


logger = get_logger('RRD.RRDHandler')


class RRDHandlerException(Exception):
    pass


class RRDHandler(Singleton):

    _lock = threading.RLock()

    def __init__(self, root_dir):
        self._root_dir = str(root_dir)
        self._temp = {}


    def suffix(self, metric_name):
        return metric_name + '.rrd'


    def pathScheme(self, host_id, metric_name):
        return os.sep.join([self._root_dir, host_id]), self.suffix(metric_name)


    def cd(self, path):
        try:
            os.chdir(path)
        except OSError, e:
            if e.errno == 2:
                os.makedirs(path)
                os.chdir(path)
            else:
                raise e


    def write(self, host_id, metric_name, val):
        #print "writing to db...%s:%s:%s" % (host_id, metric_name, val)

        dir_path, rrd_db = self.pathScheme(host_id, metric_name)
        self._lock.acquire()
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
            except OSError, e:
                #if e.errno != 17:  # if not because file already exists
                raise e
        self._lock.release()

        #rrd_db = dir_path + os.sep + rrd_db
        self.cd(dir_path)
        try:
            if not os.path.exists(rrd_db):
                self.rrdCreate(host_id, metric_name, rrd_db)
        
            ret = self.rrdGroupUpdata(rrd_db, val)

        except rrdtool.error, e:
            logger.exception('%s, %s, %s' % (host_id, metric_name, val))
            raise RRDHandlerException, str(e)


    def read(self, host_id, metric_name, cf='AVERAGE', resolution=5, start=None, end=None):
        # Read monitor data
        # The most recent data will be retrived if there is 
        # no time specified
        resolution = int(resolution)
        host_rrd_dir, rrd_db = self.pathScheme(host_id, metric_name)
        if not os.path.exists(host_rrd_dir):
            logger.error('cannot find data of host %s' % host_id)
            raise RRDHandlerException, 'host %s is not monitored' % host_id
        if not os.path.exists(rrd_db):
            raise RRDHandlerException, 'metric %s not found' % metric_name
        try:
            if start is None:
                #val = self.rrd_fetch_latest(rrd_db, cf, resolution)
                ret = rrdfetchlatest(rrd_db, cf, resolution)
            else:
                #val = self.rrd_fetch(rrd_db, cf, resolution, start, end)
                ret = rrdfetch_wrapper(rrd_db, cf, resolution, start, end)
        except rrdtool.error, e:
            logger.exception('%s, %s, %s, %s, %s' % (rrd_db, cf, resolution, start, end))
            raise RRDHandlerException, str(e)

        return ret


    def getMetricConf(self, host_id):
        try:
            return self._temp[host_id]
        except KeyError, e:
            metric_conf = host_metric_conf(host_id)
            self._temp[host_id] = metric_conf
            return metric_conf


    def rrdCreate(self, host_id, metric_name, rrd_db):
        metric_conf = self.getMetricConf(host_id)

        found = self.getMetricMetricgrp(metric_name, metric_conf)

        if found is None:
            raise RRDHandlerException, "metric %s not found" % name
        else:
            metric_group = found[0]
            metric = found[1]
            from time import time
            start = str(int(time()) - 60)
            step = metric_group['period']
            heartbeat = step * 2
            #ds_type = (metric['type'] == 'continuous') and \
                    #"COUNTER" or "GAUGE"
            ds_type = 'GAUGE'
            max = metric.has_key('max') and str(metric["max"]) or "U"
            min = metric.has_key('min') and str(metric["min"]) or "U"
            xff = 0.5
            ttl = 3600 * 24
            cf_time = metric_group['consolidation_intervals']
            DSs = [[name, ds_type, heartbeat, min, max]]
            RRAs = []
            RRAs.append(['AVERAGE', xff, 1, ttl/step])
            for cf in ('AVERAGE', 'MIN', 'MAX'):
                for i in cf_time:
                    RRAs.append([cf, xff, i/step, ttl/i])

            rrdcreate_wrapper(rrd_db, start=-24*3600, step=step, DSs=DSs, RRAs=RRAs)


    def rrdGroupUpdata(self, rrd_db, vals):
        if type(vals) is list:
            for val in vals:
                timestamp = int(val[0])
                val = str(val[1])
                rrdupdate_wrapper(rrd_db, timestamp, val)
        else:
            timestamp = int(val[0])
            val = str(val[1])
            rrdupdate_wrapper(rrd_db, timestamp, val)
        return ret


    def getMetricMetricgrp(self, metric_name, metric_conf):
        found = None
        metric_groups = metric_conf['metric_groups']
        for metric_group in metric_groups:
            for metric in metric_group['metrics']:
                if metric['name'] == name:
                    found = (metric_group, metric)
                    break

        return found


def getInstance(rrdRoot):
    try:
        ins = MonDBHandler.getInstance(rrdRoot)
        return ins
    except SingletonException, e:
        #logger.exception('')
        ins = MonDBHandler.getInstance()
        return ins


if __name__=="__main__":
    t = RRDHandler.getInstance("/tmp/rrds")
    print t.read("127.0.0.1", "load_one", resolution=5, end="1278057380", start="1278057320")
    print t.read("127.0.0.1", "load_one", resolution=5)

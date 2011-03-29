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
from models.Interface import host_metric_conf


logger = get_logger("RRD.RRDHandler")


class RRDHandlerException(Exception):
    pass


class RRDHandler(Singleton):

    _lock = threading.RLock()

    def __init__(self, root_dir, buffer_size=0):
        assert type(root_dir) is str
        assert type(buffer_size) is int
        self._root_dir = root_dir
        self._temp = {}


    def suffix(self, prefix, metric_name):
        if len(prefix):
            prefix += "-"
        return prefix + metric_name + ".rrd"


    def pathScheme(self, host_id, prefix, metric_name):
        return os.sep.join([self._root_dir, host_id]), self.suffix(prefix, metric_name)


    def cd(self, path):
        try:
            os.chdir(path)
        except OSError, e:
            if e.errno == 2:
                os.makedirs(path)
                os.chdir(path)
            else:
                raise e


    #def onDataArrival(self, host_obj, data):
    def onDataArrival(self, host_id, data):
        #host_id = host_obj.id
        prefix = data.has_key("prefix") and data["prefix"] or ""
        timestamp = data["timestamp"]
        #metric_conf = host_obj.metric_list
        for metric_name, metric_val in data["val"].items():
            dir, rrd = self.pathScheme(host_id, prefix, metric_name)
            rrd = dir + os.path.sep + rrd
            try:
                rrdtool.update(rrd, "%d:%s"%(timestamp,metric_val))
            except rrdtool.error, e:
                if "No such file" in e.args[0]:
                    self._lock.acquire()
                    if not os.path.exists(dir):
                        try:
                            os.makedirs(dir)
                        except OSError, e:
                            #if e.errno != 17:  # if not because file already exists
                            raise e
                    self._lock.release()
                    
                    self.create(host_id, prefix, metric_name, rrd)
                else:
                    logger.exception("%s, %s, %s" % 
                                     (host_id, metric_name, metric_val))
                    raise RRDHandlerException, str(e)
        

    def read(self, host_id, metric_name, cf="AVERAGE", resolution=5, start=None, end=None):
        # Read monitor data
        # The most recent data will be retrived if neither start
        # nor end is given
        #logger.debug('start is %s, end is %s' % (start, end))
        resolution = int(resolution)
        host_rrd_dir, rrd_db = self.pathScheme(host_id, "", metric_name)
        if not os.path.exists(host_rrd_dir):
            logger.error("cannot find data of host %s" % host_id)
            raise RRDHandlerException, "host %s is not monitored" % host_id
        rrd_db = host_rrd_dir + os.path.sep + rrd_db
        if not os.path.exists(rrd_db):
            raise RRDHandlerException, "metric file %s not found" % rrd_db
        try:
            if start is None:
                #val = self.rrd_fetch_latest(rrd_db, cf, resolution)
                ret = rrdfetchlatest(rrd_db, cf, resolution)
            else:
                #val = self.rrd_fetch(rrd_db, cf, resolution, start, end)
                ret = rrdfetch_wrapper(rrd_db, cf, resolution, start, end)
        except rrdtool.error, e:
            logger.exception("%s, %s, %s, %s, %s" % (rrd_db, cf, resolution, start, end))
            raise RRDHandlerException, str(e)

        return ret


    def _getMetricConf(self, host_id):
        try:
            return self._temp[host_id]
        except KeyError, e:
            metric_conf = host_metric_conf(host_id)
            self._temp[host_id] = metric_conf
            return metric_conf


    def _getMetricMetricgrp(self, prefix, metric_name, metric_conf):
        found = None
        #metric_groups = metric_conf["metric_groups"]
        metric_groups = metric_conf
        for metric_group in metric_groups:
            if prefix != "":
                if not (metric_group.has_key("instances") and 
                        reduce(lambda x,y: x+y,
                               (i["device"]==prefix \
                                for i in metric_group["instances"]))):
                    continue
            for metric in metric_group["metrics"]:
                if metric["name"] == metric_name:
                    found = (metric_group, metric)
                    break

        return found


    #def create(self, host_id, metric_name, rrd_db):
    def create(self, host_id, prefix, metric_name, rrd_db):
        metric_conf = self._getMetricConf(host_id)

        #found = self._getMetricMetricgrp(metric_name, metric_conf)
        found = self._getMetricMetricgrp(prefix, metric_name, metric_conf)

        if found is None:
            errmsg = "metric %s" % metric_name
            if prefix != "":
                errmsg += " of %s" % prefix
            errmsg += " not found"
            raise RRDHandlerException, errmsg
        else:
            metric_group = found[0]
            metric = found[1]
            from time import time
            start = str(int(time()) - 60)
            step = metric_group["period"]
            heartbeat = step * 2
            #ds_type = (metric["type"] == "continuous") and \
                    #"COUNTER" or "GAUGE"
            ds_type = "GAUGE"
            max = metric.has_key("max") and str(metric["max"]) or "U"
            min = metric.has_key("min") and str(metric["min"]) or "U"
            xff = 0.5
            ttl = 3600 * 24
            cf_time = metric_group["consolidation_intervals"]
            DSs = [[metric_name, ds_type, heartbeat, min, max]]
            RRAs = []
            RRAs.append(["AVERAGE", xff, 1, ttl/step])
            for cf in ("AVERAGE", "MIN", "MAX"):
                for i in cf_time:
                    RRAs.append([cf, xff, i/step, ttl/i])

            rrdcreate_wrapper(rrd_db, start=-24*3600, step=step, DSs=DSs, RRAs=RRAs)


    #def rrdGroupUpdata(self, rrd_db, vals):
        #if type(vals) is list:
            #for val in vals:
                #timestamp = int(val[0])
                #val = str(val[1])
                #rrdupdate_wrapper(rrd_db, timestamp, val)
        #else:
            #timestamp = int(val[0])
            #val = str(val[1])
            #rrdupdate_wrapper(rrd_db, timestamp, val)
        #return ret


def getInstance(rrdRoot):
    try:
        ins = MonDBHandler.getInstance(rrdRoot)
        return ins
    except SingletonException, e:
        #logger.exception("")
        ins = MonDBHandler.getInstance()
        return ins


if __name__=="__main__":
    t = RRDHandler.getInstance("/tmp/rrds")
    print t.read("127.0.0.1", "load_one", resolution=5, end="1278057380", start="1278057320")
    print t.read("127.0.0.1", "load_one", resolution=5)

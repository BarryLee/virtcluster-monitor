import logging
import threading

from monserver.includes.Singleton import MetaSingleton
from Threshold import Threshold, CompositeThreshold
from api.mon import add_threshold, rm_host_threshold

logger = logging.getLogger('threshold')

__all__ = ["ThresholdManagerException", "ThresholdManager"]

class ThresholdManagerException(Exception):
    pass

class ThresholdManager(object):

    __metaclass__ = MetaSingleton
    __lock = threading.RLock()

    def __init__(self):
        self._thresholds = {}
        self.idc = 0

    def setThreshold(self, threshold_specs):
        """set a threshold.
        threshold_specs example:
        { # a list of thresholds on metrics
          'threshold': [      
            # format: (<host_id>, <metric_name>, <threshold_value>, 
            # <threshold_type>[, <win_size>[, <recur>]]), 
            # for threshold_type, 0 refers to upper bound, 
            # 1 refers to lower bound
            { 'host': 'localhost',
              'metric': 'cpu_usage',
              'tval': 80,
              'ttype': 0 },
            { 'host': 'example.com', 
              'metric': 'r/s', 
              'tval: 400, 
              'ttype': 0}
          ],
          'win_size': 60, # window size, in seconds, 
                          # only useful in composite threshold
        }
        """
        try:
            threshold = threshold_specs['threshold']
            assert type(threshold) is list
        except (KeyError, AssertionError), e:
            raise Exception, 'invalid threshold_specs format: %s' % e

        nt = len(threshold)

        if not nt > 0:
            logger.warning('empty threshold specs')
            return

        ts = []
        hosts = []
        tobj = None
        for t in threshold:
            logger.debug(t)
            tobj = Threshold(tid=-1, **t)
            ts.append(tobj)
            hosts.append(t['host'])

        tid = self.getTid()
        if nt > 1:
            tobj = CompositeThreshold(
                                tid=tid,
                                window=threshold_specs['win_size'],
                                thresholds=ts)
        else:
            tobj.tid = tid
            
        self.add(tobj)
        rc, res = add_threshold(hosts, tid)
        if not rc:
            self.rm(tobj)
            raise Exception,\
                    "Can't set threshold for an inactive host: %s" % res

        return tobj

    def unsetThreshold(self, tid):
        tobj = self._thresholds[tid]
        if isinstance(tobj, CompositeThreshold):
            hosts = tobj.hosts
        else:
            hosts = [tobj.host]
        for h in hosts:
            rm_host_threshold(h, tid)
        del self._thresholds[tid]
        
    def getTid(self):
        self.__lock.acquire()
        tid = self.idc
        self.idc += 1
        self.__lock.release()
        return tid

    def add(self, threshold):
        self._thresholds[threshold.tid] = threshold
    
    def rm(self, tid):
        del self._thresholds[tid]

    def get(self, tid):
        try:
            return self._thresholds[tid]
        except KeyError, e:
            raise ThresholdManagerException("threshold %s is not defined" % tid)


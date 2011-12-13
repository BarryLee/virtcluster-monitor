import pdb
import logging
import threading

import ZODB.config
import transaction
from BTrees.LOBTree import LOBTree

from monserver.includes.Singleton import MetaSingleton
from Threshold import Threshold, CompositeThreshold
#from monserver.api.mon import add_threshold, rm_host_threshold
from monserver.api.mon import get_host_state

logger = logging.getLogger('threshold')

__all__ = ["ThresholdManagerException", "ThresholdManager"]

class ThresholdManagerException(Exception):
    pass

class ThresholdManager(object):

    __metaclass__ = MetaSingleton
    __lock = threading.RLock()
    _thresholds = {}

    def __init__(self, dbconfigurl):
        #self._thresholds = {}
        self._db = ZODB.config.databaseFromURL(dbconfigurl)
        self.loadDB()

    def loadDB(self):
        #pdb.set_trace()
        conn = self._db.open()
        root = conn.root()
        if not root.has_key('thresholds'):
            root['thresholds'] = LOBTree()
            transaction.commit()
            conn.close()
            self.idc = 0
            logger.debug('init threshold db')
            return
        thresholds = root['thresholds']
        for tid, tspec in thresholds.iteritems():
            try:
                tobj = self._newThreshold(tid, *self._parseThresholdSpecs(tspec))
                self._thresholds[tid] = tobj
                logger.debug('load threhold %s:%s' % (tid, tspec))
            except ThresholdManagerException:
                logger.warning('load threshold %s:%s failed' % (tid, tspec))
                del thresholds[tid]
                continue
        try:
            self.idc = thresholds.maxKey() + 1
        except ValueError:
            self.idc = 0
        conn.close()

    def _parseThresholdSpecs(self, threshold_specs):
        """
        threshold_specs example:
        { # a list of thresholds on metrics
          'threshold': [      
            # format: (<host_id>, <metric_name>, <threshold_value>, 
            # <threshold_type>[, <win>[, <recur>]]), 
            # for threshold_type, 0 refers to upper bound, 
            # 1 refers to lower bound
            { 'host': 'localhost',
              'metric': 'cpu_usage',
              'tval': 80,
              'ttype': 0,
              'win': 60,
              'recur': 3 },
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
            if not len(threshold) > 0:
                raise ThresholdManagerException('empty threshold specs')
            hosts = [t['host'] for t in threshold]
            win_size = threshold_specs.get('win_size')
            return threshold, hosts, win_size
        except (KeyError, AssertionError), e:
            raise ThresholdManagerException, 'invalid threshold_specs format: %s' % e

    def _newThreshold(self, tid, threshold, hosts, win_size):
        """instansiate a Threshold object.
        """
        ts = []
        tobj = None
        for t in threshold:
            logger.debug(t)
            try:
                tobj = Threshold(tid=-1, **t)
                ts.append(tobj)
            except TypeError, e:
                raise ThresholdManagerException, 'invalid threshold_specs format: %s' % e

        if len(threshold) > 1:
            try:
                tobj = CompositeThreshold(
                                    tid=tid,
                                    window=win_size,
                                    thresholds=ts)
            except TypeError, e:
                raise ThresholdManagerException, 'invalid threshold_specs format: %s' % e
        else:
            tobj.tid = tid
            
        #self.add(tobj)
        #rc, res = add_threshold(hosts, tid)
        #if not rc:
            #self.rm(tobj)
            #raise ThresholdManagerException,\
                    #"Can't set threshold for an inactive host: %s" % res
        self.add(tobj)
                
        return tobj

    def _delThreshold(self, tid):
        #tobj = self.get(tid)
        #if isinstance(tobj, CompositeThreshold):
            #hosts = tobj.hosts
        #else:
            #hosts = [tobj.host]
        #for h in hosts:
            #rm_host_threshold(h, tid)
        #del self._thresholds[tid]
        self.rm(tid)

    def setThreshold(self, threshold_specs):
        tspec, hosts, win_size = self._parseThresholdSpecs(threshold_specs)
        for h in hosts:
            rc, res = get_host_state(h)
            if not rc:
                raise ThresholdManagerException,\
                        "Can't set threshold for an unregistered host: %s" % res
        tid = self.getTid()
        tobj = self._newThreshold(tid, tspec, hosts, win_size)
        conn = self._db.open()        
        root = conn.root()
        root['thresholds'][tid] = threshold_specs
        transaction.commit()
        conn.close()
        return tobj

    def unsetThreshold(self, tid):
        try:
            conn = self._db.open()
            root = conn.root()
            del root['thresholds'][tid]
            transaction.commit()
        except KeyError, e:
            if self._thresholds.has_key(tid):
                logger.warning(
                    'inconsistent between db and in-memory mapping: %s' % tid)
            else:
                conn.close()
                raise ThresholdManagerException(
                        "threshold %s is not defined" % tid)
        try:
            self._delThreshold(tid)
        except ThresholdManagerException, e:
            logger.warning(
                'inconsistent between db and in-memory mapping: %s' % tid)
        finally:
            conn.close()
        
    def getTid(self):
        self.__lock.acquire()
        tid = self.idc
        self.idc += 1
        self.__lock.release()
        return tid

    def add(self, threshold):
        self._thresholds[threshold.tid] = threshold
    
    def rm(self, tid):
        try:
            del self._thresholds[tid]
        except KeyError, e:
            raise ThresholdManagerException(
                    "threshold %s is already removed" % tid)

    @classmethod
    def get(cls, tid):
        try:
            return cls._thresholds[tid]
        except KeyError, e:
            raise ThresholdManagerException(
                    "threshold %s is not set" % tid)


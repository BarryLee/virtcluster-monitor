import pdb
import threading
from time import time

from persistent import Persistent

from monserver.event.Event import Event
from monserver.api.event import send_event

__all__ = ["Threshold", "CompositeThreshold"]

class ThresholdViolation(Event):
    
    def __init__(self, host, tid):
        super(ThresholdViolation, self).__init__(target=host)
        self.tid = tid
        #self.merge_key = tid

    def mergable(self, evt):
        #pdb.set_trace()
        return self.tid == evt.tid

class Threshold(object):

    def __init__(self, tid, host, metric, tval, ttype=0, 
            win=0, recur=1 ,callback=None):
        self.tid = tid
        self.host = host
        self.metric = metric
        self.tval = tval
        self.ttype = ttype
        self.win = win
        self.recur = recur
        self._recurs = 0
        self._win_in = 0
        # 0 refers to upper bound, 1 refers to lower bound
        if ttype == 0:
            self.test = lambda x: x > self.tval
        elif ttype == 1:
            self.test = lambda x: x < self.tval

        self.callback = callback
        self.etype = 'ThresholdViolation'

    def produceEvent(self, v):
        return ThresholdViolation(self.host, self.tid)       

    def __call__(self, evt):
        ret = 0
        if evt.metric == self.metric:
            if self.test(evt.val):
                now = time()
                if now - self._win_in > self.win: 
                    self._recurs = 1
                    self._win_in = now
                else:
                    self._recurs += 1
                if self._recurs >= self.recur:
                    ret = 1
                    send_event(self.produceEvent(evt.val))
                    if self.callback:
                        self.callback(evt)
        return ret

    def info(self):
        return {
                "tid": self.tid,
                "host": self.host,
                "metric": self.metric,
                "tval": self.tval,
                "ttype": self.ttype,
                "win": self.win,
                "recur": self.recur
               }

class CompositeThreshold(object):

    #_lock = threading.RLock()

    def __init__(self, window, thresholds=[], callback=None):
        self.thresholds = thresholds
        self.hosts = set([t.host for t in thresholds])
        self.alerts = [0 for i in thresholds]
        self.test = lambda : reduce(lambda x,y: x*y, self.alerts)
        self.win = window
        self.etype = 'ThresholdViolation'
        self.last = 0

    #def addThreshold(self, t):
        #self.thresholds.append(t)
        #self.alerts.append(0)

    def produceEvent(self):
        return Event(self.etype)

    def __call__(self, evt):
        ret = 0
        try:
            #self._lock.acquire()
            t = time()
            if t-self.last > self.win:
                for i,j in enumerate(self.alerts):
                    self.alerts[i] = 0

            for i,threshold in enumerate(self.thresholds):
                if evt.metric == threshold.metric and\
                   threshold.test(evt.val):
                    self.last = t
                    self.alerts[i] = 1

            if self.test(self.alerts):
                ret = 1
                send_event(self.produceEvent())
                if self.callback:
                    self.callback(evt)
        finally:
            #self._lock.release()
            return ret

if __name__ == '__main__':
    t = ThresholdViolation('lo', 1)
    print isinstance(t, Event)

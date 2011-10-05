
import threading
from time import time

from monserver.event.Event import Event

class Threshold(object):

    def __init__(self, conn, host, metric, ttype, tval, callback=None):
        self.conn = conn
        self.host = host
        self.metric = metric
        self.threshold = tval
        if ttype == 'gt':
            self.matcher = lambda x: x > self.threshold
        elif ttype == 'lt':
            self.matcher = lambda x: x < self.threshold

        self.callback = callback
        self.etype = 'ThresholdViolation'

    def composeEvent(self, v):
        return Event(self.etype, entity=self.host, metric=self.metric,\
                    threshold=self.threshold, val=v)
        
    def __call__(self, evt):
        ret = 0
        if evt.metric == self.metric:
            if self.matcher(evt.val):
                ret = 1
                self.conn.sendEvent(self.composeEvent(evt.val))
                if self.callback:
                    self.callback(evt)
        return ret

class CompositeThreshold(object):

    _lock = threading.RLock()

    def __init__(self, conn, window, thresholds=[], callback=None):
        self.conn = conn
        self.thresholds = thresholds
        self.alerts = [0 for i in thresholds]
        self.matcher = lambda : reduce(lambda x,y: x*y, self.alerts)
        self.win = window
        self.etype = 'ThresholdViolation'
        self.last = 0

    def addThreshold(self, t):
        self.thresholds.append(t)
        self.alerts.append(0)

    def composeEvent(self):
        return Event(self.etype)

    def __call__(self, evt):
        ret = 0
        try:
            self._lock.acquire()
            t = time()
            if t-self.last > self.win:
                self.alerts = [0] * len(self.thresholds)

            for i,threshold in enumerate(self.thresholds):
                if evt.metric == threshold.metric and\
                   threshold.matcher(evt.val):
                    self.last = t
                    self.alerts[i] = 1

            if self.matcher(self.alerts):
                ret = 1
                self.conn.sendEvent(self.composeEvent())
                if self.callback:
                    self.callback(evt)
        finally:
            self._lock.release()
            return ret

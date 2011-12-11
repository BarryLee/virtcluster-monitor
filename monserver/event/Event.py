import pdb
import json
from time import time

from persistent import Persistent

class EventException(Exception): pass

class Event(Persistent):

    __win = 600

    def __init__(self, target, etype=None, occur_t=None, **econtent):
        self.eventType = etype or self.__class__.__name__
        self.target = target
        self.occurTime = occur_t if occur_t else int(time())
        #self.detectTime = self.occurTime
        self.recurs = 0
        self.merge_key = ''

        self.__dict__.update(econtent)

    def __str__(self):
        return dumps(self)

    def getWinSize(self):
        return self.__win

    def mergable(self, evt):
        #return True
        #pdb.set_trace()
        return self.merge_key == evt.merge_key

    def merge(self, evt):
        #if not hasattr(self, 'recurs'):
            #self.recurs = []
        #self.recurs.append(evt.occurTime)
        self.recurs += 1
        self.occurTime = evt.occurTime

    def info(self):
        return self.__dict__

def loads(event_dump):
    try:
        edict = json.loads(event_dump)
        evt_type = edict.pop('eventType')
        occur_time = edict.pop('occurTime')
        return Event(etype=evt_type, occur_t=occur_time, **edict)
    except Exception, e:
        raise EventException

def dumps(event_obj):
    try:
        return json.dumps(event_obj.__dict__)
    except Exception, e:
        raise EventException


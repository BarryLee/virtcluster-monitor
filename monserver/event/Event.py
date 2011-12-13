import pdb
import json
from time import time

from persistent import Persistent

__all__ = ['EventException', 'Event', 'dumps', 'loads']

class EventException(Exception): pass

class Event(Persistent):

    __win = 600

    def __init__(self, target, eventType=None, occurTime=None, **econtent):
        self.eventType = eventType or self.__class__.__name__
        self.target = target
        self.occurTime = occurTime if occurTime else int(time())
        #self.detectTime = self.occurTime
        self.recurs = 0
        #self.merge_key = ''
        self.unread = True

        self.__dict__.update(econtent)

    def __str__(self):
        return dumps(self)

    def getWinSize(self):
        return self.__win

    def mergable(self, evt):
        return True
        #pdb.set_trace()
        #return self.merge_key == evt.merge_key

    def merge(self, evt):
        #if not hasattr(self, 'recurs'):
            #self.recurs = []
        #self.recurs.append(evt.occurTime)
        self.recurs += 1
        self.occurTime = evt.occurTime
        self.unread = True

    def info(self):
        return self.__dict__

    def msg(self):
        return self.__str__()

def loads(event_dump):
    try:
        edict = json.loads(event_dump)
        evt_type = edict.pop('eventType')
        occurTime = edict.pop('occurTime')
        return Event(eventType=evt_type, occurTime=occurTime, **edict)
    except Exception, e:
        raise EventException

def dumps(event_obj):
    try:
        return json.dumps(event_obj.__dict__)
    except Exception, e:
        raise EventException


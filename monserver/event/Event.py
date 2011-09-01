import json
from time import time

class error(Exception): pass

class Event(object):

    def __init__(self, etype, occur_t=None, **econtent):
        self.eventType = etype
        self.occurTime = occur_t if occur_t else time()

        self.__dict__.update(econtent)

    def __str__(self):
        return dumps(self)

def loads(event_dump):
    try:
        edict = json.loads(event_dump)
        evt_type = edict.pop('eventType')
        occur_time = edict.pop('occurTime')
        return Event(etype=evt_type, occur_t=occur_time, **edict)
    except Exception, e:
        raise error

def dumps(event_obj):
    try:
        return json.dumps(event_obj.__dict__)
    except Exception, e:
        raise error


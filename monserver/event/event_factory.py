import pdb
import json
import os
import logging

from Event import *
from monserver.utils.utils import current_dir

__all__ = ['make_event']

logger = logging.getLogger('event.event_factory')

event_defs = current_dir(__file__) + os.path.sep + 'event_defs'

# import event defs
edefs = json.load(open(event_defs))

event_classes = {}

for edefgrp in edefs:
    mod = edefgrp['module']
    classes = __import__(mod, globals(), locals(), edefgrp['class'])
    for cls in edefgrp['class']:
        the_class = getattr(classes, cls)
        event_classes[cls] = the_class
        logger.debug('import class %s:%s' % (cls, the_class))

def make_event(event_dump):
    try:
        evt_dict = json.loads(event_dump)
        evt_type = evt_dict.pop('eventType')
        evt_cls = event_classes.get(evt_type, Event)
        if evt_cls is Event:
            evt_dict['eventType'] = evt_type
        #pdb.set_trace()
        return evt_cls(**evt_dict)
    except ValueError, e:
        logger.exception('invalid event dump format')
        return None
    except TypeError, e:
        logger.exception('error on class %s with args %s' % (evt_cls, evt_dict))
        return None


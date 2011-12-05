import xmlrpclib
#import itertools
import logging

import ZODB.config
from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree

import Event
from monserver.models.ModelDB import ModelDBException as EventDBException, ModelDB, ModelDBSession
from monserver.api import get_host_state

logger = logging.getLogger('event.EventDB')

class EventDB(ModelDB):

    def open(self):
        self._db = ZODB.config.databaseFromURL(self._config_url)
        self._opened = 1

    def openSession(self):
        return EventDBSession(self)

class EventDBSession(ModelDBSession):
    
    def save(self, event):
        assert isinstance(event, Event.Event)
        target = getattr(event, 'target')
        if target is None:
            logger.warning('event with no target %s' % event.eventType)
            return 

        #rc, state = get_host_state(target)
        #if not rc:
            #raise EventDBException("unknown target: %s" % target, 1)
        if not self.root.has_key(target):
            self.root[target] = OOBTree()
    
        etype = event.eventType
        if not self.root[target].has_key(etype):
            self.root[target][etype] = IOBTree()

        last_evt = self.probe(target, etype, event.occurTime - event.getWinSize())

        if last_evt is None:
            self.root[target][etype][event.occurTime] = event
        else:
            last_evt = self.merge(last_evt, event)
            self.root[target][etype][last_evt.occurTime] = last_evt

    def load(self, selector):
        target = selector.get('target')
        etype = selector.get('etype')
        from_t = selector.get('from')
        to_t = selector.get('to')
        _filter = selector.get('filter')
        if _filter is None:
            _filter = lambda x: True
        #_chain = itertools.chain.from_iterable
        try:
            if target is None and etype is None:
                res = (e for target_elems in self.root.itervalues()
                            for etype_elems in target_elems.itervalues()
                            for e in etype_elems.itervalues(from_t, to_t))
            elif etype is None:
                res = (e for etype_elems in self.root[target].itervalues()
                            for e in etype_elems.itervalues(from_t, to_t))
            elif target is None:
                res = (e for target_elems in self.root.itervalues() if target_elems.has_key(etype)
                            for e in target_elems[etype].itervalues(from_t, to_t))
            else:
                res = self.root[target][etype].itervalues(from_t, to_t)

            return [e for e in res if _filter(e)]
        except KeyError, e:
            raise EventDBException(str(e), 1)
    
    def probe(self, target, etype, max_t):
        try:
            k = self.root[target][etype].minKey(max_t)
            return self.root[target][etype].pop(k)
        except ValueError, e:
            return None
        except KeyError, e:
            return None

    def merge(self, evt1, evt2):
        logger.debug('recured')
        if not hasattr(evt1, 'recurs'):
            evt1.recurs = []
        evt1.recurs.append(evt2.occurTime)
        evt1.occurTime = evt2.occurTime
        return evt1

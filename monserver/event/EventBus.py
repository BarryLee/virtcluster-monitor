import pdb
import logging
import threading
import time
import Queue
from SocketServer import StreamRequestHandler, ThreadingTCPServer

#from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
from ThreadingXMLRPCServer import ThreadingXMLRPCServer

from monserver.includes.Singleton import MetaSingleton
from monserver.utils.utils import threadinglize
#from monserver.utils.get_logger import get_logger
import Event

__all__ = ['EventBus', 'subscribe', 'on_event_arrival']

logger = logging.getLogger("event.EventBus")
#logger = get_logger("event.EventBus")

class _Server(ThreadingTCPServer):
    pass

class _RequestHandler(StreamRequestHandler):

    def handle(self):
        req = ''
        try:
            req = self.rfile.readline().strip()
            #print req
            #evt = self.parse(req)
            evt = Event.loads(req)
            on_event_arrival(evt)
            self.wfile.write(0)
        except Event.EventException:
            logger.exception("Invalid event format")
            self.wfile.write(1)

    #def parse(self, req_data):
        #return Event.loads(req_data)

class EventBus(object):

    __metaclass__ = MetaSingleton

    _ALL = '*'

    def __init__(self, event_server_addr, service_server_addr, 
                 EventServerClass=_Server, 
                 RequestHandlerClass=_RequestHandler,
                 ServiceServerClass=ThreadingXMLRPCServer):
        self._event_server_addr = event_server_addr
        self._service_server_addr = service_server_addr
        self._queue = Queue.Queue()
        self._eventServer = EventServerClass(event_server_addr, RequestHandlerClass)
        self._serviceServer = ServiceServerClass(service_server_addr)
        self._subscribers = {}
        self._RUNNING = 0
        #self.__inited = True

    def startAll(self):
        logger.info("starting event bus...")
        self._RUNNING = 1
        #print self.__dict__
        threadinglize(self.startEventServer)()
        threadinglize(self.dispatch)()
        self.startServiceServer()

    def halt(self):
        self.cleanup()

    def handleSubscribe(self, etype, subscriber, target=None, match=None):
        self._subscribers.setdefault(etype, {})
        target = str(target) if target is not None else self._ALL
        subscribers = self._subscribers[etype].setdefault(target, set())
        assert callable(subscriber)
        #if name is None: name = subscriber.__name__
        if match:
            setattr(subscriber, '__match__', match)
        subscribers.add(subscriber)
        logger.debug("%s subscribes events %s on %s" % (\
                        subscriber, etype, target))

    def handleUnsubscribe(self, etype, subscriber, target=None):
        try:
            target = str(target) if target is not None else self._ALL
            self._subscribers[etype][target].remove(subscriber)
            logger.debug("%s unsubscribes events %s on %s" % (\
                            subscriber, etype, target))
        except KeyError, e:
            logger.exception()

    def startEventServer(self):
        logger.info("Starting event server on %s:%s" % self._event_server_addr)
        self._eventServer.serve_forever()

    def shutdownEventServer(self):
        self._eventServer.shutdown()
        self._eventServer.server_close()

    def startServiceServer(self):
        logger.info("Starting serice server on %s:%s" % self._service_server_addr)
        #self._serviceServer.register_function(self.handleSubscribe)
        #self._serviceServer.register_function(self.handleUnsubscribe)
        self._serviceServer.register_introspection_functions()
        self._serviceServer.serve_forever()

    def shutdownServiceServer(self):
        self._serviceServer.shutdown()
        self._serviceServer.server_close()

    def registerService(self, func, funcName=None):
        #def wrap(func):
            #ebus = self
            #def wrapped(*args, **kwargs):
                #func(*args, **kwargs)

            #wrapped.__name__ = func.__name__
            #return wrapped
        #self._serviceServer.register_function(wrap(func))
        self._serviceServer.register_function(func, funcName)

    def onEventArrival(self, evt):
        self._queue.put(evt)

    def _notifyAll(self, evt, subscribers):
        for s in subscribers:
            try:
                if hasattr(s, '__match__'):
                    if s.__match__(evt):
                        s(evt)
                else:
                    s(evt)
            except Exception, e:
                logger.exception('')
                print e
                continue

    def route(self, evt):
        #print 'route'
        #print evt.eventType
        #print self._subscribers
        etype = evt.eventType
        if not self._subscribers.has_key(etype):
            #logger.debug('unsubscribed event type: %s' % etype)
            return
        if self._subscribers[etype].has_key(self._ALL):
            self._notifyAll(evt, self._subscribers[etype][self._ALL])

        target = str(getattr(evt, 'target'))        
        if target is not None:
            if not self._subscribers[etype].has_key(target):
                #pdb.set_trace()
                #logger.debug('unsubscribed target %s for event %s' % \
                        #(target, etype))
                return
            self._notifyAll(evt, self._subscribers[etype][target])

    def dispatch(self):
        #logger.info("Starting dispatcher")
        while self._RUNNING:
            try:
                evt = self._queue.get(True, 1)
                self.route(evt)
            except Queue.Empty, e:
                continue

    def cleanup(self):
        self._RUNNING = False
        self.shutdownEventServer()
        self.shutdownServiceServer()
        ct = threading.current_thread()
        for t in threading.enumerate():
            if t != ct:
                t.join()

def subscribe(etype, subscriber, target=None, match=None):
    EventBus().handleSubscribe(etype, subscriber, target, match)

def on_event_arrival(evt):
    EventBus().onEventArrival(evt)

def run(event_server_addr, service_server_addr):
    EventBus(event_server_addr, service_server_addr).startAll()

if __name__ == '__main__':
    ip = '0.0.0.0'
    port = 20062
    port2 = 20063

    ebus = EventBus((ip, port), (ip, port2))
    def consumer1(evt):
        print 'c1: %s' % evt.eventType

    def consumer2(evt):
        print 'c2: %s:%s:%s:%s' % (evt.occurTime, evt.target, evt.metric, evt.val)

    subscribe('PerfDataArrival', consumer1, target='xxx')
    subscribe('PerfDataArrival', consumer2, target='localhost')
    #subscribe('RedAlarm', consumer1)
    #subscribe('RedAlarm', consumer2)
    #subscribe('AlienInvade', consumer1)
    print ebus._subscribers

    #ebus.startEventServer()
    try:
        ebus.startAll()
    except KeyboardInterrupt:
        print 'Bye'
        time.sleep(1)
        ebus.cleanup()


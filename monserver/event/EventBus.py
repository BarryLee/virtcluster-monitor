import logging

from Queue import Queue
from SocketServer import StreamRequestHandler, TCPServer
from multiprocessing import Process,Pool,Value

from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

from monserver.utils.utils import threadinglize
import Event
#import pickle_methods

logger = logging.getLogger("event.EventBus")

class _Server(TCPServer):
#class _Server(ThreadingTCPServer):
    pass

class _RequestHandler(StreamRequestHandler):

    def handle(self):
        req = ''
        try:
            req = self.rfile.readline().strip()
            print req
            evt = self.parse(req)
            EventBus.onEventArrival(evt)
            self.wfile.write(0)
        except Event.error:
            #logger.exception("Invalid event format")
            self.wfile.write(1)

    def parse(self, req_data):
        return Event.loads(req_data)

class EventBus(object):

    _queue = Queue()
    _subscribers = {}
    _RUNNING = Value('i', 0)

    def __init__(self, event_server_addr, manage_server_addr, 
                 EventServerClass=_Server, 
                 RequestHandlerClass=_RequestHandler,):
                 #ManageServerClass=SimpleJSONRPCServer):
        self._event_server_addr = event_server_addr
        self._manage_server_addr = manage_server_addr
        #self._queue = Queue()
        self._eventServer = EventServerClass(event_server_addr, RequestHandlerClass)
        self._manageServer = SimpleJSONRPCServer(manage_server_addr)
        #self._subscribers = {}
        self._workers = Pool()
        #self._RUNNING = Value('i', 0)

    def __call__(self):
        pass

    def startAll(self):
        self._RUNNING.value = 1
        #self._eventServerProcess = Process(target=self.startEventServer, args=())
        #self._dispathProcess = Process(target=self.dispatch, args=())

        #self._eventServerProcess.start()
        #self._dispathProcess.start()

        #self._workers.apply_async(self.startEventServer, args=())
        #self._workers.apply_async(self.dispatch, args=())
        #self.startManageServer()
        print self.__dict__
        threadinglize(self.startEventServer)()
        threadinglize(self.dispatch)()
        from time import sleep
        while True:
            sleep(5)

    def halt(self):
        pass

    @classmethod
    def handleSubscribe(cls, etype, subscriber, entity=None, filter=None):
        cls._subscribers.setdefault(etype, {})
        entity = str(entity)
        cls._subscribers[etype].setdefault(entity, set())
        assert callable(subscriber)
        #if name is None: name = subscriber.__name__
        if filter:
            setattr(subscriber, '__filter__', filter)
        cls._subscribers[etype][entity].add(subscriber)

    @classmethod
    def handleUnsubscribe(cls, etype, subscriber, entity=None):
        try:
            cls._subscribers[etype][str(entity)].remove(subscriber)
        except KeyError, e:
            #logger.exception()
            print e

    def startEventServer(self):
        #logger.info("Starting event server on %s:%s" % self._event_server_addr)
        self._eventServer.serve_forever()

    def startManageServer(self):
        #logger.info("Starting serice server on %s:%s" % self._manage_server_addr)
        self._manageServer.register_function(self.handleSubscribe)
        self._manageServer.register_function(self.handleUnsubscribe)
        self._manageServer.serve_forever()

    @classmethod
    def onEventArrival(cls, evt):
        cls._queue.put(evt)

    def route(self, evt):
        print 'route'
        entity = str(getattr(evt, 'entity', None))
        subscriber_list = self._subscribers[evt.eventType][entity]
        print subscriber_list
        for s in subscriber_list:
            if hasattr(s, '__filter__'):
                if s.__filter__(evt):
                    threadinglize(s)(evt)
                    #s(evt)
            else:
                threadinglize(s)(evt)
                #s(evt)

    def dispatch(self):
        #logger.info("Starting dispatcher")
        while self._RUNNING:
            evt = self._queue.get(True)
            print evt
            #self._workers.apply_async(self.route, (evt,))
            self._workers.apply(route, (evt,self._subscribers))

def route(evt, subscribers):
    print 'route'
    entity = str(getattr(evt, 'entity', None))
    subscriber_list = subscribers[evt.eventType][entity]
    print subscriber_list
    for s in subscriber_list:
        if hasattr(s, '__filter__'):
            if s.__filter__(evt):
                threadinglize(s)(evt)
                #s(evt)
        else:
            threadinglize(s)(evt)

def subscribe(etype, subscriber, entity=None, filter=None):
    EventBus.handleSubscribe(etype, subscriber, entity, filter)

if __name__ == '__main__':
    ip = '0.0.0.0'
    port = 20062
    port2 = 20063

    def consumer1(evt):
        print 'c1: %s' % evt.eventType

    def consumer2(evt):
        print 'c2: %s' % evt.occurTime

    ebus = EventBus((ip, port), (ip, port2))
    subscribe('RedAlarm', consumer1)
    subscribe('RedAlarm', consumer2)
    subscribe('AlienInvade', consumer1)

    #ebus.startEventServer()
    ebus.startAll()


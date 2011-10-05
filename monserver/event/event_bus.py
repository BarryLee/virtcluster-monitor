
import logging
from Queue import Queue
from SocketServer import StreamRequestHandler, ThreadingTCPServer, TCPServer

from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

from monserver.utils.utils import threadinglize
import Event

logger = logging.getLogger('event.event_bus')

__INITED = 0

#class _Server(TCPServer):
class _Server(ThreadingTCPServer):
    pass

class _RequestHandler(StreamRequestHandler):

    def handle(self):
        req = ''
        try:
            req = self.rfile.readline().strip()
            #print req
            evt = self.parse(req)
            on_event_arrival(evt)
            self.wfile.write(0)
        except Event.error:
            logger.exception("Invalid event format")
            self.wfile.write(1)

    def parse(self, req_data):
        return Event.loads(req_data)

def start_event_server(addr):
    s = _Server(addr, _RequestHandler)
    s.serve_forever()

def on_event_arrival(evt):
    global __queue
    __queue.put(evt)
    print __queue

def add_subscriber(etype, subscriber, entity=None, filter=None):
    global __subscribers
    d = __subscribers.setdefault(etype, {})
    entity = str(entity)
    d.setdefault(entity, set())
    assert callable(subscriber)
    if filter:
        setattr(subscriber, '__filter__', filter)
    d[entity].add(subscriber)
    __subscribers[etype] = d

def rm_subscriber(etype, subscriber, entity=None):
    global __subscribers
    try:
        d = __subscribers[etype]
        d[str(entity)].remove(subscriber)
        __subscribers[etype] = d
    except KeyError, e:
        logger.exception()

def route_event(evt):#, subscribers):
    global __subscribers
    print 'route'
    entity = str(getattr(evt, 'entity', None))
    subscriber_list = __subscribers[evt.eventType][entity]
    print subscriber_list
    for s in subscriber_list:
        if hasattr(s, '__filter__'):
            if s.__filter__(evt):
                threadinglize(s)(evt)
                #s(evt)
        else:
            threadinglize(s)(evt)
            #s(evt)

def dispatch():
    global __queue
    #global __subscribers

    while __RUNNING:
        evt = __queue.get(True)
        route_event(evt)
        #threadinglize(route_event)(evt)

def init():
    global __queue
    global __subscribers
    global __RUNNING
    global __INITED

    if __INITED:
        logger.error('There can only be one')
        return

    __queue = Queue()
    __subscribers = {}
    __RUNNING = 0
    __INITED = 1

def run(addr1, addr2):
    global __RUNNING

    __RUNNING = 1
    threadinglize(start_event_server)(addr1)
    threadinglize(dispatch)()

    from time import sleep
    while True:
        sleep(5)

if __name__ == '__main__':
    ip = '0.0.0.0'
    port = 20062
    port2 = 20063

    def consumer1(evt):
        print 'c1: %s' % evt.eventType

    def consumer2(evt):
        print 'c2: %s' % evt.occurTime

    init()

    add_subscriber('RedAlarm', consumer1)
    add_subscriber('RedAlarm', consumer2)
    add_subscriber('AlienInvade', consumer1)

    #ebus.startEventServer()
    run((ip, port), (ip, port2))

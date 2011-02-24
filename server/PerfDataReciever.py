"""data_reciever.py -- the UDPServer that recieves the monitor
data
"""

from SocketServer import ThreadingUDPServer, BaseRequestHandler
import time

from utils.get_logger import get_logger
#from monitor.center.utils.session import getidbyip, set_session
#from monitor.center.utils.scheduler_info_broker import getvmidbyip

logger = get_logger('PerfDataReciever')

class DRRequestHandler(BaseRequestHandler):

    def __init__(self, request, client_address, server, queue=None):
        #self.queue = queue
        BaseRequestHandler.__init__(self, request, client_address, server)

    def handle(self):
        logger.debug("recieved 1 msg from %s:%d" % \
                    (self.client_address[0], self.client_address[1]))
        print self.request
        #data = [self.request[0], self.client_address]
        #print data
        #try:
            #data = self.mangle(data)
        #except KeyError, e:
            #logger.debug('recieved msg from unsigned host %s' % self.request[0])
            #return
        #logger.debug('msg from %s:%d - %s' % (data[1][0], data[1][1], data[0])) 
        #self.queue.put(data, True)

    #def mangle(self, data):
        ## convert the host addr to its id
        #ip, port = data[1]
        #try:
            #hostID = getidbyip(ip)
        #except KeyError, e:
            #id = getvmidbyip(ip)
            #if id is None:
                #raise e
            #logger.warning('get msg from unregistered vm %s,\
                           #register it now' % id)
            #set_session(ip, type='vm', id=id)
        #set_session(ip, last_send=time.time())
        #return [data[0], (hostID, port)]

class PerfDataReciever(ThreadingUDPServer):

    def __init__(self, server_address, queue=None,\
                 RequestHandlerClass=DRRequestHandler,\
                 bind_and_activate=True):
        ThreadingUDPServer.__init__(self, server_address, RequestHandlerClass)
        self.queue = queue

    def verify_request(self, request, client_address):
        # TODO check if host is on node list
        return True

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self, self.queue)


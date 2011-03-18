"""data_reciever.py -- the UDPServer that recieves the monitor
data
"""
from SocketServer import BaseRequestHandler, ThreadingUDPServer
import time

from models.interface import getidbyip 
from utils.get_logger import get_logger


logger = get_logger('PerfDateReciever')


class DRRequestHandler(BaseRequestHandler):

    def __init__(self, request, client_address, server, data_store_handler):
        self.data_store_handler = data_store_handler
        BaseRequestHandler.__init__(self, request, client_address, server)


    def handle(self):
        #logger.debug("recieved 1 msg from %s:%d" % \
        #             (self.client_address[0], self.client_address[1]))
        data = self.request[0]
        ip = self.client_address[0]
        try:
            # convert the host addr to its id
            host_id = getidbyip(ip)
        except KeyError, e:
            # TODO 
            #logger.debug('recieved msg from unsigned host %s' % \
                         #(self.client_address,))
            return
        #logger.debug('msg from %s:%d - %s' % (data[1][0], data[1][1], data[0])) 
        #set_session(ip, last_send=time.time())
        self.passOn(host_id, data)


    def passOn(self, host, data):
        msg = decode(data)
        timestamp = msg['timestamp']
        del msg['timestamp']

        for metric_name, val in msg.iteritems():
            try:
                self.data_store_handler.write(host, metric_name, 
                                              '%d:%s' % (timestamp, val))
            except Exception, e:
                raise


class DataReciever(ThreadingUDPServer):

    def __init__(self, server_address, \
                 RequestHandlerClass=DRRequestHandler,\
                 bind_and_activate=True):
        UDPServer.__init__(self, server_address, RequestHandlerClass)


    def verify_request(self, request, client_address):
        # TODO validation
        return True


    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self)



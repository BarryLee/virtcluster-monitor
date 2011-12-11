"""data_reciever.py -- the UDPServer that recieves the monitor
data
"""
from SocketServer import BaseRequestHandler, ThreadingUDPServer
import time
import logging

from models.Interface import Interface
from utils.utils import decode
from api.event import send_event
from event.Event import Event

#logger = get_logger('PerfDateReciever')
logger = logging.getLogger('PerfDateReciever')

class PerfDataArrival(Event):

    def __init__(self, occur_t, host, metric, val):
        super(PerfDataArrival, self).__init__(host, 'PerfDataArrival', occur_t)
        self.metric = metric
        self.val = val
        #self.detectTime = int(time.time()*1e6)

class DRRequestHandler(BaseRequestHandler):

    def __init__(self, request, client_address, server):
        self.data_store_handler = server.data_store_handler
        self.model_int = Interface()
        #self.conn = Connection(server.event_server_address)
        BaseRequestHandler.__init__(self, request, client_address, server)


    def handle(self):
        #logger.debug("recieved 1 msg from %s:%d" % \
        #             (self.client_address[0], self.client_address[1]))
        data = self.request[0]
        ip = self.client_address[0]
        try:
            #logger.debug(list(self.model_int.session.root.get("active", {}).keys()))
            host_obj = self.model_int.getActiveHost(ip)
            host_id = host_obj.id
            host_obj.last_arrival = time.time()
            self.model_int.commit()
            self.model_int.close()
            data = decode(data)
            for evt in self.produceEvent(host_id, data):
                send_event(evt)
            self.data_store_handler.onDataArrival(host_id, data)
        except KeyError, e:
            # TODO 
            #logger.debug('recieved msg from unsigned host %s' % \
                         #(self.client_address,))
            return
        #logger.debug('msg from %s:%d - %s' % (data[1][0], data[1][1], data[0])) 
        #set_session(ip, last_send=time.time())
        #self.passOn(host_id, data)

    def produceEvent(self, host, data):
        t = data['timestamp']
        device = data.get('device','')
        for m,v in data['val'].items():
            yield PerfDataArrival(t, host, self.metricName(device,m), v)
        
    def metricName(self, device, metric):
        if len(device):
            device += '-'
        return device + metric

    #def passOn(self, host, data):
        #msg = decode(data)
        #timestamp = msg['timestamp']
        #del msg['timestamp']

        #for metric_name, val in msg.iteritems():
            #try:
                #self.data_store_handler.write(host, metric_name, 
                                              #'%d:%s' % (timestamp, val))
            #except Exception, e:
                #raise


class DataReciever(ThreadingUDPServer):

    def __init__(self, server_address, data_store_handler, 
                 #event_server_address,
                 RequestHandlerClass=DRRequestHandler,
                 bind_and_activate=True):
        ThreadingUDPServer.__init__(self, server_address, RequestHandlerClass)
        self.data_store_handler = data_store_handler
        #self.event_server_address = event_server_address


    def verify_request(self, request, client_address):
        # TODO validation
        return True


    #def finish_request(self, request, client_address):
        #self.RequestHandlerClass(request, client_address, self, self.data_store_handler)



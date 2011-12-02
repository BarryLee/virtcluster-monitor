import pdb
import os.path
import sys
import threading
import logging
import socket
import xmlrpclib

from time import sleep

from ThreadingXMLRPCServer import ThreadingXMLRPCServer, get_request_data
from PerfDataReciever import DataReciever
from RRD.RRDHandler import RRDHandler
from models.Interface import *
from utils.load_config import load_config
#from utils.get_logger import get_logger
from utils import logging_conf
from utils.utils import *


_ = lambda f: os.path.dirname(os.path.abspath(f))
SERVER_CONFIG_PATH = _(__file__) + os.path.sep + "serverrc"
global_config = load_config(SERVER_CONFIG_PATH)


logger = logging.getLogger("monserver")


class MonServer(object):

    @rpc_formalize()
    def register(self, msg):
        platform_info = decode(msg)
        client_ip = get_request_data().client_address[0]
        hostobj = register(client_ip, platform_info)
        logger.info("%s %s(%s) registered" % (hostobj.rtype, hostobj.id, client_ip))
        return hostobj.id

    def howru(self):
        return 'Fine'
    
    @rpc_formalize()
    def metricList(self, hostID):
        return host_metric_list(hostID)

    @rpc_formalize()
    def hostList(self):
        host_list = map(lambda x: (x[0], x[1].id), 
                        get_active_hosts().items())
        return host_list

    @rpc_formalize()
    def getHostState(self, hostID):
        interface = Interface()
        try:
            hostobj = interface.getHost(hostID)
        except ModelDBException, e:
            interface.close()
            if e.errno == 1:
                return '%s is not registered' % hostID
            else:
                logger.exception('')
                raise
        try:
            interface.getActiveHost(hostobj.ip)
            return "active"
        except ModelDBException, e:
            if e.errno == 1:
                return "inactive"
        finally:
            interface.close()

    @rpc_formalize()
    def getHostInfo(self, hostID):
        interface = Interface()
        try:
            hostobj = interface.getHost(hostID)
            return hostobj.info()
        except ModelDBException, e:
            if e.errno == 1:
                return '%s is not registered' % hostID
            else:
                logger.exception('')
                raise
        finally:
            interface.close()

def bring_up_all_agents():
    interface = Interface()
    try:
        active_hosts = interface.getActiveHosts()
    except ModelDBException, e:
        interface.close()
        if e.errno == 1:
            return
        else: 
            raise

    default_port = global_config.get('agent_port')

    for ip, hostobj in active_hosts.iteritems():
        #pdb.set_trace()
        if hasattr(hostobj, 'port'):
            port = hostobj.port
            #logger.debug(port)
        else:
            port = default_port
        try:
            c = xmlrpclib.ServerProxy('http://%s:%s' % (ip, port))
            c.restart()
        except socket.error, e:
            logger.debug(e)
            continue

    interface.close()

def main():

    local_host = global_config.get("server_ip")
    #local_host = get_ip_address(global_config.get("local_interface")) 

    rpc_port = global_config.get("rpc_port")
    rpc_server = ThreadingXMLRPCServer((local_host, rpc_port),
                                       logRequests=False)
    #rpc_server.register_function(sign_in)
    #rpc_server.register_function(howru)
    rpc_server.register_instance(MonServer())
    threadinglize(rpc_server.serve_forever, "rpc_server")()
    logger.info("start RPC server on %s:%d" % (local_host, rpc_port))

    rrd_root = global_config.get("RRD_root", "/dev/shm")    
    rrd_handler = RRDHandler.getInstance(rrd_root)
    ds_port = global_config.get("ds_port")
    es_port = global_config.get("es_port")
    data_server = DataReciever((local_host, ds_port), rrd_handler,\
                               (local_host, es_port))
    threadinglize(data_server.serve_forever, "data_server")()
    logger.info("start data server on %s:%d" % (local_host, ds_port))

    bring_up_all_agents()

    agent_timeout = global_config.get("agent_timeout")
    check_alive_interval = global_config.get("check_alive_interval")
    scheduled_task(check_alive, "check_alive", True,
                   0, -1, check_alive_interval)(agent_timeout)
    logger.info("check_alive started...")

    while True:
        #myprint(threading.enumerate())
        sleep(60)


def bye():
    logger.info('bye')


if __name__ == "__main__":
    main()

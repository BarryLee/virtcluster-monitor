
import os.path
import sys
import threading

from time import sleep

from ThreadingXMLRPCServer import ThreadingXMLRPCServer, get_request_data
from PerfDataReciever import DataReciever
from RRD.RRDHandler import RRDHandler
from models.Interface import sign_in_handler
from utils.load_config import load_config
from utils.get_logger import get_logger
from utils.utils import encode, decode, get_ip_address, threadinglize, _print


_ = lambda f: os.path.dirname(os.path.abspath(f))
SERVER_CONFIG_PATH = _(__file__) + os.path.sep + 'serverrc'


logger = get_logger('server')


def sign_in(msg):
    try:
        platform_info = decode(msg)
        client_ip = get_request_data().client_address[0]
        #metric_list = sign_in_handler(client_ip, platform_info)
        sign_in_handler(client_ip, platform_info)
        return 1
    except Exception, e:
        logger.exception('')
        return 0


def main():
    config = load_config(SERVER_CONFIG_PATH)

    local_host = get_ip_address(config.get('local_interface')) 

    rpc_port = config.get('rpc_port')
    rpc_server = ThreadingXMLRPCServer((local_host, rpc_port),)
    rpc_server.register_function(sign_in)
    #server.serve_forever()
    threadinglize(rpc_server.serve_forever, 'rpc_server')()

    rrd_root = config.get('RRD_root', '/tmp')    
    rrd_handler = RRDHandler.getInstance(rrd_root)
    ds_port = config.get('ds_port')
    data_server = DataReciever((local_host, ds_port), rrd_handler)
    threadinglize(data_server.serve_forever, 'data_server')()

    while True:
        _print(threading.enumerate())
        sleep(60)


if __name__ == '__main__':
    main()

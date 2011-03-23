
import os.path
import sys
import threading

from time import sleep

from ThreadingXMLRPCServer import ThreadingXMLRPCServer, get_request_data
from PerfDataReciever import DataReciever
from RRD.RRDHandler import RRDHandler
from models.Interface import sign_in_handler, check_alive
from utils.load_config import load_config
from utils.get_logger import get_logger
from utils.utils import *


_ = lambda f: os.path.dirname(os.path.abspath(f))
SERVER_CONFIG_PATH = _(__file__) + os.path.sep + "serverrc"


logger = get_logger("server")


class MonServer(object):

    def signIn(self, msg):
        try:
            platform_info = decode(msg)
            client_ip = get_request_data().client_address[0]
            sign_in_handler(client_ip, platform_info)
            return 1
        except Exception, e:
            logger.exception("")
            return 0


    def howru(self):
        return 1


def main():
    config = load_config(SERVER_CONFIG_PATH)

    local_host = get_ip_address(config.get("local_interface")) 

    rpc_port = config.get("rpc_port")
    rpc_server = ThreadingXMLRPCServer((local_host, rpc_port),)
    #rpc_server.register_function(sign_in)
    #rpc_server.register_function(howru)
    rpc_server.register_instance(MonServer())
    threadinglize(rpc_server.serve_forever, "rpc_server")()
    logger.info("start RPC server on %s:%d" % (local_host, rpc_port))

    rrd_root = config.get("RRD_root", "/dev/shm")    
    rrd_handler = RRDHandler.getInstance(rrd_root)
    ds_port = config.get("ds_port")
    data_server = DataReciever((local_host, ds_port), rrd_handler)
    threadinglize(data_server.serve_forever, "data_server")()
    logger.info("start data server on %s:%d" % (local_host, ds_port))

    #model_int = Interface()
    agent_timeout = config.get("agent_timeout")
    check_alive_interval = config.get("check_alive_interval")
    scheduled_task(check_alive, "check_alive", True,
                   0, -1, check_alive_interval)(agent_timeout)
    logger.info("check_alive started...")

    while True:
        myprint(threading.enumerate())
        sleep(60)


if __name__ == "__main__":
    main()

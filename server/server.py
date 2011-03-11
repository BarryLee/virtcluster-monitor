
import os.path
import sys

from ThreadingXMLRPCServer import ThreadingXMLRPCServer, get_request_data
from models.interface import sign_in_handler
from utils.load_config import load_config
from utils.get_logger import get_logger
from utils.utils import encode, decode, get_ip_address, _print


_ = lambda f: os.path.dirname(os.path.abspath(f))
SERVER_CONFIG_PATH = _(__file__) + os.path.sep + 'serverrc'


logger = get_logger('server')


def sign_in(msg):
    try:
        platform_info = decode(msg)
        client_ip = get_request_data().client_address[0]
        metric_list = sign_in_handler(client_ip, platform_info)
        return 1, encode(metric_list)
    except Exception, e:
        logger.exception('')
        return 0, ''


def main():
    config = load_config(SERVER_CONFIG_PATH)

    local_host = get_ip_address(config.get('local_interface')) 
    local_port = config.get('port')
    
    server = ThreadingXMLRPCServer((local_host, local_port),)
    server.register_function(sign_in)
    server.serve_forever()


if __name__ == '__main__':
    main()

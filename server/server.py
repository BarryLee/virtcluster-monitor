
from ThreadingXMLRPCServer import ThreadingXMLRPCServer, get_request_data
from models.interface import sign_in_handler
from utils.load_config import load_config
from utils.get_logger import get_logger
from utils.utils import encode, decode, get_ip_address, _print


logger = get_logger('server')


def sign_in(msg):
    try:
        platform_info = decode(msg)
        client_address = get_request_data().client_address
        metric_conf = sign_in_handler(client_address, platform_info)
        return 1, encode(metric_conf)
    except Exception, e:
        logger.exception('')
        return 0, ''


def main():
    config = load_config()

    local_host = get_ip_address(config.get('local_interface')) 
    local_port = config.get('port')
    
    server = ThreadingXMLRPCServer((local_host, local_port),)
    server.register_function(sign_in)
    server.serve_forever()


if __name__ == '__main__':
    main()

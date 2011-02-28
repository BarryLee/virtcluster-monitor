
from ThreadingXMLRPCServer import ThreadingXMLRPCServer, get_request_data
from utils.load_config import load_config
from utils.get_logger import get_logger
from utils.utils import encode, decode, get_ip_address, _print


logger = get_logger('server')


def sign_in(msg):
    try:
        model = decode(msg)
        client_address = get_request_data().client_address
        return 1, ''
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

import sys
from SocketServer import StreamRequestHandler, ThreadingTCPServer

from PerfDataCache import PerfDataCache
from RRD.RRDHandler import RRDHandler
from utils.utils import decode, get_ip_address
from utils.load_config import load_global_config
from utils.get_logger import get_logger


logger = get_logger('PerfDataCacheServer')


class PDCacheRequestHandler(StreamRequestHandler):

    def __init__(self, request, client_address, server, data_cache):
        self.data_cache = data_cache
        StreamRequestHandler.__init__(self, request, client_address, server)


    def handle(self):
        req = ''
        try:
            req = self.rfile.readline().strip()
            #logger.debug('%s' % req)
            host, name, cf, step, start, end = decode(req)
            #logger.debug('%s' % (decode(req),))
            self.wfile.write(self.data_cache.read(host, name, cf, step, start, end))
        except ValueError, e:
            #logger.exception('%s' % req)
            self.wfile.write('Invalid request format')


class PDCacheServer(ThreadingTCPServer):

    def __init__(self, server_address, data_cache):
        self.data_cache = data_cache
        ThreadingTCPServer.__init__(self, server_address, PDCacheRequestHandler)


    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self, self.data_cache)



if __name__ == '__main__':
    config = load_global_config()
    cache_size = config.get('cache_size')
    rrd_root = config.get("RRD_root")
    
    db_handler = RRDHandler.getInstance(rrd_root)
    cache = PerfDataCache.getInstance(cache_size, db_handler)

    public_host = get_ip_address(config.get("public_interface"))
    cache_server_port = config.get('cache_server_port')

    cache_server = PDCacheServer((public_host, cache_server_port), cache)
    logger.info("starting cache server...")
    try:
        cache_server.serve_forever()
    except KeyboardInterrupt, e:
        sys.exit(0)



import socket
from utils.utils import encode
from utils.get_logger import get_logger

logger = get_logger('PerfDataFetcher')


class PerfDataFetcher(object):

    BUFSIZE = 1024

    def __init__(self, server_addr):
        self.server_addr = server_addr


    def getStats(self, host, metric, stat, resolution, start, end):
        res = ''
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(self.server_addr)
            req = encode((host, metric, stat, resolution, start, end))
            sock.send('%s\r\n' % req)
            while True:
                chunk = sock.recv(self.BUFSIZE)
                if not chunk:
                    break
                res += chunk
            sock.close()
        except socket.error, e:
            print e
            logger.exception('')
            sock.close()
            raise e

        return res

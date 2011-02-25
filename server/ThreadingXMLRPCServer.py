from threading import local
from SocketServer import ThreadingTCPServer
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher, SimpleXMLRPCRequestHandler
try:
    import fcntl
except ImportError:
    fcntl = None

__request_data = local()

def get_request_data():
    return __request_data


class ThreadingXMLRPCRequestHandler(SimpleXMLRPCRequestHandler):
    """This class is different from its super class only in that
    it stores the request and client_address in the thread local
    data, so that registered functions may have access to them.
    """

    def __init__(self, request, client_address, server):
        local_data = get_request_data()
        local_data.request = request
        local_data.client_address = client_address
        SimpleXMLRPCRequestHandler.__init__(self, request, client_address, server)



class ThreadingXMLRPCServer(ThreadingTCPServer, SimpleXMLRPCDispatcher):
    
    allow_reuse_address = True
    
    _send_traceback_header = False

    def __init__(self, addr, requestHandler=ThreadingXMLRPCRequestHandler,
                 logRequests=True, allow_none=False, encoding=None, bind_and_activate=True):
        self.logRequests = logRequests

        SimpleXMLRPCDispatcher.__init__(self, allow_none, encoding)
        ThreadingTCPServer.__init__(self, addr, requestHandler, bind_and_activate)

        if fcntl is not None and hasattr(fcntl, 'FD_CLOEXEC'):
            flags = fcntl.fcntl(self.fileno(), fcntl.F_GETFD)
            flags |= fcntl.FD_CLOEXEC
            fcntl.fcntl(self.fileno(), fcntl.F_SETFD, flags)


if __name__ == '__main__':
    server = ThreadingXMLRPCServer(('127.0.0.1', 20060))
    def echo(msg):
        return 'A message from %s:\n%s' % (get_request_data().client_address, msg)
    server.register_function(echo)
    server.serve_forever()


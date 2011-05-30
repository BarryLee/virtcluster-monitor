from utils4test import *
from ThreadingXMLRPCServer import ThreadingXMLRPCServer
from test_xmlrpcfuncs import *

pub_addr = '211.69.198.162'
pri_addr = '192.168.226.62'
localhost = '127.0.0.1'
port = 20060

server = ThreadingXMLRPCServer((localhost, 20060))
server.register_function(echo)
ins = MyCal()
server.register_instance(ins)
server.serve_forever()

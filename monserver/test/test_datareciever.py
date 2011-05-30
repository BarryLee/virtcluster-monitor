from utils4test import *

from PerfDataReciever import PerfDataReciever

server = PerfDataReciever(('127.0.0.1', 20060))
server.serve_forever()


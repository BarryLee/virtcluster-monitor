
import os
import sys
import threading
import time
from SocketServer import UDPServer, BaseRequestHandler

from monserver.api.mon import get_id_by_ip

BUFSZ = 2*1024**3

class ApacheLogRequestHandler(BaseRequestHandler):

    def handle(self):
        data = self.request[0]
        #if not data.endswith('\n'):
        #    raise Exception, 'incomplete line'
        #print len(data), data.endswith('\n')
        self.server.on_data_arrival(self.client_address[0], data)
        #logfile = self.server.locate_file(self.client_address)
        #logfile.write(data)
        #logfile.flush()
        #print data,

class ApacheLogServer(UDPServer):
    
    def __init__(self, server_address, log_dir,
                 RequestHandlerClass=ApacheLogRequestHandler,
                 bind_and_activate=True):
        UDPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)
        self.log_dir = log_dir
        self.log4ip = {}
        self.buf4ip = {}
        #self.bufsz4ip = {}
        self.regular_write_back()

    def on_data_arrival(self, client_ip, data):
        #logfile = self.locate_file(client_ip)
        buf = self.buf4ip.setdefault(client_ip, [])
        #bufsz = self.bufsz4ip.setdefault(client_ip, 0)
        buf.append(data)
        #bufsz += len(data)
        
    def regular_write_back(self):
        def f():
            while True:
                for client_ip, buf in self.buf4ip.items():
                    self.write_back(client_ip) 
                time.sleep(1)
        t = threading.Thread(target=f)
        t.daemon = True
        t.start()

    def write_back(self, client_ip):
        logfile = self.locate_file(client_ip)
        buf = self.buf4ip.setdefault(client_ip, [])
        if len(buf) == 0:
            return
        data = ''
        i = len(buf) - 1
        while i >= 0 and not buf[i].endswith('\n'):
            i -= 1
        data = ''.join(buf[:i+1])
        #bufsz = self.bufsz4ip.setdefault(client_ip, 0)
        if len(data):
            try:
                logfile.write(data)
                logfile.flush()
                del buf[:i+1]
            except IOError, e:
                print e
                del self.log4ip[client_ip]
                self.locate_file(client_ip)
        
    def locate_file(self, client_ip):
        fp = self.log4ip.get(client_ip)
        if fp is None or not os.path.exists(fp.name):
            try:
                rc, client_id = get_id_by_ip(client_ip)
                if not rc:
                    client_id = client_ip
                fname = self.log_dir + '/' + '_'.join([client_id, 'access_log'])
                fp = self.log4ip[client_ip] = open(fname, 'a+')
                print '%s: create file at %s for client %s' % (time.ctime(), fname, client_id)
            except IOError, e:
                print e
                sys.exit(2)

        return fp

if __name__ == '__main__':
    log_root = '/dev/shm'
    #log_root = '/tmp'
    log_dir = 'apache_logs'
    log_dir_abs_path = log_root + '/' + log_dir
    if os.path.isdir(log_root):
        if not os.path.isdir(log_dir_abs_path):
            os.mkdir(log_dir_abs_path)

    s = ApacheLogServer(('',20062), log_dir=log_dir_abs_path)
    s.serve_forever()

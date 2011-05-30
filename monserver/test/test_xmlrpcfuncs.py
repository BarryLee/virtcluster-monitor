
from utils4test import *
from ThreadingXMLRPCServer import get_request_data
from time import sleep


def echo(msg=""):
    print 'A message from %s:\n%s' % (get_request_data().client_address, msg)
    return msg 


class MyCal(object):

    QNO = 0

    def add(self, x, y):
        self.QNO += 1
        qno = self.QNO
        client_ip = get_request_data().client_address[0]
        print 'Got question %d from %s...' % (qno, client_ip)
        sleep(5)
        print 'Finished question %d from %s' % (qno, client_ip)
        return '%s: %d + %d = %d' % (client_ip, x, y, x+y)


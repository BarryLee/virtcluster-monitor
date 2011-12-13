import logging
import socket
import json

import Event

logger = logging.getLogger('event.connection')

BUFSIZE = 8

class Connection(object):

    def __init__(self, addr):
        self._addr = addr

    def sendEvent(self, evt):
        #logger.debug("sending event %s" % evt)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ret = False
        try:
            sock.connect(self._addr)

            #print '%s\r\n' % str(evt)
            if isinstance(evt, Event.Event):
                sock.send('%s\r\n' % Event.dumps(evt))
            else:
                sock.send('%s\r\n' % json.dumps(evt))
            #res = ''
            #while True:
                #chunk = sock.recv(BUFSIZE)
                #if not chunk:
                    #break
                #res += chunk
            res = sock.recv(BUFSIZE)
            #print res 
            if res != '0':
                ret = False
            else:
                ret = True
        except socket.error, e:
            logger.exception('Sending event error')
        finally:
            sock.close()
            return ret


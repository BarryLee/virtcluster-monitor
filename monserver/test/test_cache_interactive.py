from socket import *
import json
import readline

HOST = 'localhost'
PORT = 20061
ADDR = (HOST, PORT)
BUFSIZE = 8


while True:
    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect(ADDR)
        req = raw_input('> ').split()
        if not req:
            continue
        for i in range(3, 6):
            req[i] = int(req[i])
        req = json.dumps(req)
        sock.send('%s\r\n'%req)
        res = ''
        while True:
            chunk = sock.recv(BUFSIZE)
            if not chunk:
                break
            res += chunk
        print res 
        sock.close()
    except KeyboardInterrupt, e:
        sock.close()
        sys.exit(0)



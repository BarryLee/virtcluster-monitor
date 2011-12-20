import socket, select

def main():
    s = socket.socket()
    #host = socket.gethostname()
    host = ''
    port = 0
    s.bind((host, port))

    s.listen(5)
    inputs = [s]

    while True:
        rs, ws, es = select.select(inputs, [], [])
        print rs
        for r in rs:
            if r is s:
                c, addr = s.accept()
                print 'Got connection from', addr
                print c
                inputs.append(c)
                print inputs
            else:
                print 'r:',r
                print 's:',s
                try:
                    data = r.recv(1024)
                    disconnected = not data
                except socket.error:
                    print socket.error
                    disconnected = True

                if disconnected:
                    print r.getpeername(), 'disconnected'
                    inputs.remove(r)
                else:
                    print data

if __name__ == '__main__':
    main()

#!/usr/env python
import threading
import subprocess
import os.path

cmd = 'sh /usr/crane/monitor/daemon/daemon.sh restart'
ssh = 'ssh'

timeout = 20

hosts = open(os.path.dirname(os.path.abspath(__file__))+'/nodes').read().split()
#hosts = [
#       'cu01',
#       'cu02',
#       'cu03',
#       'cu04',
#       'cu05',
#       'cu06',
#       'cu07',
#       'cu08',
#       'cu09',
#       'cu10'
#]

ng = [h for h in hosts]

def start_daemon(host):
    o, e = subprocess.Popen([ssh, host, cmd], \
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).\
        communicate()
    #if e not in [None, '']:
       #print '%s: %s' % (w, e)
    print '%s:\n%s\n%s' % (host, o, e)
    ng.remove(host)


def main():
    print 'Bring up all daemons...'

    threads = []
    for h in hosts:
        t = threading.Thread(target=start_daemon, args=(h,))      
        t.setDaemon(True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout)
    
    if len(ng):
        print 'Not done: ',
	for i in ng:
            print i,
    print


main()

#!/usr/bin/env python

import os
from time import sleep
from findunreachablevms import findunreachablevms

def restartagent(vmid):
    rc = os.system('ssh root@`cranevm show %s|grep IP_PUBLIC=|cut -d= -f2|cut -d, -f1` python /tmp/agent/mon_agent restart' % vmid)
    if rc != 0:
        print 'failed on %s' % vmid
    else:
        print 'Successfully started agent on %s' % vmid
    sleep(1)

if __name__ == '__main__':
    ip = '10.0.0.11'
    port = 20060
    rootdir = '/tmp/rrds'
    unreachablevms, toberemoved = findunreachablevms(ip, port, rootdir)
    print "unreachable vms: %s" % unreachablevms
    map(restartagent, unreachablevms)

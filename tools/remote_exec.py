#!/usr/bin/env python

import subprocess
import sys
import readline
import os.path

import cloud

type = 0

if len(sys.argv) > 1:
    type = 1
    workers = ['root@%s' % (cloud.get_vm_ip(id),) for id in sys.argv[1:]]
else:
    workers = open(os.path.dirname(os.path.abspath(__file__))+'/nodes').read().split()
#    workers = [
#               'cu01',
#               'cu02',
#               'cu03',
#               'cu04',
#               'cu05',
#               'cu06',
#               'cu07',
#               'cu08',
#               'cu09',
#               'cu10'
#]

ssh_cmd = 'ssh'

def main():
    print "remote exec on multiple hosts"
    #prompt()
    try:
        while(1):
            cmd = raw_input('In [%d] ' % prompt())
            for w in workers:
                o, e = subprocess.Popen([ssh_cmd, w, cmd], \
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).\
                    communicate()
                #if e not in [None, '']:
                   #print '%s: %s' % (w, e)
                print '%s:\n%s\n%s' % (w, o, e)

            #prompt()
    except KeyboardInterrupt, e:
        print
    except EOFError, e:
        print

def prompt_counter(start_at):
    count = [start_at]
    def inc():
        count[0] += 1
        return count[0]
        #print 'In [%d]' % count[0],
    return inc

prompt = prompt_counter(-1)
#def prompt():
    #cmd_count = counter(-1)
    #print 'In [%d]' % cmd_count(),

main()

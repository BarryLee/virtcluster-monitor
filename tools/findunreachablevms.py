#!/usr/bin/env python

import xmlrpclib
import re
import os


def get_monitored_vms(server_ip, server_port):
    s = xmlrpclib.ServerProxy('http://%s:%d' % (server_ip, server_port))
    session_output = s.print_session()
    monitored_vms = []
    for l in session_output.splitlines():
        matchs = re.search("(?<='id': ')\d+(?=')", l)
        matchs_last_send = re.search("last_send", l)
        if matchs and matchs_last_send:
            monitored_vms.append(matchs.group(0))

    monitored_vms.sort()
    return monitored_vms

def get_ever_monitored_vms(rrdroot):
    dirs = os.listdir(rrdroot)
    ever_monitored_vms = [id for id in dirs if id.isdigit()]
    ever_monitored_vms.sort()
    return ever_monitored_vms

def get_crane_vms():
    cmd = "cranevm list|grep -v USER|awk '{print $1}'"
    vms = os.popen(cmd).read().split()
    return vms

def findunreachablevms(server_ip, server_port, rrdroot):
    monitored_vms = get_monitored_vms(server_ip, server_port)
    print "active agents: %s" % (','.join(monitored_vms))
    ever_monitored_vms = get_ever_monitored_vms(rrdroot)
    print "ever monitored vms: %s" % (','.join(ever_monitored_vms))
    crane_vms = get_crane_vms()
    print "cranevm list: %s" % (','.join(crane_vms))
    unreachablevms = []
    toberemoved = []
    for i in crane_vms:
        if i not in monitored_vms:
            unreachablevms.append(i)
    for i in ever_monitored_vms:
        if i not in crane_vms:
            toberemoved.append(i)
    #for i in ever_monitored_vms:
        #if i not in crane_vms:
            #toberemoved.append(i)
        #elif i not in monitored_vms:
            #unreachablevms.append(i)

    return unreachablevms, toberemoved


if __name__ == '__main__':
    ip = '10.0.0.11'
    port = 20060
    rootdir = '/tmp/rrds'
    unreachablevms, toberemoved = findunreachablevms(ip, port, rootdir)
    print "unreachable vms: %s" % (','.join(unreachablevms))
    print "to be removed: %s" % (','.join(toberemoved))


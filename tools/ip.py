#!/usr/bin/env python

import socket
import fcntl
import struct
import subprocess

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def parse_ifconfig(output):
    nifs = output.split('\n\n')
    res = []
    #print nifs
    for nif in nifs:
        #print len(nif)
        if len(nif) == 0:
            continue
        #print nif
        nifd = {}
        nif = nif.splitlines()
        sum = nif[0].strip().split()
        nifd['ifname'] = sum[0]
        nifd['hwaddr'] = sum[-1]
        for line in nif[1:]:
            line = line.strip()
            if line.startswith('inet addr'):
                if not nifd.has_key('addr_v4'):
                    nifd['addr_v4'] = line.split()[1].split(':')[1].strip()
            elif line.startswith('inet6 addr'):
                if line.rfind('Global') != -1:
                    s = line.find(':')
                    e = line.find('/')
                    if s != -1 and e != -1:
                        nifd['addr_v6'] = line[s+1:e].strip()

        res.append(nifd)
    return res

def get_local_ifs():
    cmd = '/sbin/ifconfig'
    o, e = subprocess.Popen([cmd],
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE).communicate()
    return parse_ifconfig(o)
    
def get_inet6_addr(user='', host=None, prefix=''):
    ifconfig_cmd = '/sbin/ifconfig'
    ssh_cmd = 'ssh'
    if host is None:
        cmd = [ifconfig_cmd]
    else:
        if user != '':
            ssh_arg = user + '@' + host
        else:
            ssh_arg = host
        cmd = [ssh_cmd, ssh_arg, ifconfig_cmd]
    o, e = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE).communicate()
    nifs = parse_ifconfig(o)
    ret = ''
    for nif in nifs:
        if nif['addr_v6'].startswith(prefix):
            ret = nif['addr_v6']
            break
    return ret

if __name__ == "__main__":
    #print get_ip_address('eth0')
    #print get_ip_address('lo')
    print get_inet6_addr(user='', host='cu01', prefix='')

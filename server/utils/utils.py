#-*- coding:utf-8 -*-
import os
import sys
import socket
import fcntl
import struct


current_dir = lambda f: os.path.dirname(os.path.abspath(f))

parent_dir = lambda f: os.path.dirname(current_dir(f))

if sys.version[:3] >= '2.6':
    import json
else:
    # Because of simplejson's intra-package import statements, the path
    # of simplejson has to be temporarily add to system path, otherwise 
    # we will get ImportError when import from the upper level.
    cur_dir = current_dir(__file__)
    sys.path.append(cur_dir)
    import simplejson as json
    sys.path.remove(cur_dir)


import pprint
pp = pprint.PrettyPrinter(indent=2)
def _print(msg):
    pp.pprint(msg)


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def decode(data):
    #return json.loads(data)
    return _parseJSON(json.loads(data))
    #return eval(data)


def encode(data):
    #return json.dumps(data, sort_keys=True, indent=2)
    return json.dumps(data)


# turns unicode back into str
def _parseJSON(obj):
    if obj is None:
        return obj
    elif type(obj) in (int, float, str, bool):
        return obj
    elif type(obj) == unicode:
        return str(obj)
    elif type(obj) in (list, tuple, set):
        obj = list(obj)
        for i,v in enumerate(obj):
            obj[i] = _parseJSON(v)
    elif type(obj) == dict:
        for i,v in obj.iteritems():
            obj.pop(i)
            obj[_parseJSON(i)] = _parseJSON(v)
    else:
        print "invalid object in data, converting to string"
        obj = str(obj) 
    return obj


def get_from_dict(dict_, keys):
    ret = dict_
    if type(keys) is str:
        ret = dict_[keys]
    else:
        keys = list(keys)
        for i in keys:
            ret = ret[i]

    return ret


def put_to_dict(dict_, keys, val, createMidNodes=False):
    if type(keys) is str:
        dict_[keys] = val
    else:
        keys = list(keys)
        midKeys = keys[0:-1]
        theKey = keys[-1]
        sub = dict_
        for i in midKeys:
            try:
                sub = sub[i]
            except KeyError, e:
                if createMidNodes:
                    sub[i] = {}
                    sub = sub[i]
                else:
                    raise
        sub[theKey] = val

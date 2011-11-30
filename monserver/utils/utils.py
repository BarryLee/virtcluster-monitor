#-*- coding:utf-8 -*-
import os
import sys
import socket
import fcntl
import struct
import threading
import time
import logging

logger = logging.getLogger('monserver.utils.utils')

__all__ = ["get_ip_address", "decode", "encode", "get_from_dict", 
           "put_to_dict", "threadinglize", "scheduled_task", "myprint", "rpc_formalize"]

current_dir = lambda f: os.path.dirname(os.path.abspath(f))

parent_dir = lambda f: os.path.dirname(current_dir(f))

if sys.version[:3] >= "2.6":
    import json
else:
    # Because of simplejson"s intra-package import statements, the path
    # of simplejson has to be temporarily add to system path, otherwise 
    # we will get ImportError when import from the upper level.
    cur_dir = current_dir(__file__)
    sys.path.append(cur_dir)
    import simplejson as json
    sys.path.remove(cur_dir)


import pprint
pp = pprint.PrettyPrinter(indent=2)
def myprint(msg):
    pp.pprint(msg)


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack("256s", ifname[:15])
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


def threadinglize(target_, tName=None, isDaemon_=True):
    def func_(*args_, **kwargs_):
        t = threading.Thread(target=target_, args=args_, kwargs=kwargs_)
        if isDaemon_:
            t.setDaemon(True)
        if tName:
            t.setName(tName)
        else:
            t.setName(target_.__name__)
        t.start()
    return func_


def scheduled_task(procedure, tname=None, isdaemon=True, 
                   schedule_delay=0, loop_time=0, loop_interval=0):
    def schedule(*args_, **kwargs_):
        def do_task(*args, **kwargs):
            loop_counter = loop_time
            while loop_time == -1 or loop_counter >= 0:
                procedure(*args_, **kwargs_)
                loop_counter -= 1
                if loop_interval > 0:
                    time.sleep(loop_interval)

        if schedule_delay > 0:
            t = threading.Timer(schedule_delay, do_task, args_, kwargs_)
        else:
            t = threading.Thread(target=do_task, args=args_, kwargs=kwargs_)
        t.daemon = isdaemon
        if tname:
            t.name = tname
        else:
            t.name = procedure.__name__
        t.start()
    return schedule


def rpc_formalize(errmsg=None):
    logger.debug('test')
    def wrapper(func):
        def f(*args, **kwargs):
            try:
                res = func(*args, **kwargs)
                return [True, res]
            except Exception, e:
                logger.exception('')
                return [False, errmsg or str(e)]
        return f
    return wrapper

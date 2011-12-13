import xmlrpclib

from monserver.utils.load_config import load_config
from monserver.event.connection import Connection

__all__ = ['send_event', 'get_events', 'set_threshold', 'unset_threshold',
           'get_host_thresholds']

config = load_config()

conn = Connection((config.get('server_ip'), config.get('evt_port')))
rpc_client = xmlrpclib.ServerProxy('http://localhost:%s' % config.get('evt_srv_port'))

def send_event(evt):
    return conn.sendEvent(evt)

def set_threshold(threshold_specs):
    return rpc_client.set_threshold(threshold_specs)

def unset_threshold(tid):
    return rpc_client.unset_threshold(tid)

def get_events(selectors):
    return rpc_client.get_events(selectors)

def get_host_thresholds(hostid):
    return rpc_client.get_host_thresholds(hostid)

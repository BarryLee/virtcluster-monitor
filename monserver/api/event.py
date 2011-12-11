import xmlrpclib

from monserver.utils.load_config import load_config
from monserver.event.connection import Connection

__all__ = ['send_event', 'unset_threshold']

config = load_config()

conn = Connection((config.get('server_ip'), config.get('evt_port')))
rpc_client = xmlrpclib.ServerProxy('http://localhost:%s' % config.get('evt_srv_port'))

def send_event(evt):
    return conn.sendEvent(evt)

def unset_threshold(tid):
    return rpc_client.unset_threshold(tid)


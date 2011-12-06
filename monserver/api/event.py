import xmlrpclib

from monserver.utils.load_config import load_config
from monserver.event.connection import Connection

__all__ = ['send_event']

config = load_config()

conn = Connection((config.get('server_ip'), config.get('evt_port')))

def send_event(evt):
    return conn.sendEvent(evt)


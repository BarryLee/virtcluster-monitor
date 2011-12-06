import logging
import os

from utils.load_config import load_global_config
from utils.utils import current_dir
from utils import logging_conf
from event.EventBus import EventBus
from event.EventDB import EventDB

config = load_global_config()
logger = logging.getLogger("event.main")

event_db_conf = current_dir(__file__) + os.path.sep + config.get('event_db_conf')

def save_event(evt):
    conn = EventDB.getInstance(event_db_conf).openSession()
    conn.save(evt)
    conn.commit()
    conn.close()
    return True

def get_events(selector={}):
    conn = EventDB.getInstance(event_db_conf).openSession()
    res = [e.info() for e in conn.load(selector)]
    conn.commit()
    conn.close()
    return res

def main():
    ip = config.get('server_ip')
    ebus = EventBus((ip, config.get('evt_port')), (ip, config.get('evt_srv_port')))

    # handlers

    ebus.handleSubscribe('HostInactive', save_event)
    ebus.handleSubscribe('HostExpire', save_event)
    ebus.handleSubscribe('ThresholdViolation', save_event)

    ebus.registerService(get_events)
    ebus.startAll()

if __name__ == '__main__':
    main()

import logging
import os
import time
import copy

from utils.load_config import load_global_config
from utils.utils import current_dir, rpc_formalize
from utils import logging_conf
from event.EventBus import EventBus, send_event
from event.EventDB import EventDB
from threshold.ThresholdManager import *
#from threshold.Threshold import *
from threshold import Threshold

CompositeThreshold = Threshold.CompositeThreshold
Threshold.send_event = send_event

logger = logging.getLogger("event.main")

curdir = current_dir(__file__)
config = load_global_config()

event_db_conf = curdir + os.path.sep + config.get('event_db_conf')
edb = EventDB.getInstance(event_db_conf)

threshold_db_conf = curdir + os.path.sep + config.get('threshold_db_conf')
threshold_manager = ThresholdManager(threshold_db_conf)

def save_event(evt):
    conn = edb.openSession()
    conn.save(evt)
    conn.commit()
    conn.close()
    return True

def delete_events(selector={}):
    conn = edb.openSession()
    conn.delete(selector)
    conn.commit()
    conn.close()
    return True

@rpc_formalize()
def get_events(selector={}):
    conn = edb.openSession()
    evts = conn.load(selector)
    res = [copy.copy(e.info()) for e in evts]
    for e in evts:
        e.unread = False
    conn.commit()
    conn.close()
    return res

def main():
    ip = config.get('server_ip')
    ebus = EventBus((ip, config.get('evt_port')), (ip, config.get('evt_srv_port')))

    # handlers

    ebus.handleSubscribe('HostInactive', save_event)
    #ebus.handleSubscribe('HostDel', save_event)
    ebus.handleSubscribe('ThresholdViolation', save_event)

    for tid, threshold_handler in threshold_manager._thresholds.iteritems():
        if hasattr(threshold_handler, 'hosts'):
            hosts = threshold_handler.hosts
        else:
            hosts = [threshold_handler.host]
        for h in hosts:
            ebus.handleSubscribe('PerfDataArrival', threshold_handler, h)

    @rpc_formalize()
    def set_threshold(threshold_specs):
        threshold_handler = threshold_manager.setThreshold(threshold_specs)
        if hasattr(threshold_handler, 'hosts'):
            hosts = threshold_handler.hosts
        else:
            hosts = [threshold_handler.host]
        for h in hosts:
            ebus.handleSubscribe('PerfDataArrival', threshold_handler, h)

    @rpc_formalize()
    def unset_threshold(tid):
        try:
            threshold_handler = threshold_manager.get(tid)
        except ThresholdManagerException, e:
            logger.warning(e)
            return
        if hasattr(threshold_handler, 'hosts'):
            hosts = threshold_handler.hosts
        else:
            hosts = [threshold_handler.host]
        for h in hosts:
            ebus.handleUnsubscribe('PerfDataArrival', threshold_handler, h)
            delete_events({'etype':'ThresholdViolation', 'target':h, 
                'filter': lambda e: e.tid == tid})
        threshold_manager.unsetThreshold(tid)

    @rpc_formalize()
    def get_host_thresholds(host):
        return [i.info() for i in ebus.getSubscribers("PerfDataArrival", host) \
                if isinstance(i, Threshold.Threshold)] 

    ebus.registerService(set_threshold, 'set_threshold')
    ebus.registerService(unset_threshold, 'unset_threshold')
    ebus.registerService(get_events, 'get_events')
    ebus.registerService(get_host_thresholds, 'get_host_thresholds')
    try:
        ebus.startAll()
    except KeyboardInterrupt, e:
        logger.info("closing...")
        ebus.cleanup()
        #time.sleep(1)

if __name__ == '__main__':
    main()

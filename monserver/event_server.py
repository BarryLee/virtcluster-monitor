
from utils.load_config import load_config
from utils.utils import current_dir
from utils.get_logger import get_logger
from event.EventBus import EventBus
from event.EventDB import EventDB

config = load_global_config()
logger = get_logger("event.main")

def main():
    ip = config.get('server_ip')
    ebus = EventBus((ip, config.get('evt_port')), (ip, config.get('evt_srv_port')))

    # handlers
    event_db_conf = current_dir(__file__) + os.path.sep + config.get('event_db_conf')

    edb = EventDB(event_db_conf)
    ebus.handleSubscribe('HostInactive', edb.save)
    ebus.handleSubscribe('HostExpire', edb.save)
    ebus.handleSubscribe('ThresholdViolation', edb.save)


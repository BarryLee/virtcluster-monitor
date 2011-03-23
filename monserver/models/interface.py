import os.path
import sys

###############################################################
# temporary solution for importing upper level modules/packages
_ = lambda f: os.path.dirname(os.path.abspath(f))

par_dir = _(_(__file__))
if par_dir not in sys.path:
    sys.path.append(par_dir)
###############################################################

from ModelDB import ModelDB, ModelDBSession
from resources import Host, VirtualHost, CPU, Disk, Partition, NetworkInterface
import ID
from utils.load_config import load_config
from utils.utils import decode
from utils.get_logger import get_logger

logger = get_logger('models.interface')

#config = load_config()
cur_dir = _(__file__)

DB_CONFIG_URL = cur_dir + os.path.sep + 'modelstore.conf'
modeldb = ModelDB.getInstance(DB_CONFIG_URL)

METRIC_CONFIG_PATH = cur_dir + os.path.sep + 'metric.conf'


def sign_in_handler(ip, info):
    is_virtual = info.get('virtual')
    virt_type = info.get('virt_type')

    if not is_virtual:
        id = ID.host_id_gen(ip)
        host_type = 'Host'

    global modeldb
    session = modeldb.openSession()
    host = session.getResource(host_type, id)
    if host is None:
        host = Host(ip)
        host.id = id
    else:
        logger.debug('retieve object %s from db' % host)

    host.is_virtual = is_virtual
    host.virt_type = virt_type

    components = info.get('components')

    cpuinfo = components.get('cpu')
    cpu = CPU(**cpuinfo)
    host.hasOne('cpu', cpu)

    disksinfo = components.get('filesystem')['local']
    for dn, di in disksinfo.iteritems():
        if di.has_key('disk'):

            diskname = di.get('disk')
            diskinfo= disksinfo.get(diskname)
            disk = Disk(**diskinfo)
            disk.update({'name': diskname})
            
            partition = Partition(**di)
            partition.update({'name': dn})

            disk.addOne('partitions', dn, partition)
            host.addOne('disks', diskname, disk)
        else:
            continue

    meminfo = components.get('memory')
    host.update(meminfo)

    ifsinfo = components.get('network')
    for ifn, ifi in ifsinfo.iteritems():
        if ifn not in ('lo',):
            network_interface = NetworkInterface(**ifi)
            network_interface.update({'name': ifn})
            host.addOne('network_interfaces', ifn, network_interface)

        #if virt_type is not None:
        #host.virt_type = virt_type

    host.metric_list = info['metric_groups']

    session.setResource(host.__class__.__name__, host.id, host)
    session.setResource('active', host.ip, host)
    session.commit()
    session.close()


def host_metric_conf(host_id):
    global modeldb
    session = modeldb.openSession()
    
    host_obj = session.getResource(host.__class__.__name__, host_id)
    assert host_obj is not None
    session.close()
    
    return host_obj.metric_list
    

def getidbyip(ip):
    global modeldb
    session = modeldb.openSession()

    host_obj = session.getResource('active', ip)
    session.close()
    return host_obj.id


def setLastArrival(host_id):
    pass

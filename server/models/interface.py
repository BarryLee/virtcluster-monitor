import os.path
import sys

_ = lambda f: os.path.dirname(os.path.abspath(f))

par_dir = _(_(__file__))
if par_dir not in sys.path:
    sys.path.append(par_dir)

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

    host = Host(ip)
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

    if not is_virtual:
        host.id = ID.host_id_gen(ip)
        #if virt_type is not None:
        #host.virt_type = virt_type

    host.use_default_metrics = True

    global modeldb
    session = modeldb.openSession()
    session.addResource(host.__class__.__name__, host.id, host)
    session.commit()
    session.close()
    
    metric_list = metric_list_gen(host)
    
    return metric_list


def metric_list_gen(host_obj):
    if not host_obj.use_default_metrics:
        return host_obj.metric_list

    metric_config = load_config(METRIC_CONFIG_PATH)

    if host_obj.virt_type is None:
        metric_list_path = metric_config['default_path']['normal']
    else:
        virt_type = host_obj.virt_type
        if not host_obj.is_virtual:
            host_type = 'host'
        else:
            host_type = 'guest'
        metric_list_path = metric_config['default_path'][virt_type + 
                                                         '_' + host_type]

    metric_list = decode(open(cur_dir + os.path.sep + metric_list_path).read())

    metric_groups = [] 
    for metric_group in iter(metric_list['metric_groups']):
        this_group = {}
        this_group['name'] = metric_group['name']
        this_group['period'] = metric_group['period']
        this_group['metrics'] = metric_group['metrics']
        #for metrics in metric_group:
            #for metric in metrics:
                #if metric['enabled']:
                    #this_group['metrics'].append({'name': metric['name']})
        if this_group['name'] == 'DiskModule':
            devices = []
            for disk in host_obj.disks.values():
                devices.append(disk.name)
                if metric_config['enable_partitions']:
                    if hasattr(disk, 'partitions'):
                        for partition in disk.partitions:
                            devices.append(partition.name)
            for device in devices:
                #logger.debug(this_group)
                dup_group = {'args': {'device': device}}
                dup_group.update(this_group)
                #logger.debug(dup_group)
                metric_groups.append(dup_group)
                #logger.debug(metric_groups)
        else:
            metric_groups.append(this_group)
            #logger.debug(metric_groups)

    return {"metric_groups" : metric_groups}




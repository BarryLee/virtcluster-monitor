import xmlrpclib

from monserver.RRD.RRDHandler import RRDHandler
from monserver.utils.load_config import load_config

config = load_config()
rrd_handler = RRDHandler.getInstance(config.get('RRD_root'))
rpc_client = xmlrpclib.ServerProxy('http://localhost:%s' % config.get('rpc_port'))

disk_metrics = ['rps','wps','rrqmps','wrqmps','rsecps','wsecps',
                'rkBps','wkBps','util','await','avgrq_sz','avgqu_sz'] 
d_table = {}

__all__ = ['get_stats', 'get_host_state', 'get_host_info', 
           'get_host_list', 'get_metric_list', 'get_active_hosts']

def get_stats(hostId, metricName, stat="AVERAGE", step=15, \
                   startTime=None, endTime=None):
    hostId = str(hostId)
    metricName = str(metricName)
    stat = str(stat)

    if '-' in metricName:
        device, metric_name = metricName.rsplit('-')
    else:
        device, metric_name = '', metricName

    if metric_name in disk_metrics:
        if d_table.has_key(hostId):
            device = d_table[hostId]
        else:
            rc, hostinfo = rpc_client.hostInfo(hostId)
            if rc:
                device = hostinfo['disks'].keys()[0]
                d_table[hostId] = device
            else:
                raise Exception, hostinfo

    return [i for i in rrd_handler.read(hostId, device, metricName, stat, step, \
                        startTime, endTime)[1] if i[1] is not None]

def get_host_state(hostId):
    assert type(hostId) is str
    return rpc_client.hostState(hostId)

def get_host_info(hostId):
    assert type(hostId) is str
    return rpc_client.hostInfo(hostId)

def get_host_list(hostType="all"):
    return rpc_client.hostList(hostType)

def get_metric_list(hostId):
    return rpc_client.metricList(hostId)

def get_active_hosts():
    return rpc_client.activeHosts()

#def add_threshold(hostIds, tid):
    #return rpc_client.addThreshold(hostIds, tid)

#def rm_host_threshold(hostId, tid):
    #return rpc_client.rmHostThreshold(hostId, tid)


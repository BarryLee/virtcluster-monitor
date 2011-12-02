import xmlrpclib

from RRD.RRDHandler import RRDHandler
from utils.load_config import load_config

config = load_config()
rrd_handler = RRDHandler.getInstance(config.get('RRD_root'))
rpc_client = xmlrpclib.ServerProxy('http://localhost:%s' % config.get('rpc_port'))

disk_metrics = ['rps','wps','rrqmps','wrqmps','rsecps','wsecps',
                'rkBps','wkBps','util','await','avgrq_sz','avgqu_sz'] 
d_table = {}

__all__ = ['get_stats', 'get_host_state', 'get_host_info', 
           'get_host_list', 'get_metric_list']

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
            hostinfo = rpc_client.getHostInfo(hostId)[1]
            device = hostinfo['disks'].keys()[0]
            d_table[hostId] = device

    return rrd_handler.read(hostId, device, metricName, stat, step, \
                        startTime, endTime)[1]

def get_host_state(hostId):
    assert type(hostId) is str
    return rpc_client.getHostState(hostId)

def get_host_info(hostId):
    assert type(hostId) is str
    return rpc_client.getHostInfo(hostId)

def get_host_list():
    return rpc_client.hostList()

def get_metric_list(hostId):
    return rpc_client.metricList(hostId)


from celery.decorators import task

import mon_db_handler
from mon_db_handler import MonDBHandler, MonDBException
from mon_config_manager import global_config
from mon_center_utils import get_ip_address

config = global_config

#rw_handler = MonDBHandler.getInstance(config['db']['root_dir'])
rw_handler = mon_db_handler.getInstance(config['db']['root_dir'])

@task()
def get_stats(hostId, metricName, stat="AVERAGE", step=15, \
                   startTime=None, endTime=None):
    """
    Get the specified host's monitor data between startTime and EndTime. A list
    of supported metrics by the interested host can be retrieved by calling 
    get_metric_list(...). Specifically, with metricName='summary', a summary
    contains CPU usage, memory usage, bytes in per second and bytes out per 
    second will be returned; if hostId is assigned a site's name, the site's 
    data will be returned(site's name cannot be used with metric 'summary').

    @param hostId: ID of the host(id of vm or host name of pm).
    @type hostId: string
    @param metricName: Metric name.
    @type metricName: string
    @param stat: Consolidation type of the data, one of AVERAGE, MAX and MIN, 
        defaults to AVERAGE.
    @type stat: string
    @param step: The interval between every two data, defaults to 15 sec.
    @type step: integer
    @param startTime: The start time of returned data. When specified, can be 
        either a positive int represents seconds since epoch, or a negtive int 
        represents seconds back from the end time. If it is None or not given,
        the last update will be returned. Defaults to None.
    @type startTime: integer
    @param endTime: The end time of returned data. When specified, can be 
        either a positive int represents seconds since epoch, or a negtive int 
        represents seconds back from the last update time. If it is None or not 
        given, the data from start time to last update will be returned. 
        Defaults to None.
    @type endTime: integer
    @return: A list of data, each in a form of [<timestamp>, <value>]. 
        Specifically, if metricName is 'summary', a dictionary of four entries(
        cpu_usage, mem_usage, bytes_in, bytes_out) will be returned.
    @rtype: list
    """
    # TODO validate input args

    hostId = str(hostId)
    metricName = str(metricName)
    stat = str(stat)
    #try:
    if metricName == 'summary':
        ret = {}
        ret['cpu_usage'] = rw_handler.read(hostId, 'cpu_usage', stat, step, startTime, endTime)[1]
        ret['mem_usage'] = rw_handler.read(hostId, 'mem_usage', stat, step, startTime, endTime)[1]
        ret['bytes_in'] = rw_handler.read(hostId, 'bytes_in', stat, step, startTime, endTime)[1]
        ret['bytes_out'] = rw_handler.read(hostId, 'bytes_out', stat, step, startTime, endTime)[1]
    else:
        ret = rw_handler.read(hostId, metricName, stat, step, \
                               startTime, endTime)[1]
    #except MonDBException, e:
        #ret = None
    #arr = [val[1] for val in ret[1]]
    return ret

#get_stats = get_vm_stats = get_node_stats

def human_readable_mem_size(mem_size, precision=0):
    mem_size = float(mem_size)
    unit = 'K'          # mem_size is in kb
    GIGA = 1024 ** 2 
    MEGA = 1024
    if mem_size >= GIGA:
        mem_size /= GIGA
        unit = 'G'
    elif mem_size >= MEGA:
        mem_size /= MEGA
        unit = 'M'

    if precision == 0:
        mem_size = int(mem_size)
    else:
        mem_size = round(mem_size, precision)

    return mem_size, unit

@task()
def get_remote_hostpool_info(site_name):
    if site_name == config.get('site_info')['name']:
        return [site_name, get_hostpool_info()]
    site_info = config.get('site_list').get(site_name)
    if site_info is None:
        return None
    addr = site_info['address']
    import xmlrpclib
    p = xmlrpclib.ServerProxy('http://%s%s' % 
                              (addr['host'], addr['port']))
    ret = [site_name, p.get_hostpool_info()]
    return ret

@task()
def get_hostpool_info():
    import cloud
    suc, hostpool = cloud.get_hostpool_info()
    if not suc:
        return None
    ret = []
    for host in hostpool:
        hostinfo = {}
        tm, unit = human_readable_mem_size(host['totalMemory'])
        tm = str(tm) + unit
        fm, unit = human_readable_mem_size(host['freeMemory'])
        fm = str(fm) + unit
        uc = round(float(host['usedCpu']) / float(host['totalCpu']), 1)
        hostinfo['name'] = host['name']
        hostinfo['id'] = host['guid']
        hostinfo['numofvms'] = len(host['virtualMachines'])
        hostinfo['totalMemory'] = tm
        hostinfo['freeMemory'] = fm
        hostinfo['totalCpu'] = int(host['totalCpu']) / 100
        hostinfo['usedCpu'] = str(uc) + '%'
        ret.append(hostinfo)

    return ret

@task()
def get_platform_info(hostId):
    platinfo = rw_handler.read(hostId, 'metadata')['basic_info']['Platform Info']
    return platinfo

@task()
def get_site_info():
    total_cpu_num = 0
    total_mem_size = 0
    for node in config['node_list']:
        try:
            platinfo = get_platform_info(node)
            total_cpu_num += platinfo['cpu_num']

            mem_total = platinfo['mem_total']
            i = len(mem_total) - 1
            while i > 0:
                if mem_total[i].isdigit():
                    break
                i -= 1
            #total_mem_size += int(platinfo['mem_total'].split()[0])
            total_mem_size += int(mem_total[:i+1])
        except MonDBException, e:
            print e

    result = {}
    site_info = config.get('site_info')
    for k, v in site_info.items():
        result[k] = v
    result['num_of_nodes'] = len(config['node_list'])
    result['site_cpu_num'] = total_cpu_num
    if total_mem_size >= 1024 ** 2:
        total_mem_size /= 1024 ** 2
        unit = 'GB'
    elif total_mem_size >= 1024:
        total_mem_size /= 1024
        unit = 'MB'
    result['site_mem_total'] = '%d%s' % (total_mem_size, unit)
    
    #result['metric_groups'] = config.get('site_summary_metrics')

    return result


@task()
def get_site_summary():
    #print config['node_list']
    node_sums = {}
    failed = []
    result = {}

    for node in config['node_list']:
        try:
            #node_sum = rw_handler.read(node, 'summary', step='3600', \
                    #startTime='-3600*24')
            summary = get_stats(node, 'summary', step='60')
            node_sum = {}
            node_sum['cpu_usage'] = summary['cpu_usage'][0][1]
            node_sum['mem_usage'] = summary['mem_usage'][0][1]
            #platinfo = get_platform_info(node)
            #node_sum['cpu_num'] = platinfo['cpu_num']
            #node_sum['mem_total'] = int(platinfo['mem_total'][:-1])
        except MonDBException, e:
            print e
            node_sum = None
        if node_sum is None:
            failed.append(node)
        else:
            node_sums[node] = node_sum

    monitored_node_count = len(node_sums.items())
    total_cpu_usage = 0.0
    total_mem_usage = 0.0
    #total_cpu_num = 0
    #total_mem_size = 0
    
    max_cpu = ['', 0]
    max_mem = ['', 0]

    if monitored_node_count > 0:
        for node, node_sum in node_sums.items():
            cpu_usage = (node_sum['cpu_usage'] is None and [0] or \
                    [node_sum['cpu_usage']])[0]
            mem_usage = (node_sum['mem_usage'] is None and [0] or \
                    [node_sum['mem_usage']])[0]
            if cpu_usage > max_cpu[1]:
                max_cpu[0] = node
                max_cpu[1] = cpu_usage
            if mem_usage > max_mem[1]:
                max_mem[0] = node
                max_mem[1] = mem_usage
            total_cpu_usage += cpu_usage
            total_mem_usage += mem_usage
            #total_cpu_usage += (node_sum['cpu_usage'][0][1] is None and [0] or \
                    #[node_sum['cpu_usage'][0][1]])[0]
            #total_mem_usage += (node_sum['mem_usage'][0][1] is None and [0] or \
                    #[node_sum['mem_usage'][0][1]])[0]
            #total_cpu_num += node_sum['cpu_num']
            #total_mem_size += node_sum['mem_total']

        #total_cpu_usage = total_cpu_usage / monitored_node_count
        #total_mem_usage = total_mem_usage / monitored_node_count

    #result['site_cpu_num'] = total_cpu_num
    #if total_mem_size > 1024 ** 2:
        #total_mem_size /= 1024 ** 2
        #unit = 'GB'
    #elif total_mem_size > 1024:
        #total_mem_size /= 1024
        #unit = 'MB'
    #result['site_mem_total'] = '%d%s' % (total_mem_size, unit)
    result['unmonitored'] = failed
    result['site_cpu_usage'] = total_cpu_usage / monitored_node_count
    result['site_mem_usage'] = total_mem_usage / monitored_node_count
    result['max_cpu'] = max_cpu
    result['max_mem'] = max_mem
    #result['num_of_nodes'] = len(config['node_list'])

    import cloud
    vms_info = cloud.get_vms_info()[1]
    result['num_of_vms'] = len(vms_info)

    return result


#def get_current_sessions():
    #host = get_ip_address('eth0')
    #port = config['listen_channel']['port']
    #import xmlrpclib
    #x = xmlrpclib.ServerProxy('http://%s:%d' % (host, port))
    #sessions = x.print_session()

@task()
def get_metric_list(hostId):

    # TODO check the id before proceed

    ret = rw_handler.read(hostId, 'metadata')['metric_groups']
    return ret

@task()
def get_site_stats():
    nodelist = config.get('node_list')
    bad_count = 0
    cpu_sum = 0.0
    mem_sum = 0.0
    c_times = []
    m_times = []
    for n in nodelist:
        try:
            t_cpu, cpu_usage = get_stats(n, 'cpu_usage', step=60)[0]
            t_mem, mem_usage = get_stats(n, 'mem_usage', step=60)[0]
            c_times.append(t_cpu)
            m_times.append(t_mem)
            cpu_sum += ((cpu_usage is None) and [0] or [cpu_usage])[0]
            mem_sum += ((mem_usage is None) and [0] or [mem_usage])[0]
        except MonDBException, e:
            print e
            bad_count += 1

    def find_t(tlist):
        t_sum = reduce((lambda x,y: x+y), tlist) 
        t_avg = float(t_sum) / len(tlist)
        t_found = reduce((lambda x,y: (abs(t_avg-x) < abs(t_avg-y)) and x or y),
                      tlist)
        return int(t_found)

    num_of_monitored = len(nodelist) - bad_count
    cpu_avg = cpu_sum / num_of_monitored
    mem_avg = mem_sum / num_of_monitored 
    ret_c = (find_t(c_times), cpu_avg)
    ret_m = (find_t(m_times), mem_avg)

    return ret_c, ret_m


def get_realtime_stats(hostId, metricName):
    return None

if __name__ == "__main__":
    import unittest

    from time import sleep, time
    from mon_center_utils import get_ip_address
    import random
    class mon_getter_test(unittest.TestCase):

        local = get_ip_address('eth0')
        hosts = ['cu01']
        #metrics = ['cpu_idle', 'mem_available', 'packets_out',
                   #'bytes_in', 'bytes_out', 'packets_in']

        #def testlast(self):
            #l_ = len(self.metrics)
            #for n in range(7):
                #thisHost = self.hosts[random.randint(0, len(self.hosts)-1)]
                #thisMetric = self.metrics[random.randint(0, l_-1)]
                #arr = get_node_stats(thisHost, thisMetric)
                #print thisHost, ':', thisMetric, ':', arr
                ##self.assertEqual(type(arr[0]), float)
                #sleep(5)

        #def testrandom(self):
            #l_ = len(self.metrics)
            #for n in range(70):
                #thisHost = self.hosts[random.randint(0, len(self.hosts)-1)]
                #thisMetric = self.metrics[random.randint(0, l_-1)]
                #arr = get_node_stats(thisHost, thisMetric, "AVERAGE", 5, \
                                    #int(time())-60)
                #print thisHost, ':', thisMetric, ':', arr
                #sleep(1)

        #def testcpumem(self):
            #print get_cpu_mem(self.hosts[0])

        #def testwrongmetric(self):
            #self.assertRaises(MonDBException, get_node_stats, self.hosts[0], \
                             #'load_fif', 'AVERAGE', 5)

        #def testmetriclist(self):
            #ret = get_metric_list(self.hosts[0])
            ##print ret
            #self.assertEquals(type(ret), list)

        #def testvartimeinput(self):
            #arr = get_node_stats(self.hosts[0], self.metrics[0], 'AVERAGE', 5, -60)
            #print arr

        def testsitesummary(self):
            print get_site_summary()
            #print get_platform_info('cu01')
            print get_site_info()

    unittest.main()

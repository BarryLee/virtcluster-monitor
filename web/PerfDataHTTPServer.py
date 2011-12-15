import pdb
import logging

from flask import Flask, request, abort, url_for, redirect
app = Flask(__name__)

#from monserver.PerfDataCache import PerfDataCache
#from monserver.RRD.RRDHandler import RRDHandler
from monserver.api.mon import get_stats
from monserver.utils.utils import encode
from monserver.utils.load_config import load_global_config
from monserver.utils import logging_conf
from xmlrpclib import ServerProxy

logger = logging.getLogger('monserver.web')


config = load_global_config()
#cache_size = config.get('cache_size')
#rrd_root = config.get("RRD_root")

#db_handler = RRDHandler.getInstance(rrd_root)
#cache = PerfDataCache.getInstance(cache_size, db_handler)

@app.route('/monitor')
def index():
    return redirect(url_for('static', filename='simple-monitor.html'))

@app.route('/monitor/json/<host>/<metric>')
def get_perf_data(host, metric):
    only_latest = False
    cf = request.args.get('cf', 'AVERAGE')
    step = request.args.get('step', 15)
    start = request.args.get('start')
    if start is None:
        #only_latest = True
        start = '-%s' % step
        end = -1
    else:
        end = request.args.get('end', -1)
    #ret = db_handler.read(str(host), str(metric), str(cf).upper(), 
                     #int(step), int(start), int(end))
    ret = get_stats(str(host), str(metric), str(cf).upper(), 
                     int(step), int(start), int(end))[1]
    #if only_latest:
        #return encode([ret[0]] + [[i for i in ret[1] if i[1] is not None][-1]])
    #else:
    return encode(ret)

mon_server_ip = '127.0.0.1'
mon_server_port = 20060
mon_server = ServerProxy('http://%s:%d'%(mon_server_ip, mon_server_port))

@app.route('/monitor/json/host-list/<hostType>')
def get_host_list(hostType):
    rc, host_list = mon_server.hostList(hostType)
    if rc == 0:
        abort(404)
    return encode(host_list)

@app.route('/monitor/json/<host>/metric-list')
def get_metric_list(host):
    rc, metric_list = mon_server.metricList(host)
    if rc == 0:
        abort(404)
    #metric = request.args.get('metric')
    #if metric is not None:
        #if '-' in metric: prefix, metric = metric.split('-')
        #for mg in metric_list:
            #for mc in mg['metrics']:
                #if mc['name'] == metric:
                    #return encode(mc)
        #abort(404)
    return encode(metric_list)


if __name__ == '__main__':
    #app.debug = True
    app.run()


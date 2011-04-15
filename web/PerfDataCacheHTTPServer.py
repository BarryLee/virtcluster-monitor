from flask import Flask, request
app = Flask(__name__)

from monserver.PerfDataCache import PerfDataCache
from monserver.RRD.RRDHandler import RRDHandler
from monserver.utils.utils import encode
from monserver.utils.load_config import load_global_config
from monserver.utils.get_logger import get_logger

logger = get_logger('PerfDataCacheHTTPServer')


config = load_global_config()
cache_size = config.get('cache_size')
rrd_root = config.get("RRD_root")

db_handler = RRDHandler.getInstance(rrd_root)
cache = PerfDataCache.getInstance(cache_size, db_handler)

@app.route('/monitor/<host>/<metric>')
@app.route('/monitor/<host>/rawdata/<metric>')
def get_stats(host, metric):
    only_latest = False
    cf = request.args.get('cf', 'AVERAGE')
    step = request.args.get('step', 15)
    start = request.args.get('start')
    if start is None:
        only_latest = True
        start = '-%s' % step
        end = -1
    else:
        end = request.args.get('end', -1)
    ret = cache.read(str(host), str(metric), str(cf).upper(), 
                     int(step), int(start), int(end))
    if only_latest:
        return encode([ret[0]] + [[i for i in ret[1] if i[1] is not None][-1]])
    else:
        return encode(ret)


if __name__ == '__main__':
    #app.debug = True
    app.run()


import json
import sys

current_module = sys.modules[__name__]

from monserver.api import mon

def tojson(func):
    def f(*args, **kwargs):
        return json.dumps(func(*args, **kwargs))
    return f

_moretweak = ['get_stats']

for fn in mon.__all__:
    f = getattr(mon, fn)
    if fn not in _moretweak:
        f = tojson(f)
        setattr(current_module, fn, f)

__all__ = [fn for fn in mon.__all__]

def get_stats(hostId, metricName, stat="AVERAGE", step=15, \
                   startTime=None, endTime=None):
    return mon.get_stats(hostId, metricName, stat, step, startTime, endTime)[1]


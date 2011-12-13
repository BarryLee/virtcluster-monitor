import json
import sys

current_module = sys.modules[__name__]

from monserver.api import mon

def tojson(func):
    def f(*args, **kwargs):
        return json.dumps(func(*args, **kwargs))
    return f

_nojson = ['get_stats']

for fn in mon.__all__:
    f = getattr(mon, fn)
    if fn not in _nojson:
        f = tojson(f)
    setattr(current_module, fn, f)

__all__ = [fn for fn in mon.__all__]


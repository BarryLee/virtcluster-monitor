
import json
import logging

from Threshold import Threshold, CompositeThreshold

logger = logging.getLogger('threshold')

def set_threshold(threshold_specs):
    """set a threshold.
    thresold_specs example:
    { 'hid': 'localhost', # host id
      'threshold': (      # a tuple of thresholds on metrics
        ('cpu_usage', 80, 0), # format: ('metric_name', threshold_value, threshold_type), for threshold_type, 0 refers to upper bound, 1 refers to lower bound
        ('r/s', 400, 0)
      ),
      'win_size': 60, # window size, in seconds
      'sample_interval': 60,     # sample interval, in seconds
      'stats': 'AVERAGE'  # supports AVERAGE, MAX or MIN
    }
    """
    try:
        ts = json.loads(threshold_specs)
        hid = ts['hid']
        threshold = ts['threshold']
    except ValueError, e:
        logger.error('invalid threshold_specs format: %s' % threshold_specs)
        return 1
    except KeyError, e:
        logger.exception('invalid threshold_specs format: %s' % threshold_specs)
        return 2

    if len(threshold) > 1:
        for t in threshold:
            pass

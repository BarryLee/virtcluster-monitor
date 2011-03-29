import os
import sys
import time
import random

from monserver.RRD.RRDHandler import RRDHandler

RRD_DIR = '/tmp/rrds'
MAX_CLIENTS = 100
MAX_REQUEST = 100

test_metrics = ('cpu_usage', 'load_five', 'sdb-rps', 'cached')
test_steps = (60, 600, 3600)
test_stats = ('AVERAGE', 'MAX', 'MIN')

output_file = '/tmp/test_rrdfetch_out%d'

time_log = '/tmp/test_rrdfetch_time'
with open(time_log, 'w') as f:
    f.write('start at: %d\n' % time.time())

nc = 0
while nc < MAX_CLIENTS:
    pid = os.fork()
    if pid == 0:
        so = file(output_file % nc, 'a+')
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(so.fileno(), sys.stderr.fileno())
        print "child #%d" % nc
        p = RRDHandler.getInstance(RRD_DIR)
        nq = 0
        while nq < MAX_REQUEST:
            now = int(time.time())
            req = ('localhost', 
                 random.choice(test_metrics),
                 random.choice(test_stats),
                 random.choice(test_steps),
                 now-random.randint(600, 3600), 
                 now-random.randint(0, 600))
            print req
            print p.read(*req)
            nq += 1
            time.sleep(0.4)

        with open(time_log, 'a+') as f:
            f.write('child #%d end at: %d\n' % (nc, time.time()))
        break
    else:
        nc += 1
        time.sleep(0.1)




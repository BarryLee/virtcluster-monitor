from utils4test import *

import os
import time

import rrdtool
import rrdtool_wrapper


#rrd_file = '/tmp/rrds/cu01/cpu_usage.rrd'
#cf = 'AVERAGE'
#step = 5
#start = 1284451425 
##start = -600
#end = 1284451455

#os.system('rrdtool fetch %s %s -r %d -s %d -e %d' % (rrd_file, cf, step, start, end))
#print rrdtool.fetch(rrd_file, cf, '-r', str(step), '-s', str(start), '-e', str(end))
#print rrdtool_wrapper.rrdfetch_wrapper(rrd_file, cf, step, start, end)
#print '-----------------------------'
#os.system('rrdtool last %s' % (rrd_file,))
#last = rrdtool.last(rrd_file)
#print last
#print rrdtool.fetch(rrd_file, cf, '-r', str(step), '-s', str(int(last-step)), '-e', str(last))
#print rrdtool_wrapper.rrdfetch_wrapper(rrd_file, cf, step, last, last)
#print rrdtool_wrapper.rrdfetchlatest(rrd_file, cf, step)


class test_rrdtool_wrapper(unittest.TestCase):

    rrd1 = '/tmp/test1.rrd'
    rrd2 = '/tmp/test2.rrd'

    def test_rrdcreate(self):
        start = -600
        ttl = 3600
        ds_type = 'GAUGE'
        step = 15
        heartbeat = 2 * step
        cf_time = (step, 60)
        xff = 0.5
        DSs = [['test_gauge', ds_type, heartbeat, 'U', 'U']]
        RRAs = []
        for i in cf_time:
            for c in ('AVERAGE', 'MIN', 'MAX'):
                RRAs.append([c, xff, i/step, ttl/i])
        cmd = 'rrdtool create %s --start %s --step %s %s %s' % \
                (self.rrd1, start, step, 
                 ' '.join(['DS:%s:%s:%s:%s:%s' % tuple(ds) for ds in DSs]),
                 ' '.join(['RRA:%s:%s:%s:%s' % tuple(rra) for rra in RRAs]))
        os.system(cmd)
        rrdtool_wrapper.rrdcreate_wrapper(self.rrd2, start, step, DSs, RRAs)
        os.system('rrdtool dump %s > %s.dump' % ((self.rrd1,) * 2))
        os.system('rrdtool dump %s > %s.dump' % ((self.rrd2,) * 2))
        os.system('diff %s.dump %s.dump' % (self.rrd1, self.rrd2))

                
    def _test_rrdupdate(self):
        #start = time.time() - 120
        #for i in range(120):
            #rrdtool.update(self.rrd1, "%d:%s" % ((start + i), i))
        start = time.time() - 600 + 15
        for i in range(600/15):
            rrdtool.update(self.rrd1, "%d:%s" % ((start + i*15), i))


    def test_rrdfetch(self):
        self._test_rrdupdate()
        rrd_file = self.rrd1
        cf = 'AVERAGE'
        step = 60
        start = -240
        end = int(time.time())
        os.system('rrdtool fetch %s %s -r %d -s %d -e %d' % \
                  (rrd_file, cf, step, start, end))
        myprint(rrdtool.fetch(rrd_file, cf, '-r', str(step), '-s', str(start), '-e', str(end)))
        myprint(rrdtool_wrapper.rrdfetch_wrapper(rrd_file, cf, step, start, end))
        

unittest.main()

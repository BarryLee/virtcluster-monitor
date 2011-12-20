import rrdtool
import sys
import os
sys.path.append('/home/crane/monitor/center')
import rrdtool_wrapper

rrd_file = '/tmp/rrds/cu01/cpu_usage.rrd'
cf = 'AVERAGE'
step = 5
start = 1284451425 
#start = -600
end = 1284451455

os.system('rrdtool fetch %s %s -r %d -s %d -e %d' % (rrd_file, cf, step, start, end))
print rrdtool.fetch(rrd_file, cf, '-r', str(step), '-s', str(start), '-e', str(end))
print rrdtool_wrapper.rrdfetch_wrapper(rrd_file, cf, step, start, end)
print '-----------------------------'
os.system('rrdtool last %s' % (rrd_file,))
last = rrdtool.last(rrd_file)
print last
print rrdtool.fetch(rrd_file, cf, '-r', str(step), '-s', str(int(last-step)), '-e', str(last))
print rrdtool_wrapper.rrdfetch_wrapper(rrd_file, cf, step, last, last)
print rrdtool_wrapper.rrdfetchlatest(rrd_file, cf, step)

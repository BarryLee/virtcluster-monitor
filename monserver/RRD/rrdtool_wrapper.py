import rrdtool
import os

native_module = True
if not hasattr(rrdtool, 'first'):
    native_module = False
    rrdtool.first = lambda x: int(os.popen('rrdtool first %s' % x).read())


def rrdcreate_wrapper(rrd_db, start=-10, step=300, DSs=[], RRAs=[]):
    args = []
    args += ["--step", str(step)]
    args += ["--start", str(start)]

    for ds in DSs:
        args.append("DS:%s:%s:%d:%s:%s" % tuple(ds))

    for rra in RRAs:
        args.append("RRA:%s:%s:%d:%d" % tuple(rra))

    rrdtool.create(rrd_db, *args)
            

def rrdfetch_wrapper(rrd_db, cf, resolution, start=-3600, end=-1):
    # type check
    assert type(rrd_db) is str
    assert type(cf) is str
    assert type(resolution) is int
    assert type(start) is int
    assert type(end) is int
    
    assert start < end
    #print 'start is %s, end is %s' % (start, end) 

    last = rrdtool.last(rrd_db)
    first = rrdtool.first(rrd_db)

    if start < 0:
        start = last + start
    if end < 0:
        end = last + end

    if start >= last or end <= first:
        return (start, end, resolution), []

    if start < first:
        start = first
    if end > last:
        end = last

    #print start, end
    # adjust the start/end time to match the result with the args
    #start = int(start) - int(resolution)
    if not native_module: # fix for pyrrdtool package
        end = int(end) - int(resolution)        

    data = rrdtool.fetch(rrd_db, cf, "-r", str(resolution), "-e", str(end), \
                         "-s", str(start))
    #logger.debug(r'rrdtool.fetch("%s", "%s", "-r", "%s", "-e", "%s", "-s", "%s")' %\
            #(rrd_db, cf, str(resolution), str(end), str(start)))
    #print data[0]
    #return (data[0][0]+data[0][2], data[0][1], data[0][2]),\
           #data[2][0:-1]
    rstep = data[0][2]
    rstart = data[0][0] + rstep
    rend = data[0][1] - rstep   # minus rstep if we are using the native python binding
    rdata = []
    timestamp = rstart

    for d in data[2][0:-1]:
        rdata.append([timestamp, d[0]])
        timestamp += rstep

    return (rstart, rend, rstep), rdata


def rrdfetchlatest(rrd_db, cf, resolution):
    step = 5 * resolution
    end = rrdtool.last(rrd_db)
    start = end - step
    ret = rrdfetch_wrapper(rrd_db, cf, resolution, start, end) 
    vals = ret[1]
    l_ = len(vals)
    j = k = -1
    while j >= -l_:
        if vals[j][1] is not None:
            k = j
            break
        j -= 1
    return ret[0], [vals[k]]


def rrdupdate_wrapper(rrd_db, timestamp, value):
    rrdtool.update(rrd_db, "%d:%s"%(timestamp,val))


if __name__ == '__main__':
    #print rrdfetchlatest('/tmp/rrds/cu01/cpu_usage.rrd', 'AVERAGE', 3600)
    ttl = 3600 * 24
    ds_type = 'COUNTER'
    step = 15
    heartbeat = 2 * step
    cf_time = (step, 60, 600, 900, 1800, 3600)
    xff = 0.5
    DSs = [['test_counter', ds_type, heartbeat, 'U', 'U']]
    RRAs = []
    for i in cf_time:
        for c in ('AVERAGE', 'MIN', 'MAX'):
            RRAs.append([c, xff, i/step, ttl/i])

    rrdcreate_wrapper('./test/test.rrd', DSs=DSs, RRAs=RRAs)


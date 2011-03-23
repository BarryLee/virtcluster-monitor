

class PerfDataCache(object):

    def __init__(self, max_cache_size, db_handler):
        self._data_store = {}
        self.max_cache_size = max_cache_size
        self.cache_size = 0
        self.db_handler = db_handler
        self._hit = 0


    def write(self, host, name, vals):
        print host, name, vals
        #store = self._data_store
        #if not store.has_key((host, name)):
            #store[(host, name)] = [0] # number of hits and unhits

        #if type(vals) is list:
            #store[host, name].extend(vals)
            #self.cache_size += len(vals)
        #else:
            #store[host, name].append(vals)
            #self.cache_size += 1
        
        #print "%d/%d" %(self.cache_size, self.max_cache_size)
        self.db_handler.write(host, name, vals)
        #if self.cache_size >= self.max_cache_size:
            #self.rollover()
        

    def rollover(self):
        print 'out of cache!' 
        for entry, item in self._data_store.items():
            #vlen = len(vlist)-1
            #n = int((1 - float(vlist[0]) / float(self._hit+1)) * vlen)
            #del vlist[1:n+1]
            vlist = item['data']
            vlen = len(vlist)
            n = int((1 - float(item['hit'])/float(self._hit+1)) * vlen)
            del vlist[0:n]
            self.cache_size -= n


    def read(self, host, name, stat, step, start, end):

        if self.cache_size >= self.max_cache_size:
            self.rollover()

        start = int(start)
        end = int(end)
        bounds = [None, None]

        if not self._data_store.has_key((host, name, stat, step)):
            self._data_store[(host,name,stat,step)] = {"hit":0, "data":[]}

        store = self._data_store[(host,name,stat,step)]

        vlist = store["data"]
        cs = len(vlist) > 0 and vlist[0][0]-step or end
        if start < cs:
            data = self.db_handler.read(host, name, stat, step, start, cs)
            rstart = data[0][0]
            rend = data[0][1]
            if rstart > cs:
                print 'out of date'
                return data
            rdata = data[1]
            i = -1
            while True:
                if rdata[i][0] <= cs:
                    break
                i -= 1
            if i < -1:
                rdata = rdata[0:i+1]
            vlist = rdata + vlist
            store["data"] = vlist
            self.cache_size += len(rdata)

        if start <= cs:
            bounds[0] = 0

        ce = len(vlist) > 0 and vlist[-1][0]+step or start
        if end > ce:
            data = self.db_handler.read(host, name, stat, step, ce, end)
            rdata = data[1]
            i = 0
            while True:
                if rdata[i][0] >= ce:
                    break
                i += 1
            rdata = rdata[i:]
            vlist.extend(rdata)
            self.cache_size += len(rdata)

        if end >= ce:
            bounds[1] = len(vlist)-1
            
        print "%d/%d" %(self.cache_size, self.max_cache_size)
        store["hit"] += 1
        self._hit += 1

        for i in range(2):
            target = (start, end)[i]
            if bounds[i] is None:
                low = 0
                high = len(vlist) - 1
                mid = 0
                while low < high:
                    mid = (low + high) / 2
                    if vlist[mid][0] > target:
                        high = mid - 1
                    elif vlist[mid][0] < target:
                        low = mid + 1
                    elif vlist[mid][0] == target:
                        low = mid
                        break
                bounds[i] = low
        
        return (vlist[bounds[0]][0], vlist[bounds[1]][0], step), \
               vlist[bounds[0]:bounds[1]+1]


if __name__== "__main__":
    from mon_db_handler import MonDBHandler
    from time import time, sleep
    t = MonDBHandler.getInstance("/tmp")
    r = TimelyDataRWHandler(100, t)
    while True:
        for metric in ("load_one", "load_five"):#, "cpu_use_time", "cpu_total_time"):
            now = int(round(time()))
            print r.read("192.168.226.193", metric, stat="AVERAGE", step=5, \
                         end=now, start=now-60)[0]
            print r'read("192.168.226.193", "%s", "AVERAGE", 5, %d, %d)' % (metric, now, now-60)
            print metric, r._data_store["192.168.226.193",metric,"AVERAGE",5]
        sleep(10)

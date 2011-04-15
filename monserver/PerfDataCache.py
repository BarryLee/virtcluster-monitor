import threading
import time

from includes.singletonmixin import Singleton
from utils.get_logger import get_logger
from utils.utils import encode


logger = get_logger("PerfDataCache")


class PerfDataCache(Singleton):

    _lock = threading.RLock()

    def __init__(self, max_cache_size, db_handler):
        self._data_store = {}
        self.max_cache_size = max_cache_size
        self.cache_size = 0
        self.db_handler = db_handler
        self._hit = 0


    #def rollover(self, cache):
        #vlist = cache["data"]
        #vlen = len(vlist)
        #n = int((1 - float(cache["hit"])/float(self._hit+1)) * vlen)
        #del vlist[0:n]
        ##vlist = vlist[n:]
        #self._lock.acquire()
        #self.cache_size -= n
        #self._lock.release()
        #logger.info("done rollover")


    def rollover(self):
        for entry in self._data_store.keys():
            #vlen = len(vlist)-1
            #n = int((1 - float(vlist[0]) / float(self._hit+1)) * vlen)
            #del vlist[1:n+1]
            item = self._data_store[entry]
            item["lock"].acquire()
            vlist = item["data"]
            vlen = len(vlist)
            n = int((1 - float(item["hit"])/float(self._hit+1)) * vlen)
            del vlist[0:n]
            item["lock"].release()
            #vlist = vlist[n:]
            self._lock.acquire()
            self.cache_size -= n
            self._lock.release()
        logger.info("done rollover")


    def read(self, host, metric, stat, step, start, end):

        if self.cache_size >= self.max_cache_size:
            logger.warning("out of cache!")
            self.rollover()

        #start = int(start)
        #end = int(end)
        if start < 0: 
            start = int(time.time()) + start
        if end < 0:
            end = int(time.time()) + end
        logger.debug("start is %d" % start)
        logger.debug("end is %d" % end)
        bounds = [None, None]

        self._lock.acquire()
        self._data_store.setdefault((host, metric, stat, step), 
                                    {"hit":0, "data":[], "lock":threading.RLock()})
        #if not self._data_store.has_key((host, metric, stat, step)):
            #self._data_store[(host,metric,stat,step)] = {"hit":0, "data":[], "lock":threading.RLock()}
        self._lock.release()

        store = self._data_store[(host,metric,stat,step)]
        store["lock"].acquire()
        vlist = store["data"]
        logger.debug("vlist: \n%s" % (vlist,))

        # cs stands for cache start, which is the timestamp of the 1st 
        # record in cache. If cs is ahead of start, we shall 
        # retrieve records from start to cs. If there is currently no 
        # records, just retrieve data from start to end
        cs = len(vlist) > 0 and vlist[0][0] or end
        #logger.debug("cs is %s" % cs)
        if start < cs:
            # we increase the fetch range by one step otherwise no data
            # will be fetched if the range is less than one step
            data = self.db_handler.read(host, metric, stat, step, start-step, cs)
            #logger.debug("fetch from file(%s, %s, %s, %d, %d, %d): \n%s" % 
                         #(host, metric, stat, step, start, cs, data))
            rstart = data[0][0]
            rend = data[0][1]
            rdata = data[1]
            rlen = len(rdata)
            i = -1
            while -i <= rlen:
                if rdata[i][0] <= cs:
                    break
                i -= 1
            #logger.debug("%d" % i)
            if i >= -rlen:
                rdata = rdata[0:(rlen+i+1)]
                vlist = rdata + vlist
                store["data"] = vlist
                #logger.debug("vlist: \n%s" % (vlist,))
                self._lock.acquire()
                self.cache_size += rlen
                self._lock.release()

        if start <= cs:
            bounds[0] = 0

        logger.debug("vlist: \n%s" % (vlist,))
        #ce = len(vlist) > 0 and vlist[-1][0]+step or start
        ce = len(vlist) > 0 and vlist[-1][0] or start
        #logger.debug("ce is %s" % ce)
        if end > ce:
            data = self.db_handler.read(host, metric, stat, step, ce, end+step)
            #logger.debug("fetch from file(%s, %s, %s, %d, %d, %d): \n%s" % 
                         #(host, metric, stat, step, ce, end, data))
            rdata = data[1]
            i = 0
            rlen = len(rdata)
            while i < rlen:
                if rdata[i][0] >= ce:
                    break
                i += 1
            if i < rlen:
                rdata = rdata[i:]
                vlist.extend(rdata)
                #logger.debug("vlist: \n%s" % (vlist,))
                self._lock.acquire()
                self.cache_size += rlen
                self._lock.release()

        cl = len(vlist)
        if end >= ce:
            #bounds[1] = len(vlist)-1
            bounds[1] = cl - 1
            
        logger.debug("%d/%d" %(self.cache_size, self.max_cache_size))
        store["hit"] += 1
        self._lock.acquire()
        self._hit += 1
        self._lock.release()

        for i in range(2):
            target = (start, end)[i]
            if bounds[i] is None:
                low = 0
                #high = len(vlist) - 1
                high = cl - 1
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
        
        #return (vlist[bounds[0]][0], vlist[bounds[1]][0], step), \
               #vlist[bounds[0]:bounds[1]+1]
        #logger.debug("cache: \n%s" % self._data_store)
        logger.debug('vlist: %s' % vlist) 
        logger.debug('bounds: %s' % bounds)
        #ret = encode(((vlist[bounds[0]][0], vlist[bounds[1]][0], step), \
               #vlist[bounds[0]:bounds[1]+1]))
        ret = ((vlist[bounds[0]][0], vlist[bounds[1]][0], step), \
               vlist[bounds[0]:bounds[1]+1])
        #if self.cache_size >= self.max_cache_size:
            #logger.warning("out of cache!")
            #self.rollover(store)
        store["lock"].release()
        logger.debug("this cache: \n%s" % store)
        return ret


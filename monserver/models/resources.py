
from persistent import Persistent
from Relation import Relation
import ID

class ResourceBase(Persistent, Relation):

    _noexpose = ['_part_of_']

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


    def __str__(self):
        return str(self.__dict__)

    
    def info(self):
        return self._copy(self.__dict__)


    def _copy(self, d):
        ret = {}
        for k,v in d.items():
            if k in self._noexpose:
                continue
            elif isinstance(v, ResourceBase):
                v = v.info()
            elif type(v) is dict:
                v = self._copy(v)
            ret[k] = v
        return ret

    def update(self, dictattrs):
        self.__dict__.update(dictattrs)


    def hasOne(self, comp_name, comp_obj):
        self.oneToOne(comp_name, comp_obj, '_part_of_')


    def addOne(self, comp_type, comp_name, comp_obj):
        self.oneToMany(comp_type, comp_name, comp_obj, '_part_of_')
        self._p_changed = 1


class Host(ResourceBase):

    _noexpose = ['metric_list']

    def __init__(self, ip, **extrainfo):
        #self.hostname = hostname
        self.ip = ip
        #for k, v in extrainfo:
            #setattr(self, k, v)
        self.id = ID.get_id(self)
        self.rtype = self.__class__.__name__
        self.__dict__.update(extrainfo)

    def __str__(self):
        return str(self.info())

    def info(self):
        ret = self._copy(self.__dict__)
        return ret

    def _copy(self, d):
        ret = {}
        for k,v in d.items():
            if k == 'metric_list':
                continue
            elif isinstance(v, ResourceBase):
                v = v.info()
            elif type(v) is dict:
                v = self._copy(v)
            ret[k] = v
        return ret

class VM(Host): 
    pass    


class CPU(ResourceBase):
    """Fields of CPU:
        cpu_num: int
        (opt)cpu_MHz: str
    """
    pass


class Disk(ResourceBase):
    """Fields of Disk:
        name: str
        size: int (Byte)
        (opt)avail: int (Byte)
    """
    pass


class Partition(Disk):
    pass


class NetworkInterface(ResourceBase):
    pass



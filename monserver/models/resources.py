
from persistent import Persistent
from Relation import Relation
import ID

class ResourceBase(Persistent, Relation):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


    def __str__(self):
        return str(self.__dict__)


    def update(self, dictattrs):
        self.__dict__.update(dictattrs)


    def hasOne(self, comp_name, comp_obj):
        self.oneToOne(comp_name, comp_obj, '_part_of_')


    def addOne(self, comp_type, comp_name, comp_obj):
        self.oneToMany(comp_type, comp_name, comp_obj, '_part_of_')
        self._p_changed = 1


class Host(ResourceBase):


    def __init__(self, ip, **extrainfo):
        #self.hostname = hostname
        self.ip = ip
        #for k, v in extrainfo:
            #setattr(self, k, v)
        self.id = ID.get_id(self)
        self.__dict__.update(extrainfo)


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
        label: str
        size: int (Byte)
        (opt)avail: int (Byte)
    """
    pass


class Partition(Disk):
    pass


class NetworkInterface(ResourceBase):
    pass



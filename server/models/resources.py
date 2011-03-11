
from persistent import Persistent

from Relation import Relation


class ResourceBase(Persistent, Relation):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


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
        self.__dict__.update(extrainfo)


class VirtualHost(Host): 
    pass


class CPU(ResourceBase):
    pass


class Disk(ResourceBase):
    pass


class Partition(ResourceBase):
    pass


class NetworkInterface(ResourceBase):
    pass



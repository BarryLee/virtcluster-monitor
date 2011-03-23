#from persistent import Persistent

from ComponentBase import ComponentBase


class Host(ComponentBase):


    def __init__(self, ip, **extrainfo):
        #self.hostname = hostname
        self.ip = ip
        #for k, v in extrainfo:
            #setattr(self, k, v)
        self.__dict__.update(extrainfo)


class VirtualHost(Host): 
    pass

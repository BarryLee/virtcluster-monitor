from persistent import Persistent

from Relation import Relation


class Host(Persistent, Relation):

    def __init__(self, hostname, ip, **extrainfo):
        self.hostname = hostname
        self.ip = ip
        for k, v in extrainfo:
            setattr(self, k, v)



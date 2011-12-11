from monserver.event.Event import *

__all__ = ['HostInactive']

class HostInactive(Event):

    def __init__(self, hostId, ip, **econtent):
        super(HostInactive, self).__init__(hostId, 
                                           'HostInactive',
                                           None,
                                           ip=ip,
                                           **econtent)
        self.msg = "Host %s(%s) state changed to inactive" % (self.target, self.ip)


class HostDel(Event):

    def __init__(self, hostId, **econtent):
        super(HostDel, self).__init__(hostId,
                                      'HostDel',
                                      None,
                                      **econtent)
        self.msg = "Host %s deleted" % (self.target,)

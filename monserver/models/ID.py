
import logging
import socket
import resources
from monserver.VIMBroker import VIM

logger = logging.getLogger('monserver.models.ID')

def host_id(ip):
    """use hostname as host's id"""
    hostname = ''
    try:
        host = socket.gethostbyaddr(ip)
        if len(host[1]) > 0:
            hostname = host[1][0]
        else:
            hostname = host[0]
    except socket.herror:
        hostname = ip
    return hostname

def vm_id(ip):
    """Get vm' id from VIM, otherwise use its ip.
    """
    vmid = getvmidbyip(ip)
    if vmid is not None:
        return vmid
    else:
        logger.info('unmanaged vm %s' % ip)
        return ip

def get_id(hostobj):
    if isinstance(hostobj, resources.Host):
        return host_id(hostobj.ip)
    elif isinstance(hostobj, resources.VM):
        return vm_id(hostobj.ip)
    else:
        raise Exception, 'unknown host type: %s' % type(hostobj)


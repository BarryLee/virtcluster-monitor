import logging

import cloud

from exceptions import VIMException

logger = logging.getLogger('monserver.VIM.crane')

def get_vms_info():
    state, vmsinfo = cloud.get_vms_info(-2, 0)
    if not state:
        raise VIMException, '%s' % ([state, vmsinfo])
    return vmsinfo

def get_vm_info(vmid):
    vmsinfo = get_vms_info()
    for vminfo in vmsinfo:
        if vminfo['guid'] == vmid:
            return vminfo
    return None

def getvminfobyip(ip):
    suc, vmsinfo = cloud.get_vms_info(-2, 0)
    if not suc:
        logger.error('call vim error: %s' % vmsinfo)
        return None
    for vminfo in vmsinfo:
        if vminfo['ip'] == ip:
            return vminfo
    return None

def getvmidbyip(ip):
    vminfo = getvminfobyip(ip)
    if vminfo is not None and vminfo.has_key('guid'):
        return vminfo['guid']
    else:
        return None

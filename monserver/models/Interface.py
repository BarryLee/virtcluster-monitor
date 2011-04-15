import os.path
import sys
import time

###############################################################
# temporary solution for importing upper level modules/packages
_ = lambda f: os.path.dirname(os.path.abspath(f))

par_dir = _(_(__file__))
if par_dir not in sys.path:
    sys.path.append(par_dir)
###############################################################

from ModelDB import ModelDB, ModelDBSession
from resources import Host, VirtualHost, CPU, Disk, Partition, NetworkInterface
import ID
from utils.load_config import load_config
from utils.utils import decode
from utils.get_logger import get_logger

logger = get_logger("models.interface")

#config = load_config()
cur_dir = _(__file__)


def sign_in_handler(ip, info):
    interface = Interface()
    interface.signIn(ip, info)
    interface.close()


def host_metric_conf(host_id):
    interface = Interface()
    ret = interface.hostMetricConf(host_id)
    interface.close()
    return ret


def check_alive(timeout):
    interface = Interface()
    interface.checkAlive(timeout)
    interface.close()


def check_expire(expire_time):
    interface = Interface()
    interface.checkExpire("Host", expire_time)
    interface.checkExpire("VirtualHost", expire_time)
    interface.close()


def getidbyip(ip):
    interface = Interface()
    ret = interface.getActiveHost(ip)
    interface.close()
    return ret
    

class Interface(object):

    DB_CONFIG_URL = cur_dir + os.path.sep + "modelstore.conf"

    def __init__(self):
        self.modeldb = ModelDB.getInstance(self.DB_CONFIG_URL)
        self.open()


    def open(self):
        self.session = self.modeldb.openSession()


    def close(self):
        self.session.commit()
        self.session.close()


    def signIn(self, ip, info):
        is_virtual = info.get("virtual")
        virt_type = info.get("virt_type")

        if not is_virtual:
            id = ID.host_id_gen(ip)
            host_type = "Host"

        session = self.session
        #host = session.getResource(host_type, id)
        host = session.getResource("all", id)
        if host is None:
            host = Host(ip)
            host.id = id
        else:
            logger.debug("retrieve object %s from db" % host)

        host.is_virtual = is_virtual
        host.virt_type = virt_type
        host.ip = ip

        components = info.get("components")

        cpuinfo = components.get("cpu")
        cpu = CPU(**cpuinfo)
        host.hasOne("cpu", cpu)

        disksinfo = components.get("filesystem")["local"]
        for dn, di in disksinfo.iteritems():
            if di.has_key("disk"):

                diskname = di.get("disk")
                diskinfo = disksinfo.get(diskname)
                disk = Disk(**diskinfo)
                disk.update({"name": diskname})
                
                partition = Partition(**di)
                partition.update({"name": dn})

                disk.addOne("partitions", dn, partition)
                host.addOne("disks", diskname, disk)
            else:
                continue

        meminfo = components.get("memory")
        host.update(meminfo)

        ifsinfo = components.get("network")
        for ifn, ifi in ifsinfo.iteritems():
            if ifn not in ("lo",):
                network_interface = NetworkInterface(**ifi)
                network_interface.update({"name": ifn})
                host.addOne("network_interfaces", ifn, network_interface)

        host.metric_list = info["metric_groups"]

        host.last_arrival = time.time()

        session.setResource("all", host.id, host)
        session.setResource(host.__class__.__name__, host.id, host)
        session.setResource("active", host.ip, host)
        #session.root._p_changed = 1
        session.commit()
        logger.info("%s(%s) signed in" % (host.id, host.ip))
        

    def hostMetricConf(self, host_id):
        session = self.session
        
        host_obj = session.getResource("all", host_id)
        assert host_obj is not None
        return host_obj.metric_list


    def getActiveHost(self, ip):
        session = self.session
        host_obj = session.getResource("active", ip)
        return host_obj


    def getIDByIP(self, ip):
        return self.getActiveHost(ip).id

            
    def setLastArrival(self, ip, timestamp):
        self.getActiveHost(ip).last_arrival = timestamp

    
    def checkAlive(self, timeout):
        active_hosts = self.session.root.get("active", None)
        if active_hosts is None:
            return
        #active_hosts = self.session.root.get("active", {})
        #logger.debug(list(active_hosts.keys())) 
        #logger.debug(list(self.session.root.get("all", {}).keys()))
        #logger.debug(list(self.session.root.get("Host", {}).keys()))
        now = time.time()
        toberemoved = []
        for ip, host_obj in active_hosts.iteritems():
            logger.debug("%d, %d, %d" % (now, host_obj.last_arrival, timeout))
            if now - host_obj.last_arrival > timeout:
                toberemoved.append(ip)
        if len(toberemoved):
            for ip in toberemoved:
                host_obj = active_hosts.pop(ip)
                logger.warning("""no msg from %s(%s) for more than %d seconds,\
remove it from session""" % (host_obj.id, ip, timeout))
            self.session.commit()                           


    def delHost(self, host_type, host_id):
        self.session.delResource(host_type, host_id)
        self.session.delResource("all", host_id)
        self.session.commit()


    def checkExpire(self, host_type, expire_time):
        hosts = self.session.root.get(host_type, None)
        if hosts is None:
            return
        now = time.time()
        toberemoved = []

        for id, host in hosts.iteritems():
            if now - host.last_arrival > expire_time:
                toberemoved.append(id)

        if len(toberemoved):
            for id in toberemoved:
                self.delHost(host_type, id)
                logger.info("record %s:%s expired and deleted" 
                            % (host_type, id))




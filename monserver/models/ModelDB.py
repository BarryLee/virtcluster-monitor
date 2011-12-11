import ZODB.config
import transaction
from BTrees.OOBTree import OOBTree

from monserver.includes.singletonmixin import Singleton
#from utils.utils import put_to_dict


class ModelDBException(Exception):
    """errno:
        0 -- undefined
        1 -- no such record
    """
    def __init__(self, errmsg, errno=0):
        super(ModelDBException, self).__init__(errmsg, errno)
        self.errmsg = errmsg
        self.errno = errno


class ModelDB(Singleton):


    def __init__(self, dbconfigurl):
        self._config_url = dbconfigurl
        self._opened = 0
        #self.db = ZODB.config.databaseFromURL(dbconfigurl)
        self.open()
        #conn = self._db.open()
        #root = conn.root()
        #if not root.has_key("all"):
            #root["all"] = OOBTree()
            #self.commit()
        #conn.close()
        #print "__init__() called"


    #def commit(self):
        #transaction.commit()


    def getConnection(self):
        return self._db.open()


    def openSession(self):
        return ModelDBSession(self)


    def open(self):
        self._db = ZODB.config.databaseFromURL(self._config_url)
        conn = self._db.open()
        root = conn.root()
        if not root.has_key("all"):
            root["all"] = OOBTree()
            transaction.commit()
        self._opened = 1


    def close(self):
        self._db.close()
        self._opened = 0



class ModelDBSession(object):

    def __init__(self, modeldbobj):
        #self.modeldb = ModelDB.getInstance(dbconfigurl)
        self.modeldb = modeldbobj
        self.connection = self.modeldb.getConnection()
        #self.root = self.connection.root().get("all")
        self.root = self.connection.root()
        self.trans = transaction.get()

    def hasResource(self, res_key):
        return self.root['all'].has_key(res_key)

    def addResource(self, res_type, res_key, obj):
        if not self.root.has_key(res_type):
            self.root[res_type] = OOBTree()

        self.root[res_type][res_key] = obj
        #self.root[res_type]._p_changed = 1


    def getResource(self, res_type, res_key=None):
        try:
            if res_key is None:
                return self.root[res_type]
            else:
                return self.root[res_type][res_key]
        except KeyError, e:
            #return None
            raise ModelDBException("no resource has key %s" % e.args[0], 1)


    def delResource(self, res_type, res_key):
        try:
            self.root[res_type].pop(res_key)
        except KeyError, e:
            raise ModelDBException("no resource has key %s" % e.args[0], 1)


    def commit(self):
        self.trans.commit()

    def abort(self):
        self.trans.abort()

    def close(self):
        self.connection.close()
        #del self.root




import ZODB.config
import transaction
from BTrees.OOBTree import OOBTree

from singletonmixin import Singleton
#from utils.utils import put_to_dict


class ModelDBException(Exception):
    pass


class ModelDB(Singleton):


    def __init__(self, dbconfigurl):
        self._config_url = dbconfigurl
        self._opened = 0
        #self.db = ZODB.config.databaseFromURL(dbconfigurl)
        self.open()
        #conn = self._db.open()
        #root = conn.root()
        #if not root.has_key('all'):
            #root['all'] = OOBTree()
            #self.commit()
        #conn.close()
        #print '__init__() called'


    def commit(self):
        transaction.commit()


    def getConnection(self):
        return self._db.open()


    def openSession(self):
        return ModelDBSession(self)


    def open(self):
        self._db = ZODB.config.databaseFromURL(self._config_url)
        self._opened = 1


    def close(self):
        self._db.close()
        self._opened = 0



class ModelDBSession(object):

    def __init__(self, modeldbobj):
        #self.modeldb = ModelDB.getInstance(dbconfigurl)
        self.modeldb = modeldbobj
        self.connection = self.modeldb.getConnection()
        #self.root = self.connection.root().get('all')
        self.root = self.connection.root()
        

    def addResource(self, res_type, res_key, obj):
        if not self.root.has_key(res_type):
            self.root[res_type] = OOBTree()

        self.root[res_type][res_key] = obj


    def removeResource(self, res_type, res_key):
        try:
            self.root[res_type].pop(res_key)
        except KeyError, e:
            raise ModelDBException


    def commit(self):
        transaction.commit()


    def close(self):
        self.connection.close()
        self.root = None




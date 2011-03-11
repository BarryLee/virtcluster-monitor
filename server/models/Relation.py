
from utils.get_logger import get_logger

logger = get_logger('models.Relation')


class Relation(object):

    def oneToOne(self, field, obj, foreign_field):
        #logger.debug('%s\n%s\n%s\n%s' % (self, field, obj, foreign_field))
        setattr(obj, foreign_field, self)
        setattr(self, field, obj)


    def oneToMany(self, field, key, obj, foreign_field):
        #logger.debug('%s\n%s\n%s\n%s' % (self, field, obj, foreign_field))
        setattr(obj, foreign_field, self)
        if not hasattr(self, field):
            setattr(self, field, dict())
        #getattr(self, field).append(obj)
        getattr(self, field)[key] = obj


    def manyToMany(self, field, key, obj, foreign_field, foreign_key):
        #logger.debug('%s\n%s\n%s\n%s' % (self, field, obj, foreign_field))
        if not hasattr(obj, foreign_field):
            setattr(obj, foreign_field, dict())
        #getattr(obj, foreign_field).append(self)
        getattr(obj, foreign_field)[foreign_key] = self
        if not hasattr(self, field):
            setattr(self, field, dict())
        getattr(self, field)[key] = obj


    def manyToOne(self, field, obj, foreign_field, foreign_key):
        #logger.debug('%s\n%s\n%s\n%s' % (self, field, obj, foreign_field))
        if not hasattr(obj, foreign_field):
            setattr(obj, foreign_field, dict())
        getattr(obj, foreign_field)[foreign_key] = self
        setattr(self, field, obj)




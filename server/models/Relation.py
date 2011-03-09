

class Relation(object):

    def oneToOne(self, link, obj, backlink):
        setattr(obj, backlink, self)
        setattr(self, link, obj)


    def oneToMany(self, link, obj, backlink):
        setattr(obj, backlink, self)
        if not hasattr(self, link):
            setattr(self, link. list())
        getattr(self, link).append(obj)


    def manyToMany(self, link, obj, backlink):
        if not hasattr(obj, backlink):
            setattr(obj, backlink, list())
        getattr(obj, backlink).append(self)
        if not hasattr(self, link):
            setattr(self, link. list())
        getattr(self, link).append(obj)


    def manyToOne(self, link, obj, backlink):
        if not hasattr(obj, backlink):
            setattr(obj, backlink, list())
        getattr(obj, backlink).append(self)
        setattr(self, link, obj)




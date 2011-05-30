from persistent import Persistent


class Component(Persistent, Relation):

    def hasOne(self, comp_name, comp_obj):
        self.oneToOne(comp_name, comp_obj, '_belong_to_')


    def addOne(self, comp_type, comp_obj):
        self.oneToMany(comp_type, comp_obj, '_belong_to_')
        self._p_changed = 1

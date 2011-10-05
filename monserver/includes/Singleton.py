#import sys
#sys.path.append('/home/drli/code/vnix_2.0/vnix_daemon/')
#import vnixbase

class MetaSingleton(type):
    """Singleton Metaclass"""

    def __init__(cls, name, bases, dic):
        super(MetaSingleton, cls).__init__(name, bases, dic)
        cls.__instance = None

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(MetaSingleton, cls).__call__(*args, **kwargs)
        return cls.__instance


class Singleton(object):

    _instance = None

    def __init__(self):
        print '__init__ called'

    def __new__(cls, *args, **kargs):
        print '__new__ called'
        return cls._getInstance(*args, **kargs)

    @classmethod
    def _getInstance(cls, *args, **kargs):
        # Check to see if a __single exists already for this class
        # Compare class types instead of just looking for None so
        # that subclasses will create their own __single objects
        if type(cls._instance) is not cls:
        #if cls._instance is None:
            cls._instance = object.__new__(cls)
            cls._instance.init(*args, **kargs)
        else:
            print "only 1 instance can be instanciated"
        return cls._instance

    def spam(self):
        return id(self)

    def init(self, *args, **kargs):
        """may be overriden.
        """
        pass


class MetaSingleton2(type):

    def __call__(cls, *args, **kwargs):
        print 'meta class invoked!'
        if type(cls._instance) is not cls:
            print 'instansiating...'
            cls._instance = super(MetaSingleton2, cls).__call__(*args, **kwargs)
        return cls._instance


class Singleton2(object):

    __metaclass__ = MetaSingleton2

    _instance = None

    def __new__(cls, *args, **kwargs):
        print '__new__ called'
        return object.__new__(cls)

    def __call__(cls, *args, **kwargs):
        print '__call__ called'
        return super(Singleton2, cls).__call__(*args, **kwargs)

    def __init__(self, i):
        self.i = i

    def spam(self):
        return id(self)


class MySingleton(Singleton2):

    #_instance = None
    __private = "private"

    def __init__(self, *name):
        try:
            self.nameMe(name[0])
        except:
            print "I was born with no name"

    def init(self, real_name):
        self.real_name = real_name
   
    def nameMe(self, name):
        print 'you named me', name
        self.name = name

    def sayHi(self):
        print "Hi! I'm %s" % self.name

    def confess(self):
        print "okay, my real name is %s" % self.real_name


class MyAnotherSingleton(object):

    __metaclass__ = MetaSingleton

    def __init__(self, *name):
        try:
            self.nameMe(name[0])
        except:
            print "I was born with no name"

    def nameMe(self, name):
        print 'you named me', name
        self.name = name

    def sayHi(self):
        print "Hi! I'm %s" % self.name
   


if __name__ == '__main__':
    s1 = Singleton()
    s2 = Singleton()
    print s1.spam(), s2.spam()
    ms1 = MySingleton("Kobe")
    ms2 = MySingleton()
    print ms1.spam(), ms2.spam()
    print id(s1._instance), id(ms1._instance)
    #ms1.sayHi()
    #ms2.sayHi()
    #ms1.nameMe("Jordan")
    #ms1.sayHi()
    #ms2.sayHi()
    #ms3 = MyAnotherSingleton()
    #ms3.nameMe("Allen")
    #ms4 = MyAnotherSingleton()
    #ms4.nameMe("Steve")
    #ms3.sayHi()
    #ms4.sayHi()
    #print ms1._MySingleton__private

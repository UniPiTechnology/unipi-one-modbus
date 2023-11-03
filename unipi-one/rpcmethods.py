import logging
import re
#from future.utils import iteritems
import asyncio


class DevList(dict):
    """ modified dictionary 
        - return None if index is unknown
        - key can be number - converted to string
        - add - insert device with key
    """

    def __init__(self, name, methods=None):
        super().__init__()
        self.name = name
        self.methods = methods

    def __getitem__(self, key):
        return super().get(str(key), None)

    def __setitem__(self, key, val):
        return super().__setitem__(str(key), val)

    def __contains__(self,key):
        return super().__contains__(str(key))

    def add(self, key, value):
        if str(key) in self:
            raise Exception(f'Duplicate node name "{self.name}"')
        return super().__setitem__(str(key), val)

    def addMethods(self):
        if self.methods: self.methods(self)


class DevListFactory:

    list_of_devlist = {}

    def __call__(self, name):
        try:
            return self.list_of_devlist[name]
        except KeyError:
            d = DevList(name)
            self.list_of_devlist[name] = d
            return d

class UnitList(list):

    def by_name(self, name):
        return next(filter(lambda x: hasattr(x,'name') and x.name==name, iter(self)),None)

    def add(self, obj):
        name = getattr(obj, 'name', None)
        if name and self.by_name(name):
            raise Exception(f'Duplicate node name "{self.name}"')
        self.append(obj)


DevListFactory=DevListFactory()
Units = UnitList()   #DevListFactory('__all__')

# modify class to:
#    -- create DevList with name of class or __devname__
#    -- during instance __init__ do automatic registration to DevList and Units with key self.circuit

class DevMeta(type):

    def __init__(cls, clsname, parents, props):
        fun = props['__init__'] if '__init__' in props else None
        def init_decorator_devlist(self,*fargs, **kwargs):
            if fun: fun(self,*fargs, **kwargs)
            self.__devlist__.add(self.circuit, self)
            Units.add(self)

        def init_decorator(self,*fargs, **kwargs):
            if fun: fun(self,*fargs, **kwargs)
            Units.add(self)

        if '__devname__' in props:
            devname = props['__devname__']
            setattr(cls, '__devlist__', DevListFactory(devname))
            setattr(cls,'__init__',init_decorator_devlist)
        else:
            setattr(cls,'__init__',init_decorator)

    def __getitem__(cls, key):
        return cls.__devlist__[key]


def check_dev_type(devname, reqclass, unitname, parameter):
    if isinstance(devname,reqclass):
        return devname

    device = Units.by_name(devname)
    if not device:
        logging.critical("%s has unknown %s = %s", unitname, parameter, devname)
    elif not isinstance(device,reqclass):
        logging.critical("%s - %s = %s is not an %s", unitname, parameter, devname, reqclass.__name__)
    else:
        return device
    return None


def parse_name(name):
    res = re.search('^(.*\D)(\d+)$', name)
    if res: return res.group(2)
    return None


def None_or_int(s):
    return s if s is None else int(s)

def split_by_semicolon(s):
    return [ k.strip() for k in s.split(';')]

def split_by_any(s):
    return [ k.strip() for k in re.split('\s*[\s,;]\s*',s)]

def get_kwargs(Foptions, Node, channel=None):
    kwargs = {}
    for name, option in Foptions.items():
        if 'default' in option:
            val = Node.get(name, option['default'])
        else:
            if channel and name == 'channel' : 
                val = Node.get(name, channel)
            else:
                val = Node[name]

        if 'types' in option:
            if not(type(val) in (list, tuple)): val = (val,)
            mytype = option['types']
            conv = option.get('conv', mytype) if mytype!='node' else lambda x:x
            val = [ conv(v) for v in val ]

        elif 'type' in option:
            mytype = option['type']
            conv = option.get('conv', mytype) if mytype!='node' else lambda x:x
            val = conv(val)
            #if mytype != 'node' and (type(val) != mytype):
            #    try:
            #        val =  option['conv'](val)
            #    except KeyError:
            #        val = mytype(val)

        kwargs[name] = val
    return kwargs

IN = 0
OUT = 1
R_OFF = 0
R_ON = 1
RISING = 31
FALLING = 32
BOTH = 33

'''
        PROTOTYPES of some common devices
'''
class gpin(object):
    pass

class gpout(object):
    pass

class gpiochip(object):
    pass

class Thermometer(object):
    pass

class StringGenerator(object):
    pass

class CoilProvider(object):
    pass

class RegisterProvider(object):
    pass

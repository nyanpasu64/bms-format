import logging
import re

from utils.classes import AttrDict

LEVEL = logging.INFO


# https://stackoverflow.com/a/7622029/2683842
def get_logger(name='root'):
    formatter = logging.Formatter(fmt='%(levelname)s - %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(LEVEL)
    logger.addHandler(handler)
    return logger


LOG = get_logger()


def b2h(byte):
    return '0x%02X' % byte


#### Func utils...

def mapf(fun, it):
    return type(it)(map(fun, it))


def curry(x, argc=None):
    if argc is None:
        argc = x.__code__.co_argcount
    def p(*a):
        if len(a) == argc:
            return x(*a)
        def q(*b):
            return x(*(a + b))
        return curry(q, argc - len(a))
    return p


#### Dict utils...

def without(d: dict, key):
    return {k:v for k,v in d.items() if k != key}


def no_underscore(d):
    return {k:v for k,v in d.items() if k[0] != '_'}


def dict_invert(d: dict):
    return {v:k for k,v in d.items()}


#### Dict constructors...

def dictify(**kwargs):
    return kwargs


def dict_from(root, **kwargs):
    """ a, b=x, c=y -> {a.b:x, a.c:y} """
    return {getattr(root, k): v for k, v in kwargs.items()}


# Numpy array operations

# def minus(a, b):
#     return a & ~b



first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')
def uncamel(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


# **** Closure introspection hack

# def contents(f):
#     return AttrDict({k: v.cell_contents for k,v in zip(f.__code__.co_freevars, f.__closure__)})




def getname(obj: object):
    return type(obj).__name__

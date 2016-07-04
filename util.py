import logging

LEVEL = logging.WARNING


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

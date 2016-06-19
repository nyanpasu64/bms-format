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


class AttrDict(dict):
    def __init__(self, seq={}, **kwargs):
        """
        dict() -> new empty dictionary
        dict(mapping) -> new dictionary initialized from a mapping object's
            (key, value) pairs
        dict(iterable) -> new dictionary initialized as if via:
            d = {}
            for k, v in iterable:
                d[k] = v
        dict(**kwargs) -> new dictionary initialized with the name=value pairs
            in the keyword argument list.  For example:  dict(one=1, two=2)
        # (copied from class doc)
        """
        super().__init__(seq, **kwargs)
        self.__dict__ = self


def b2h(byte):
    return '0x%02X' % byte


def without(d: dict, key):
    return {k:v for k,v in d.items() if k != key}


def dict_invert(d: dict):
    return {v:k for k,v in d.items()}


def dictify(root, **kwargs):
    return kwargs


def dict_from(root, **kwargs):
    """ a, b=x, c=y -> {a.b:x, a.c:y} """
    return {getattr(root, k): v for k, v in kwargs.items()}

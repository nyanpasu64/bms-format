import logging


LEVEL = logging.DEBUG

# https://stackoverflow.com/a/7622029/2683842
def get_logger(name='root'):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(LEVEL)
    logger.addHandler(handler)
    return logger


LOGGER = get_logger()


# This function is cleverly designed, such that `a[,b] = LOG(x[,y])`.
# NOT ANYMORE

def LOG(*args):
    ''' value text text ... '''
    LOGGER.debug(' '.join(args[1:] + args[0:1]))

    # if len(args) == 0:
    #     return None
    # elif len(args) == 1:
    #     return args[0]
    # else:
    #     return args

    return args[0]


# logger.debug('main message')


class AttrDict(dict):
    def __init__(self, seq=None, **kwargs):
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
        super(self.__class__, self).__init__(seq, **kwargs)
        self.__dict__ = self

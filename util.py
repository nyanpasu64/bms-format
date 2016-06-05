import json
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


# This function is cleverly designed, such that `a[,b] = LOG(x[,y])`.
# NOT ANYMORE

# def LOG(*args):
#     ''' value text text ... '''
#     LOGGER.debug(' '.join(str(x) for x in args[1:] + args[0:1]))
#
#     # if len(args) == 0:
#     #     return None
#     # elif len(args) == 1:
#     #     return args[0]
#     # else:
#     #     return args
#
#     return args[0]
#
# def HEX(*args):
#     if args:
#         LOG(hex(args[0]), *args[1:])
#     else:
#         LOG()

# logger.debug('main message')


#     def __init__(self, seq=None, **kwargs):
#         """
#         dict() -> new empty dictionary
#         dict(mapping) -> new dictionary initialized from a mapping object's
#             (key, value) pairs
#         dict(iterable) -> new dictionary initialized as if via:
#             d = {}
#             for k, v in iterable:
#                 d[k] = v
#         dict(**kwargs) -> new dictionary initialized with the name=value pairs
#             in the keyword argument list.  For example:  dict(one=1, two=2)
#         # (copied from class doc)
#         """
#         super(self.__class__, self).__init__(seq, **kwargs)
#         self.__dict__ = self


def get_tree(tree: dict) -> str:
    return json.dumps(tree, sort_keys=True, indent=2)

def b2h(byte):
    return '0x%02X' % byte

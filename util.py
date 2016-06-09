import logging


LEVEL = logging.DEBUG

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


def without(dic, key):
    return {k:v for k,v in dic.items() if k != key}

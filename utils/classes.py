from collections import OrderedDict
from enum import Enum
from typing import Callable, Any
from functools import singledispatch, update_wrapper


class CC(Enum):
    VOLUME = 0
    PITCH = 1
    PAN = 2


class SeqError(ValueError):
    pass


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

class OrderedAttrDict(OrderedDict):
    def __init__(self, seq={}, **kwargs):
        super().__init__(seq, **kwargs)
        self.__dict__ = self


def methdispatch(func):
    dispatcher = singledispatch(func)

    def wrapper(*args, **kw):
        return dispatcher.dispatch(args[1].__class__)(*args, **kw)

    wrapper.register = dispatcher.register
    update_wrapper(wrapper, func)
    return wrapper



Function = Callable[..., Any]

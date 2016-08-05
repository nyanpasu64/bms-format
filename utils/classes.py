from enum import Enum
from typing import Callable, Any


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



Function = Callable[..., Any]

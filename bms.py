# @register(0xc1)
# def thread(
from collections import OrderedDict
from functools import wraps, partial
from types import MethodType
from typing import Callable, Any, Dict

from utils.pointer import Pointer

Function = Callable[..., Any]



class BmsError(Exception):
    pass



# Unbound methods.
handlers = {}    # type: Dict[int, Function]





def register(event: int):
    def _register(func:Function):
        handlers[event] = func
        return func
    return _register


# **** BEGIN EVENTS

@register(0xC1)
def call_thread(self, addr):
    with self.pushpop(addr) as ptr:
        return self.parse(ptr)

@register()


# **** BEGIN CLASS

class BmsFile:
    def __init__(self):

        # Bind methods.
        self.handlers = {}
        self._stack = []

        for event, handler in handlers.items():
            self.handlers[event] = MethodType(handler, self)

        self.output = OrderedDict()

    def load(self, data: bytes):
        self.data = data
        # TODO

    def parse(self, addr:int, depth:int):
        ptr = Pointer(self.data, addr)

        result = []

        while 1:
            # Evaluate command, and push subtrees into $result.

            ev = ptr.u8()

            if ev not in self.handlers:
                raise BmsError

            tree, stop = self.handlers[ev]()
            result.append(tree)

            if stop:
                break


    def pushpop(self, addr: int) -> Pointer:
        ptr = Pointer(addr)
        self.push(ptr)
        yield ptr

        return self.pop()

    def push(self, frame: Pointer) -> Pointer:
        self._stack.append(frame)
        return frame

    def pop(self) -> Pointer:
        return self._stack.pop()

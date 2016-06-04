# @register(0xc1)
# def thread(
from collections import OrderedDict
from functools import wraps, partial
from types import MethodType
from typing import Callable, Any, Dict
# from inspect import getouterframes, currentframe
# level = len(getouterframes(currentframe(1)))

import sys

from util import LOG, HEX
from utils.pointer import Pointer

Function = Callable[..., Any]



class BmsError(Exception):
    pass


#
# # Unbound methods.
# handlers = {}    # type: Dict[int, Function]
#
#
#
#
#
# def register(event: int):
#     def _register(func:Function):
#         handlers[event] = func
#         return func
#     return _register
#
#
# # **** BEGIN EVENTS
#
# @register(0xC1)
# def call_thread(self, addr):
#     with self.pushpop(addr) as ptr:
#         return self.parse(ptr)
#
# @register()


# **** BEGIN CLASS

class BmsFile:
    def __init__(self):

        # Bind methods.
        self.handlers = {}
        self._stack = []

        self.output = {}

        # TODO: BmsFile.output = parse()
        # versus BmsTrack: BmsFile[] = result
        # OrderedDict()

    def load(self, data: bytes):
        self.data = data

        track = BmsTrack(data).parse(0)
        self.output[-1] = track

        return self.output

    def pushpop(self, addr: int) -> Pointer:
        ptr = Pointer(self.data, addr)
        self.push(ptr)
        yield ptr

        return self.pop()

    def push(self, frame: Pointer) -> Pointer:
        self._stack.append(frame)
        return frame

    def pop(self) -> Pointer:
        return self._stack.pop()


class BmsTrack(dict):
    def __init__(self, data: bytes):
        super().__init__()
        self.data = data
        self['type'] = 'track'

    def parse(self, addr):

        ptr = Pointer(self.data, addr)

        result = []
        self['track'] = result

        while 1:
            # Evaluate command, and push subtrees into $result.

            ev = ptr.u8()
            HEX(ev, 'ev')

            if ev == 0xC1:
                kwargs = {
                    'tracknum': ptr.u8(),
                    'addr': ptr.u24()
                }
                result.append(kwargs)


            break
            # result.append(tree)
            #
            # if stop:
            #     break

        return self


def main():
    argv = sys.argv

    with open(argv[1], 'rb') as f:
        data = f.read()
        tree = BmsFile().load(data)

        print(tree)

if __name__ == '__main__':
    main()

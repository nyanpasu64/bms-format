from typing import List, Dict

from util import uncamel, getname, curry
from utils.pointer import Pointer, int2bytes, byte_aligned

ENDIAN = False  # TODO configurable default endian


class ParseError(ValueError):
    pass


# Old proposal: Each struct is bound to multiple ops.
# New proposal: @register(number) once per struct.
# class StructType:
#     if 0:
#         op = None
#         default = None
#
#         struct = []
#
#     def expand(self):
#         self.op = self.default
#         raise NotImplementedError
#
#         # <convert stuff here...>


class Field:

    if 0:
        name = None
        type = None

    def parse(self, ptr: Pointer):
        # todo: move out of ptr?
        return getattr(ptr, self.type)()

    def bin(self, value):
        # todo: use ptr for endian?
        raise NotImplementedError


class _Number(Field):
    def __init__(self, name: str, bits: int, signed: bool, endian=False):
        self.name = name
        self.type = 'us'[int(signed)] + str(bits)  # because screw strong typing

        byte_aligned(bits)
        self.bits = bits
        self.endian = endian

        max_unsigned = 2 ** bits

        if signed:
            unrange = max_unsigned // 2
            self.minval = -unrange
            self.maxval = unrange

        else:
            self.minval = 0
            self.maxval = max_unsigned

    def bin(self, value):
        if value not in range(self.minval, self.maxval):
            raise ParseError(
                '%s (%s) does not fit in %s' % (value, hex(value), self.type)
            )

        if int(value) != value:
            raise ParseError('%s is not an integer' % value)

        return int2bytes(value, self.bits, self.endian)


def get_number(bits: int, signed: bool, endian=False):
    def _get_number(name: str = None):
        return _Number(name, bits, signed, endian)
    return _get_number


"""

namef = lambda signed, bits: 'us'[int(signed)] + str(bits)
for signed in range(False, True+1):
    for bits in range(8, 32+1, 8):
        name = namef(signed, bits)
        print('%s = get_number(%s, signed=%s, endian=ENDIAN)' % (name, bits, bool(signed)))
    print()

"""

# type: _Number

u8 = get_number(8, signed=False, endian=ENDIAN)
u16 = get_number(16, signed=False, endian=ENDIAN)
u24 = get_number(24, signed=False, endian=ENDIAN)
u32 = get_number(32, signed=False, endian=ENDIAN)

s8 = get_number(8, signed=True, endian=ENDIAN)
s16 = get_number(16, signed=True, endian=ENDIAN)
s24 = get_number(24, signed=True, endian=ENDIAN)
s32 = get_number(32, signed=True, endian=ENDIAN)


"""
u8('name')
_Number().parse(ptr) -> int

class Child(Event):
    keys = [u8('id')]
Child.parse(ptr) -> Child()

Child.bin() -> bytes()


Idea: Use Child() instance as parser.
    Should Child().parse() return an AttrDict?
    Then bin(d) switches d.op and calls Child().bin?

"""


event_map = {}    # type: Dict[int, Event]

@curry
def register(op, eclass):

    # If we register the same event to multiple hex codes,
    # it doesn't know how to bin itself.
    assert not hasattr(eclass, 'op')

    eclass.op = op
    event_map[op] = eclass
    return eclass


class Event:
    if 0:
        keys = []       # type: List[Field]
        values = {}     # type: Dict[str, int]
        op = None

    def __init__(self, ptr: Pointer):
        self.values = {field.name: field.parse(ptr) for field in self.keys}

        # Event instances currently hold data. We don't want them to parse new data.
        self.parse = None

        # TODO: Do we need self.name, or just rely on getname()?

    @classmethod
    def parse(cls, ptr: Pointer):
        return cls(ptr)

    def bin(self) -> bytes:
        """ Encodes current event to ID + fields. """

        data = bytearray()
        data += int2bytes(self.op, 8)
                # TODO u8().bin(self.op)
                # TODO u8.bin(self.op) (@classmethod u8.__call__() produces new named copy)

        for field in self.keys:
            value = self.values[field.name]
            data += field.bin(value)

        return bytes(data)


    # **** Miscellaneous functions...

    def smallsize(self):
        try:
            nbits = sum(field.bits for field in self.keys)
        except AttributeError:
            return None

        return nbits // 8

    def bigsize(self):
        return self.smallsize() + 1

    def __getattr__(self, item):
        try:
            return self.__dict__['values'][item]
        except KeyError as e:
            return AttributeError(e)


@register(0xC1)
class Child(Event):
    keys = [
        u8('tracknum'),
        u24('addr'),
    ]

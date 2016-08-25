from typing import List, Dict

import pytest

# from formats.bms import BmsTrack
# from util import dict_from
# from utils.pointer import Pointer, Visit, OverlapError, wrap

from utils.parser import *

from tests.test_pointer import ptr
assert ptr().data == bytes.fromhex('0001 7e7f 8081 feff')


def test_fields(ptr):
    something = [
        u8('zero'),
        s16('bar'),
        u24('big'),
        s16('negative'),
    ]

    assert([field.parse(ptr) for field in something] ==
           [0x00, 0x017e, 0x7f8081, 0xfeff - 0x10000])


def test_child_instance(ptr: Pointer):
    child_event = Child.parse(ptr)
    assert type(child_event) == Child

    with pytest.raises(TypeError):
        child_event.parse(ptr)

    encoded = child_event.bin()
    assert ptr.data.startswith(encoded)


# FIXME: Child() lacks event byte, breaks rebuilding. This will require redesign.
def test_child_parse(ptr: Pointer):
    child_event = Child.parse(ptr)

    assert child_event.tracknum == 0x00
    assert child_event.addr == 0x017e7f


def test_child_bin(ptr: Pointer):
    event = Child.parse(ptr)

    size = event.bigsize()
    assert size == 5    # op + u8 + u24

    output = event.bin()
    assert len(output) == size

    assert output == ptr.data[:size]

    # "after" functions?
    # TODO: getattr(self, '_' + Child.__name__)(event)



# class Child:
#     op = 0x01

"""
IDEA: Multiple decodings from one class????
    Let's say call/jump.
        Eg: `def _calljump(self, event): new track()`
        We can differentiate call vs. jump based on event.op.
    This won't work for control change (different struct types).

Events are instances of class. op is class-global.
if it's a range/lambda match, it's replaced by the instance value.
"""

"""

https://www.python.org/dev/peps/pep-0520/
http://construct.readthedocs.io/en/latest/api/core.html#construct.core.Switch

from pconstruct.big import U8

class Struct:
    pass


Construct:
_encode, _decode
struct.parse(bin) -> Container
adapter<struct>.parse(bin) -> Object

.build(object/container) -> bin

Classes are generic. Parsers are instances.
Parsing does NOT return an instance, but rather an arbitrary object.

Construct objects don't know their original type.
Normally you build() the root of an object.
    But how does the root know what type subobjects are?
One struct can get an event number, then get the contents as a function of the event.
    Enum?
    Switch?

    struct.unbin, bin

Child.unbin, bin
"""

""" CallJump: Construct-style switching based on first-byte, to generate struct? """

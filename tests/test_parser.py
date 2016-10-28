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


@pytest.fixture
def event(ptr: Pointer):
    return MockChild.parse(ptr)


def test_child_instance(event: MockChild):
    assert type(event) == MockChild
    assert event.parse is None

    with pytest.raises(AttributeError):
        print(event.nonexistent)


def test_child_parse(event: MockChild):
    assert event.tracknum == 0x00
    assert event.addr == 0x017e7f


def test_child_bin(ptr: Pointer, event: MockChild):

    # TODO: this is a MESS.
    bigsize = event.bigsize()
    smallsize = event.smallsize()
    assert bigsize == 5    # u8 op, u8 tracknum, u24 addr

    output = event.bin()
    assert len(output) == bigsize

    assert output[0] == event.op

    # Our input data skips the op byte (it's handled by switch, not Child.parse())
    # So skip the output op byte.
    assert output[1:] == ptr.data[:smallsize]

    encoded = event.bin()

    # We parse an event body, but reencode the op and body.
    nohead = encoded[1:]
    assert ptr.data.startswith(nohead)




    # "after" functions?
    # TODO: getattr(self, '_' + Child.__name__)(event)



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

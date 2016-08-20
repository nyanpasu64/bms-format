#!/usr/bin/env python3

from construct import *
from binascii import hexlify, unhexlify
import sys

print(UBInt8('op').parse(b'\x01'))

events = [
    Struct('Child',
           UBInt8('op'),
           UBInt8('tracknum'),
           UBInt24('addr')
           )
]

# I give up.
# 1. 24-bit ints missing
# 2. Construct doesn't log read/write (no Pointer functionality).


def parse(inpath):
    with open(inpath, 'rb') as f:
        data = f.read()

    body = Body.parse(data).body_item
    print(hex(body[0].something))


if __name__ == '__main__':
    parse(sys.argv[1])

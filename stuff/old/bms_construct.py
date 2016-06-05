#!/usr/bin/env python3

import click
from construct import *
from binascii import hexlify, unhexlify


class BmsError(ValueError):
    pass


def HexMagic(data):
    return Magic(unhexlify(data))


HeaderItem = Struct(
    'header_item',

    HexMagic('C1'),

    UBInt8('idx'),

    UBInt8('addr16'),
    UBInt16('addr')
)


def ctx_get_addr(ctx):
    if ctx.header_item.addr16 != 0:
        raise BmsError

    # fuck
    out = ((ctx.header_item.addr16 << 16) +
            ctx.header_item.addr)
    print(out)
    return out

# todo
BodyItem = Struct(
    'body_item',
    HeaderItem,
    Pointer(
        ctx_get_addr,
        UBInt8('something')
    ),
)


Body = Struct(
    'Body',
    GreedyRange(BodyItem)
)


@click.command()
@click.argument('inpath')
def parse(inpath):
    with open(inpath, 'rb') as f:
        data = f.read()

    body = Body.parse(data).body_item
    print(hex(body[0].something))


if __name__ == '__main__':
    parse()

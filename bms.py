#!/usr/bin/env python3

import click
from collections import OrderedDict

from typing import List

from util import LOGGER, LOG
from utils.pointer import Pointer

class BmsError(ValueError):
    pass

BmsTrack = List[List]





class BmsFile:
    def __init__(self):
        # track numbers
        self.tracks = {}
        self.pstack = []    # TODO pstack

    def parse(self, data: bytes):
        self.data = data
        self._parse(tracknum=-1, addr=0, depth=0)
        return self

    # self.stack[ptr]?
    # loop parse?
    # methods:
    #   ptr = self.top()

    def _parse(self, *, tracknum, addr, depth): # -> (int, BmsTrack):
        """ Return: something, track """
        ptr = Pointer(self.data, addr)
        # track = []
        # notes = []

        while True:
            ev = LOG(ptr.u8(), 'ev')

            # **** NEW TRACK
            # this will be split off into an outside call
            # self.notes is per-track, but not per-loop

            if ev == 0xC1:
                type = 'start'
                kwargs = {
                    'tracknum': ptr.u8(),
                    'addr': ptr.u24()
                }
                LOG(kwargs, '>')

                # self._parse(**kwargs, depth=depth+1)

            # **** END TRACK
            elif ev == 0xFF:
                break


            elif ev < 0x80:
                kwargs = {
                    'poly_id': ptr.u8(),
                    'note': ev,
                    'velocity': ptr.u8()
                }

                track.append(['note_on', note, velocity])
                notes[poly_id] = note

        self.tracks[tracknum] = track



@click.command()
@click.argument('inpath')
def parse(inpath):
    with open(inpath, 'rb') as f:
        data = f.read()


if __name__ == '__main__':
    parse()

OrderedDict()

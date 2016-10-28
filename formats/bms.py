import numpy as np
from numpy import array

from enum import Enum
from typing import Callable, Any, Union, Dict, List

from util import LOG, b2h, dict_invert, dict_from, uncamel, getname, D
from utils.classes import CC, SeqError, AttrDict, Function, OrderedAttrDict, methdispatch

from utils.parser import Event, register, \
    u8, u16, u24, u32, s8, s16, s24, s32


from utils.pointer import Pointer, OverlapError
from utils.pointer import Visit



# **** BEGIN CLASS

CC2BMS = dict_from(
    CC,
    VOLUME=0,
    PITCH=1,
    PAN=3
)   # type: Dict[CC, int]

BMS2CC = dict_invert(CC2BMS)    # type: Dict[int, CC]

# BmsTrack = None     # fixme


class EndException(Exception):
    pass


@register(0xC1)
class Child(Event):
    keys = [u8('tracknum'), u24('addr')]

    def after(self, track: BmsTrack):
        BmsTrack(track._file, self.addr, self.tracknum, None).parse()


@register(0xFF)
class EndTrack(Event):
    keys = []

    def after(self, track: BmsTrack):
        if track.tracknum is None:
            raise SeqError('end_track from function')



class _CallJump(Event):
    # TODO: keys = [u8('mode', BmsSeekMode), u24('addr')]
    keys = [u8('mode'), u24('addr')]


@register(0xC4)
class Call(_CallJump):
    def after(self, track: BmsTrack):
        addr = self.addr
        hist = track._ptr.hist(addr)

        if hist == Visit.MIDDLE:
            raise OverlapError('%s %s - middle of command' % (getname(self), hex(addr)))

        # We are either visiting NONE or BEGIN.
        # Not visited:
        #   Visit target.
        # Visited:
        # 	(addr) Check preconditions and apply postconditions.
        # 	Note that OldNote compares == None.

        if hist == Visit.NONE:
            track = BmsTrack(track._file, addr, None, track.note_history).parse()

        else:
            assert hist == Visit.BEGIN

            # **** ASSERTION ****
            # We will encounter issues if any touched notes differ from the original call.

            # TODO: We assume we're not calling into the middle of a visited section... :'(
            track = track._file.track_at[addr]

            different = (track.pre_history != track.note_history)
            if any(different & track.touched):
                LOG.error(
'''Invalid call from %06X to %06X
    new:%s
    old:%s
    out:%s
    touched:%s''', track._prev_addr, addr, track.note_history, track.pre_history, track.note_history, track.touched)

        # endif already visited

        # BMS really shouldn't be touching notes, AND leaving running notes untouched...

        if any(track.touched):
            untouched = ~track.touched
            if any(track.pre_history.astype(bool) & untouched):
                LOG.warning('Function leaves running notes untouched %s %s %s',
                            track.touched, track.pre_history, track.note_history)

        # Knowing that all "touched" entries entered identically...
        # We must apply all "touched" entries of the note history.
        track.note_history[track.touched] = track.note_history[track.touched]


@register(0xC8)
class Jump(_CallJump):
    def after(self, track: BmsTrack):
        addr = self.addr
        hist = track._ptr.hist(addr)

        if hist == Visit.MIDDLE:
            raise OverlapError('%s %s - middle of command' % (getname(self), hex(addr)))

        # We are either visiting NONE or BEGIN.
        # Visit target (if necessary), then continue.

        if hist == Visit.NONE:
            track._ptr.addr = addr
        else:
            assert hist == Visit.BEGIN


@register(0xC6)
class Pop(Event):
    keys = []
    extras = D(stop = True)

    def after(self, track: BmsTrack):
        raise EndException

@register(0xE7)
class InitTrack(Event):
    keys = [u16('unknown')]

    def after(self, track: BmsTrack):
        if self.unknown != 0:
            LOG.warning('Track init %04X != 0x0000', unknown)


# FIXME
@register(range(0, 0x80))
class NoteOn(Event):
    # todo
    pass


# ev2 refers to bank/patch.
# The chosen instrument value is variable-length.

@register(0xA4)
class InstrChange8(Event):
    keys = [u8('ev2'), u8('value')]

@register(0xAC)
class InstrChange16(Event):
    keys = [u8('ev2'), u16('value')]




# def after(self, track: BmsTrack):
# ev2 = self.ev2
#
# if ev2 == 0x20:
#     ev2 = 'bank'
# elif ev2 == 0x21:
#     ev2 = 'patch'
# else:
#     LOG.warning('[instr %s] Unknown type %02X value=%02X', b2h(ev), ev2, value)
#     ev2 = 'unknown %s' % b2h(ev2)
#
# self.ev2 = ev2
# TODO: this belongs better in some construct-switch adapter contraption.

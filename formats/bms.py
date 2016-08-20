import numpy as np
from numpy import array

from enum import Enum
from typing import Callable, Any, Union, Dict, List

from util import LOG, b2h, dict_invert, dict_from, uncamel
from utils.classes import CC, SeqError, AttrDict, Function, OrderedAttrDict, methdispatch
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


# BmsType = Enum('')



# **** EVENT CLASSES

class BmsType(AttrDict):
    """
    __init__ takes **evdata.
    from_ptr takes ptr and file:BmsFile (for new tracks).

    Automatically initializes "type" attribute based on subclass name.
    It's like structs and brace initialization in C, only worse.
    For Teh Autocompletez.
    """

    if False:
        next = 0x000001
        addr = 0x000000

    def __init__(self, **evdata):
        super().__init__(**evdata)

        cmd = uncamel(type(self).__name__)
        self.type = cmd


    @classmethod
    def from_ptr(cls, ptr: Pointer):
        raise NotImplementedError(cls.__name__)

    def after(self, file: 'BmsFile', ptr: 'BmsPointer'):
        pass

    def to_hex(self):
        raise NotImplementedError(type(self).__name__)

    def fix_pointers(self, file: 'BmsFile'):
        # TODO: fix type signature
        # We need the new addresses of all events to repoint the pointers.
        # NOT the numeric IDs (dict keys).
        # We need to store key->address data.

        pass


# TODO: Maybe we should use class decorators to define types and parsers together!

# Right now, my body methods already look like class __init__.
# We should use a classmethod for track-pointer init. Otherwise, we can no longer
# create events directly.

# VGMTrans N-SPC defines enum, builds map[ev, type], and uses a long switch.


'''
Dragon Roost:

CC.VOLUME
    value s16
- is u8, u16, s16 relative to full range, or some fixed value?
- is u8 255 louder than s16 255?

CC.PITCH
    value s16
- What is the pitch range? What units? Pitch range adjust?

CC.PAN
    value s8
- I assume BMS = +-(MIDI - 64)

TODO: Recompile to BMS.
'''

event_map = {}    # type: Dict[int, BmsType]


def register(keys: Union[int, list]):

    # should I move the list call into try?
    # do I care if list(iter) raises TypeError?

    try:
        it = iter(keys)
    except TypeError:
        values = [keys]
    else:
        values = list(it)


    def register_(cls: BmsType):
        for _value in values:
            event_map[_value] = cls
        return cls
    return register_


def get_event(ptr: Pointer) -> BmsType:
    """ Create new event from pointer. """
    ev = ptr.u8(mode=Visit.BEGIN)

    evtype = event_map[ev]

    event = evtype.from_ptr(ptr)

    return event


# **** BMS :(

class BmsFile(AttrDict):
    """
    Contains a dict of events.
    Every track needs one!
    """

    def __init__(self, data: bytes):
        super().__init__()

        self._data = data

        # "visited" = pointer tracking
        # "at" = events
        # TODO Should they be combined?
        # should Pointer know about the existence of BMS events? No?

        self._visited = [Visit.NONE] * len(data)  # type: List[Visit]
        self.at = {}  # type: Dict[int, BmsType]
        self.tracks = {}  # type: Dict[int, BmsTrack]
        self.track_at = {}  # type: Dict[int, BmsTrack]
        # self.segments = {}                          # type: Dict[int, BmsSegment]

    def parse(self):
        BmsTrack(file=self, addr=0, tracknum=-1, note_history=None).parse()

        return self


class BmsSeekMode(Enum):
    Always = 0
    Zero = 1
    NonZero = 2
    One = 3
    GreaterThan = 4
    LessThan = 5


# class BmsNames:
#     end_track = 'end_track'
#     pop = 'pop'
#     init_track = 'init_track'
#     tick_rate = 'tick_rate'
#     tempo = 'tempo'
#     note_on = 'note_on'
#     note_off = 'note_off'
#     delay = 'delay'
#     child = 'child'
#     call = 'call'
#     jump = 'jump'
#     instr = 'instr_change'
#     control_change = 'control_change'


class OldNote:
    """ This represents a stopped note in the BMS note history.
    All stopped notes are equal. """
    def __init__(self, val: int):
        self.val = val

    def __repr__(self):
        return '~%s' % self.val

    # HISTORY_MODE == 'LAZY'
    # This will not be 100% accurate if we have note repeat commands.

    # OldHistory is used for non-playing notes, so compares equal to no note.

    def __eq__(self, other):
        if isinstance(other, OldNote):
            return True

        if other is None:
            return True

        return NotImplemented

    def __ne__(self, other):
        return not self == other

    def __bool__(self):
        return False


HISTORY_MODE = ''
class BmsTrack(AttrDict):
    """
    Contains tracknum and starting address of track.
    May or may not contain segment[] of BmsType.
    """
    # BmsPointer

    # BmsFile reference
    # insert into file.tracks
    # Yes, track 0 IS used.

    def __init__(self, file: BmsFile, addr:int,
                 tracknum: Union[int, None],
                 note_history: 'Union[array[int], None]'):

        super().__init__()

        # Initialize stuff.
        self._file = file    # type: BmsFile
        self._data = file._data
        self._ptr = Pointer(self._data, addr, file._visited)


        # Insert track into file.
        if tracknum is not None:
            if tracknum in file.tracks:
                LOG.error('Duplicate track %d', tracknum)

            file.tracks[tracknum] = self

        # Insert track at address.
        file.track_at[addr] = self


        # Initialize track.
        self.type = 'track'
        self.tracknum = tracknum
        self.addr = addr
        self.segment = []       # type: List[BmsType]


        # Note history (for note_off commands)
        if note_history is None:
            self.note_history = [None] * 8
        else:
            self.note_history = note_history[:]

        self.note_history = array(self.note_history)

        # Does this track modify note_history?
        # True whenever notes are started/stopped.
        self.touched = array([False] * 8)

        '''
        In BMS, note history is preserved through function calls.
            24354 turns 1 on. Pop.
            24361 turns 2 on. 24364 turns 1 off.

        As a result, we pass self.hist to tracks.
        (Return), self.hist[:] = track.hist
        All passes are done by value. (subject to change)

        - Call a function with one set of playing notes,
        - End with another set.

        Partial solution: At each address, check preconditions (note_history) and apply postconditions.
            - If repeat_note command, then None vs. OldNote may be a problem.

        - To prevent pre_history from being modified, we must np.copy(parent note_history).

        - No function (in Dragon Roost theme) uses same note-off on multiple pitches.
        - One function (volume fadeout) was called with different running notes, but did not touch them.

        We can build a system to accommodate notes that overlap functions, and functions that don't touch notes.
        The system will reject functions that uses the same note-off on multiple pitches.

        # SIMULATION (bad)

        Every time a note_off occurs, make sure it's the same pitch.

        class RepeatTrack(BmsTrack):
            def i(): pass
            def note_off():
                bms_assert(at[].note == current note)


        # ASSERTION

        Record which poly_ids are "touched" (on or off).
        We will encounter issues if any touched notes differ from the original call.
        This is equivalent but MUCH faster than simulation.

        different = (np.array(track.pre_history) != self.note_history)
        if any(different & track.touched):
            LOG.error(...)


        # FULL SOLUTION?
        For calls (not jumps), repeat the entire call. When differently pitched note_offs occur,
        you can't record them under the same at[]. So this won't work.

        # GIVE UP
        Store note-off events natively.
            Kicking the can down the road. This won't help translating to other file formats.

        The only full solution is flattening the file.
        '''

        # HISTORY_MODE == 'LAZY'
        self.pre_history = np.copy(self.note_history)


    def bms_iter(self):

        # TODO: Do we use segment-based or linked-list iteration?
        # Segment-based iteration loses event address information!

        it = iter(self.segment)
        addr = self.addr

        while 1:
            ev = self._file.at[addr]  # type: BmsType
            ev_seg = next(it)

            if ev != ev_seg:
                LOG.error('BmsIter != segment at address %06X', addr)

            yield ev

            if 'next' in ev:
                addr = ev.next
            else:
                break



    def insert(self, evtype: Union[type, str], next=True, **evdata: dict) -> None:
        addr = self._prev_addr
        event_at = self._file.at

        assert addr not in event_at

        if isinstance(evtype, type):
            event = evtype(**evdata)
        else:
            assert False
            # event = BmsType(evtype, **evdata)
        if next:
            event.next = self._ptr.addr

        event_at[addr] = event
        self.segment.append(event)


    def parse(self) -> 'BmsTrack':
        insert = self.insert

        ptr = self._ptr
        stop = False

        self._prev_addr = None     # type: int

        while 1:
            prev_addr = ptr.addr
            self._prev_addr = prev_addr
            ev = ptr.u8(mode=Visit.BEGIN)

            # **** FLOW COMMANDS

            if 0:
                pass

            elif ev == 0xC1:            # new track
                self.child(ptr)

            elif ev in [0xC4, 0xC8]:    # call address
                self.call_jump(ev, ptr)


            elif ev == 0xFF:            # end track
                if self.tracknum is None:
                    raise SeqError('end_track from function')

                insert(EndTrack, next=False)
                stop = True

            elif ev == 0xC6:            # pop address
                if self.tracknum is not None:
                    raise SeqError('pop from root thread')

                insert(Pop, next=False)
                stop = True


            # **** SPECIAL COMMANDS

            elif ev == 0xE7:            # init track
                unknown = ptr.u16()

                # ASSERT
                if unknown != 0:
                    LOG.warning('Track init %04X != 0x0000', unknown)

                insert(InitTrack, unknown=unknown)

            elif ev in [0xA4, 0xAC]:    # instr change
                self.instr_change(ptr, ev)

            elif ev == 0xFE:            # tick rate
                insert(TickRate, value=ptr.u16())

            elif ev == 0xFD:            # tempo
                insert(Tempo, value=ptr.u16())

            elif ev == 0xE6:            # TODO unknown
                unknown = ptr.u16()

                # ASSERT
                if unknown != 0:
                    LOG.warning('WriteRemovePool %04X != 0x0000', unknown)

                insert(WriteRemovePool, unknown=unknown)

            # **** NOTES

            elif ev < 0x80:             # note on
                self.note_on(ptr, ev)

            elif ev in range(0x81, 0x88):
                self.note_off(ptr, ev)


            # **** CONTROL CHANGES

            elif 0x94 <= ev <= 0x9F:
                self.control_change(ptr, ev)



            # **** DELAYS

            elif ev == 0x80:
                insert(Delay, dtime = ptr.u8())

            elif ev == 0x88:
                insert(Delay, dtime = ptr.u16())

            elif ev == 0xEA:
                insert(Delay, dtime = ptr.u24())
            # TODO 0xCF
            elif ev == 0xF0:
                insert(Delay, dtime = ptr.vlq())


            # **** FALLBACK

            else:
                text = 'unknown event %s' % b2h(ev)
                LOG.warning(text)
                insert(text)
                stop = True

            assert prev_addr in self._file.at
            assert self._file.at[prev_addr] is not None

            if stop:
                break

        # HISTORY_MODE == 'LAZY'

        return self
    

    def child(self, ptr):
        tracknum = ptr.u8()
        addr = ptr.u24()

        LOG.warning('Track %d', tracknum)

        # Symlink
        self.insert(Child,
                    tracknum=tracknum,
                    addr=addr
                    )

        BmsTrack(self._file, addr, tracknum, None).parse()

    def call_jump(self, ev, ptr):
        jumps = {0xC4: Call, 0xC8: Jump}
        evtype = jumps[ev]

        mode = BmsSeekMode(ptr.u8())
        addr = ptr.u24()

        self.insert(evtype,
                    mode=mode,
                    addr=addr)

        # Assert that we aren't jumping into the middle of an instruction.

        hist = ptr.hist(addr)

        if hist == Visit.MIDDLE:
            raise OverlapError('%s %s - middle of command' % (jumps[ev], hex(addr)))

        # We are either visiting NONE or BEGIN.
        # Jump: Visit target (if necessary), then continue.
        # Call
        # 	Not visited:
        # 		Visit target.
        # 	Visited:
        # 		(addr) Check preconditions and apply postconditions.
        # 		Note that OldNote compares == None.

        # HISTORY_MODE == 'LAZY'
        if evtype == Call:

            if hist == Visit.NONE:
                track = BmsTrack(self._file, addr, None, self.note_history).parse()

            else:
                assert hist == Visit.BEGIN

                # **** ASSERTION ****
                # We will encounter issues if any touched notes differ from the original call.

                # TODO: We assume we're not calling into the middle of a visited section... :'(
                track = self._file.track_at[addr]

                different = (track.pre_history != self.note_history)
                if any(different & track.touched):
                    LOG.error(
'''Invalid call from %06X to %06X
    new:%s
    old:%s
    out:%s
    touched:%s''', self._prev_addr, addr, self.note_history, track.pre_history, track.note_history, track.touched)


            # endif already visited

            # BMS really shouldn't be touching notes, AND leaving running notes untouched...

            if any(track.touched):
                untouched = ~track.touched
                if any(track.pre_history.astype(bool) & untouched):
                    LOG.warning('Function leaves running notes untouched %s %s %s',
                                track.touched, track.pre_history, track.note_history)

            # Knowing that all "touched" entries entered identically...
            # We must apply all "touched" entries of the note history.
            self.note_history[track.touched] = track.note_history[track.touched]


        elif evtype == Jump:
            if hist == Visit.NONE:
                self._ptr.addr = addr
            else:
                assert hist == Visit.BEGIN
        else:
            assert False


    def instr_change(self, ptr, ev):
        # (ev), ev2, value
        # ev=width, ev2=type

        if ev == 0xA4:
            get = ptr.u8
            LOG.info('instr_change u8')
        elif ev == 0xAC:
            get = ptr.u16
            LOG.info('instr_change u16')
        else:
            assert False

        ev2 = ptr.u8()
        value = get()

        if ev2 == 0x20:
            ev2 = 'bank'
        elif ev2 == 0x21:
            ev2 = 'patch'
        else:
            LOG.warning('[instr %s] Unknown type %02X value=%02X', b2h(ev), ev2, value)
            ev2 = 'unknown %s' % b2h(ev2)

        self.insert(InstrChange, ev2=ev2, value=value)


    def note_on(self, ptr, ev):
        poly_id = ptr.u8()
        note = ev
        velocity = ptr.u8()

        self.insert(NoteOn,
                    poly_id=poly_id,
                    note=note,
                    velocity=velocity
                    )

        self.touched[poly_id] = True


        # Note history...

        if poly_id not in range(1, 8):
            LOG.error('Invalid poly_id at %06X = %02X (%02X v=%02X) %s',
                      self._prev_addr, poly_id, note, velocity, self.note_history)

        else:
            old = self.note_history[poly_id]
            if isinstance(old, int):
                LOG.error('Double note_on at %06X = %02X (%02X v=%02X) %s',
                          self._prev_addr, poly_id, note, velocity, self.note_history)
            self.note_history[poly_id] = note


    def note_off(self, ptr, ev):
        poly_id = ev % 8

        # magrittr %<>% ?
        # Expression object for self._note_history[poly_id] ?
        # Python sucks.

        note = self.note_history[poly_id]

        self.insert(NoteOff, note=note, poly_id=poly_id)

        self.note_history[poly_id] = OldNote(note)
        self.touched[poly_id] = True


        # Error checking...

        if not isinstance(note, int):
            LOG.error('Double note_off at %06X = %02X %s', self._prev_addr, poly_id, self.note_history)


    def control_change(self, ptr, ev) -> ControlChange:
        # u8 cctype, [layout/4] value, [layout%4] duration

        #        duration
        #  val | 0    ?    u8   u16
        # -----+---- ---- ---- -----
        #  u8  | 94   95   96   97
        #  s8  | 98   99   9a   9b
        #  s16 | 9c   9d   9e   9f

        layout = ev - 0x94

        # READ CCTYPE
        cctype = ptr.u8()

        # READ VALUE
        values = [ptr.u8, ptr.s8, ptr.s16]
        value = values[layout // 4]()

        # READ LENGTH
        durations = [lambda: 0, None, ptr.u8, ptr.u16]
        duration = durations[layout % 4]

        if duration is not None:
            duration = duration()
        else:
            duration = None
            LOG.error('Unknown event 0x%s', b2h(ev))

        # TODO: missing CCTYPEs
        try:
            cctype = BMS2CC[cctype]
        except KeyError:
            LOG.info('[CC %s] Unknown control change %s = %s', b2h(ev), b2h(cctype), value)
            cctype = 'unknown %s' % b2h(cctype)

        # LOG.info('control change - %s', cctype)
        # # ', %02X, %02X', value, duration
        # LOG.info('    value %s', 'u8 s8 s16'.split()[layout // 4])
        # LOG.info('    duration %s', '0 ? u8 u16'.split()[layout % 4])


        self.insert(ControlChange,
                    cctype=cctype,
                    value=value,
                    length=duration
                    )


        # **** ITERATOR ****

        # def __iter__(self):







    # **** BMS Event Types

    @methdispatch
    def after(self, event: BmsType):
        pass


    # **** FLOW COMMANDS

    @register(0xC1)
    class Child(BmsType):  # new track
        if 0:
            tracknum = 0x00
            addr = 0x000000

        @classmethod
        def from_ptr(cls, ptr: Pointer):
            d = cls()

            d.tracknum = ptr.u8()
            d.addr = ptr.u24()

            LOG.warning('Track %d', d.tracknum)
            return d

    @after.register(Child)
    def _(self, event: Child):
        BmsTrack(self._file, event.addr, event.tracknum, None).parse()


    class _CallJump(BmsType):
        if 0:
            mode = BmsSeekMode(0x00)
            addr = 0x000000

        @classmethod
        def from_ptr(cls, ptr: Pointer):
            d = cls()
            d.mode = BmsSeekMode(ptr.u8())
            d.addr = ptr.u24()

            hist = ptr.hist(d.addr)
            if hist == Visit.MIDDLE:
                raise OverlapError('%s -> %s - middle of command' % (cls, hex(d.addr)))

            assert hist in [Visit.NONE, Visit.BEGIN]
            return d

    @after.register(_CallJump)
    def _(self, event: _CallJump):
        raise NotImplementedError


    @register(0xC4)
    class Call(_CallJump):  # call address
        def after(event, file: 'BmsFile', ptr: Pointer):
            addr = event.addr
            hist = ptr.hist(addr)

            if hist == Visit.NONE:
                track = BmsTrack(self._file, addr, None, self.note_history).parse()

            else:
                assert hist == Visit.BEGIN

                # **** ASSERTION ****
                # We will encounter issues if any touched notes differ from the original call.

                # TODO: We assume we're not calling into the middle of a visited section... :'(
                track = self._file.track_at[addr]

                different = (track.pre_history != self.note_history)
                if any(different & track.touched):
                    LOG.error(
                        '''Invalid call from %06X to %06X
                            new:%s
                            old:%s
                            out:%s
                            touched:%s''', self._prev_addr, addr, self.note_history, track.pre_history,
                        track.note_history,
                        track.touched)

            # endif already visited

            # BMS really shouldn't be touching notes, AND leaving running notes untouched...

            if any(track.touched):
                untouched = ~track.touched
                if any(track.pre_history.astype(bool) & untouched):
                    LOG.warning('Function leaves running notes untouched %s %s %s',
                                track.touched, track.pre_history, track.note_history)

            # Knowing that all "touched" entries entered identically...
            # We must apply all "touched" entries of the note history.
            self.note_history[track.touched] = track.note_history[track.touched]

    class Jump(_CallJump):
        def after(self, file: 'BmsFile', ptr: Pointer):
            addr = self.addr
            hist = ptr.hist(addr)

            if hist == Visit.NONE:
                ptr.addr = addr
            else:
                assert hist == Visit.BEGIN

    class EndTrack(BmsType):  # end track
        pass

    class Pop(BmsType):  # pop address
        pass

    # **** SPECIAL COMMANDS

    class InitTrack(BmsType):
        if 0:
            unknown = 0x0000

    class InstrChange(BmsType):
        if 0:
            ev2 = 'bank|patch'
            value = 0x0001

    class TickRate(BmsType):
        if 0:
            value = 0x0010

    class Tempo(BmsType):
        if 0:
            value = 0x0010

    class WriteRemovePool(BmsType):
        if 0:
            unknown = 0x0000

    # **** NOTES

    class NoteOn(BmsType):
        if 0:
            poly_id = 1 - 7
            note = 0x00
            velocity = 0x00

    class NoteOff(BmsType):
        if 0:
            poly_id = 1 - 7
            note = 0x00

    # **** CONTROL CHANGES

    class ControlChange(BmsType):
        if 0:
            cctype = CC
            value = 1
            length = 1

    # **** DELAYS

    class Delay(BmsType):
        if 0:
            dtime = 0x000000

    # **** FALLBACK

    # class UnknownEvent(BmsType):
    #     if 0:
    #         code = 0xFE

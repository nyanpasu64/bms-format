from enum import Enum
from typing import Callable, Any, Union, Dict, List

from util import LOG, b2h, dict_invert, dict_from
from utils.classes import CC, SeqError, AttrDict
from utils.pointer import Pointer, OverlapError
from utils.pointer import Visit

Function = Callable[..., Any]



# **** BEGIN CLASS

CC2BMS = dict_from(
    CC,
    VOLUME=0,
    PITCH=1,
    PAN=3
)

BMS2CC = dict_invert(CC2BMS)


# BmsType = Enum('')


class BmsEvent(AttrDict):
    def __init__(self, cmd: str, **evdata):
        super().__init__(**evdata)

        if False:
            self.next = 0x000001
            self.addr = 0x000000

        self.type = cmd


class BmsFile(AttrDict):
    def __init__(self, data: bytes):
        super().__init__()

        self._data = data

        # "visited" = pointer tracking
        # "at" = events
        # TODO Should they be combined?
        # should Pointer know about the existence of BMS events? No?

        self._visited = [Visit.NONE] * len(data)    # type: List[Visit]
        self.at = {}                                # type: Dict[int, BmsEvent]
        self.tracks = {}                            # type: Dict[int, BmsTrack]
        self.track_at = {}                          # type: Dict[int, BmsTrack]
        # self.segments = {}                          # type: Dict[int, BmsSegment]

    def parse(self):
        BmsTrack(file=self, addr=0, tracknum=-1, note_history=None).parse()

        return self


# class BmsSegment(AttrDict):
#     def __init__(self, addr: int):
#         super().__init__()
#         self.addr = addr
#         self.arr = []   # type: List[BmsEvent]
#
#     def add(self, event: BmsEvent):
#         self.arr.append(event)
#
#     def iter(self):
#         return iter(self.arr)



class BmsSeekMode(Enum):
    Always = 0
    Zero = 1
    NonZero = 2
    One = 3
    GreaterThan = 4
    LessThan = 5


class BmsTypes:
    end_track = 'end_track'
    pop = 'pop'
    init_track = 'init_track'
    tick_rate = 'tick_rate'
    tempo = 'tempo'
    note_on = 'note_on'
    note_off = 'note_off'
    delay = 'delay'
    child = 'child'
    call = 'call'
    jump = 'jump'
    instr = 'instr_change'
    control_change = 'control_change'


class OldNote:
    """ This represents a stopped note in the BMS note history."""
    def __init__(self, val: int):
        self.val = val

    def __repr__(self):
        return '~%s' % self.val

    # HISTORY_MODE == 'LAZY'
    # This will not be 100% accurate if we have note repeat commands.

    # OldHistory is used for non-playing notes, so compares equal to no note.

    def __eq__(self, other):
        if isinstance(other, OldNote):
            return self.val == other.val

        if other is None:
            return True

        return NotImplemented

    def __ne__(self, other):
        return not self == other


HISTORY_MODE = 'LAZY'
class BmsTrack(AttrDict):
    # BmsPointer

    # BmsFile reference
    # insert into file.tracks
    # Yes, track 0 IS used.

    def __init__(self, file: BmsFile, addr:int,
                 tracknum: Union[int, None],
                 note_history: Union[List[int], None]):

        super().__init__()

        # Initialize stuff.
        self._file = file    # type: BmsFile
        self._data = file._data
        self._ptr = Pointer(self._data, addr, file._visited)


        # Insert track into file.
        if tracknum is not None:
            if tracknum in file.tracks:
                LOG.warning('Duplicate track %d', tracknum)

            file.tracks[tracknum] = self

        # Insert track at address.
        file.track_at[addr] = self


        # Initialize track.
        self.type = 'track'
        self.tracknum = tracknum
        self.addr = addr
        # self.segments = []   # type: List[int]


        # Note history (for note_off commands)
        if note_history is None:
            self.note_history = [None] * 8
        else:
            self.note_history = note_history[:]


        # In BMS, Note history is preserved through function calls.
            # 24354 turns 1 on. Pop.
            # 24361 turns 2 on. 24364 turns 1 off.

        # As a result, we pass self.hist to tracks.
        # (Return), self.hist[:] = track.hist
        # All passes are done by value. (subject to change)

        # You may call a function with one set of playing notes,
        # then end with another set.

        # Partial solution: At each address, check preconditions (note_history) and apply postconditions.
            # If repeat_note command, then None vs. OldNote may be a problem.

        assert HISTORY_MODE == 'LAZY'
        self.pre_history = self.note_history[:]


        # Full solution: For calls (not jumps), repeat the entire call.
            # Right now, Pointer raises OverlapError when we reread the same address.
            # That was implemented under the assumption that everything is read exactly once.


    def bms_iter(self):
        ev = self._file.at[self.addr]   # type: BmsEvent

        while 1:
            yield ev

            if 'next' in ev:
                addr = ev.next
                ev = self._file.at[addr]
            else:
                break



    def insert(self, cmd: str, next=True, **evdata: dict) -> None:
        addr = self._prev_addr
        event_at = self._file.at

        assert addr not in event_at

        event = BmsEvent(cmd, **evdata)
        if next:
            event.next = self._ptr.addr

        event_at[addr] = event

    def parse(self):
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

                insert('end_track', next=False)
                stop = True

            elif ev == 0xC6:            # pop address
                if self.tracknum is not None:
                    raise SeqError('pop from root thread')

                insert('pop', next=False)
                stop = True





            # **** SPECIAL COMMANDS

            elif ev == 0xE7:
                unknown = ptr.u16()
                if unknown != 0:
                    LOG.warn('Track init != 0x0000')

                insert('init_track', unknown=unknown)

            elif ev in [0xA4, 0xAC]:
                self.instr_change(ptr, ev)

            elif ev == 0xFE:
                insert('tick_rate', value=ptr.u16())

            elif ev == 0xFD:
                insert('tempo', value=ptr.u16())

            elif ev == 0xE6:    # TODO unknown
                msg = 'unknown [arookas]WriteRemovePool'
                LOG.info(msg)
                insert(msg, unknown=ptr.u16())

            # **** NOTES

            elif ev < 0x80:
                poly_id = ptr.u8()
                note = ev
                velocity = ptr.u8()

                insert('note_on',
                       poly_id=poly_id,
                       note=note,
                       velocity=velocity
                       )

                if poly_id not in range(1,8):
                    LOG.error('Invalid poly_id at %06X = %02X (%02X v=%02X) %s',
                              prev_addr, poly_id, note, velocity, self.note_history)
                    # poly_id %= 8
                else:
                    old = self.note_history[poly_id]
                    if isinstance(old, int):
                        LOG.error('Double note_on at %06X = %02X (%02X v=%02X) %s',
                                  prev_addr, poly_id, note, velocity, self.note_history)
                    self.note_history[poly_id] = note

            elif ev in range(0x81, 0x88):
                poly_id = ev % 8

                # magrittr %<>% ?
                # Expression object for self._note_history[poly_id] ?
                # Python sucks.

                note = self.note_history[poly_id]
                if not isinstance(note, int):
                    LOG.error('Invalid note_off at %06X = %02X %s', prev_addr, poly_id, self.note_history)

                self.note_history[poly_id] = OldNote(note)
                insert('note_off', note=note)



            # **** CONTROL CHANGES

            elif 0x94 <= ev <= 0x9F:
                self.control_change(ptr, ev)



            # **** DELAYS

            elif ev == 0x80:
                insert('delay', dtime = ptr.u8())

            elif ev == 0x88:
                insert('delay', dtime = ptr.u16())

            elif ev == 0xEA:
                insert('delay', dtime = ptr.u24())
            # TODO 0xCF
            elif ev == 0xF0:
                insert('delay', dtime = ptr.vlq())


            # **** FALLBACK

            else:
                text = 'unknown event %s' % b2h(ev)
                LOG.warn(text)
                insert(text)
                stop = True

            assert prev_addr in self._file.at
            assert self._file.at[prev_addr] is not None

            if stop:
                break

        assert HISTORY_MODE == 'LAZY'

        return self

    def child(self, ptr):
        tracknum = ptr.u8()
        addr = ptr.u24()

        # Symlink
        self.insert('child',
                    tracknum=tracknum,
                    addr=addr
                    )

        BmsTrack(self._file, addr, tracknum, None).parse()

    def call_jump(self, ev, ptr):
        jumps = {0xC4: BmsTypes.call, 0xC8: BmsTypes.jump}
        evtype = jumps[ev]

        mode = BmsSeekMode(ptr.u8())
        addr = ptr.u24()

        self.insert(evtype,
                    mode=mode,
                    addr=addr)

        # Call address?

        hist = ptr.hist(addr)

        if hist == Visit.MIDDLE:
            raise OverlapError('%s %s - middle of command' % (jumps[ev], hex(addr)))

        # Jump: Visit target (if necessary), then continue.
        # Call
        # 	Not visited:
        # 		Visit target.
        # 	Visited:
        # 		(addr) Check preconditions and apply postconditions.
        # 		Note that OldNote compares == None.

        assert HISTORY_MODE == 'LAZY'
        if evtype == BmsTypes.call:

            if hist == Visit.NONE:
                track = BmsTrack(self._file, addr, None, self.note_history).parse()

            else:
                assert hist == Visit.BEGIN
                # If we're recalling an address, we need to check pre-history and apply post-history.

                # FIXME: .tracks maps tracknum to track.
                # We need addr to track.
                track = self._file.track_at[addr]

                # Ensure we're calling the function with same running notes.
                if track.pre_history != self.note_history:
                    LOG.error('Invalid call from %06X to %06X %s %s',
                              self._prev_addr, addr, self.note_history, track.pre_history)


            # The subtrack has modified the note history. We must apply it here.
            # track.post_history has been copied. This is intentional, as it should not be modified by the parent.
            self.note_history[:] = track.note_history


        elif evtype == 'jump':
            if hist == Visit.NONE:
                self._ptr.addr = addr
        else:
            assert False


    def instr_change(self, ptr, ev):
        # (ev), ev2, value
        # ev=width, ev2=type

        if ev == 0xA4:
            get = ptr.u8
        elif ev == 0xAC:
            get = ptr.u16
        else:
            assert False

        ev2 = ptr.u8()
        value = get()

        if ev2 == 0x20:
            ev2 = 'bank'
        elif ev2 == 0x21:
            ev2 = 'patch'
        else:
            LOG.info('[instr %s] Unknown type %02X %02X', b2h(ev), ev2, value)
            ev2 = 'unknown %s' % b2h(ev2)

        self.insert('instr_change', ev2=ev2, value=value)


    def control_change(self, ptr, ev) -> BmsEvent:
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


        LOG.info('control change - %s, %02X, %02X', cctype, value, duration)

        self.insert('control_change',
                    cctype=cctype,
                    value=value,
                    length=duration
                    )


        # **** ITERATOR ****

        # def __iter__(self):


#!/usr/bin/env python

import sys
from enum import Enum, IntEnum
from typing import Callable, Any, Union, Dict, List

from util import LOG, b2h, AttrDict, without
from utils.pointer import Pointer, OverlapError
from utils.pointer import Visit

Function = Callable[..., Any]



class BmsError(ValueError):
    pass


# **** BEGIN CLASS

class BmsPerfType(Enum):
    VOLUME = 0
    PITCH = 1
    PAN = 3


class BmsSeekMode(Enum):
    Always = 0
    Zero = 1
    NonZero = 2
    One = 3
    GreaterThan = 4
    LessThan = 5


class BmsEvent(AttrDict):
    def __init__(self, cmd: str, **evdata):
        super().__init__(**evdata)
        self['type'] = cmd


class BmsFile(dict):
    def __init__(self, data: bytes):
        super().__init__()

        self.data = data

        # "visited" = pointer tracking
        # "at" = events
        # TODO Should they be combined?
        # should Pointer know about the existence of BMS events? No?

        self.visited = [Visit.NONE] * len(data)     # type: List[Visit]
        self['at'] = {}                             # type: Dict[int, BmsEvent]
        self['tracks'] = {}                       # type: Dict[int, int]

    def parse(self):
        BmsTrack(file=self, addr=0, tracknum=-1).parse()

        return self


class BmsTrack(dict):

    # BmsFile reference
    # when you create a child track, insert into file
    # Yes, track 0 IS used.

    # byte-operation mapping?
    # status[addr] = {unvisited, visited, interior}
    # interior = bail out

    def __init__(self, file: BmsFile, addr:int,
                 tracknum: Union[int, None]):

        super().__init__()
        self.file = file    # type: BmsFile
        self.data = file.data
        self.ptr = Pointer(self.data, addr, file.visited)

        self['type'] = 'track'
        # self['tracknum'] = tracknum
        self.tracknum = tracknum
        self['addr'] = addr

        if tracknum is not None:
            if tracknum in file['tracks']:
                LOG.warning('Duplicate track %d', tracknum)

            file['tracks'][tracknum] = self

        self.note_history = [None] * 8
        self.prev_addr = None

    def insert(self, cmd: str, next=True, **evdata: dict) -> None:
        addr = self.prev_addr
        event_at = self.file['at']

        assert addr not in event_at

        event = BmsEvent(cmd, **evdata)
        if next:
            event.next = self.ptr.addr

        event_at[addr] = event

    def parse(self) -> None:
        insert = self.insert

        ptr = self.ptr
        stop = False

        self.prev_addr = None     # type: int

        while 1:
            prev_addr = ptr.addr
            self.prev_addr = prev_addr
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
                    raise BmsError('end_track from function')

                insert('end_track', next=False)
                stop = True

            elif ev == 0xC6:            # pop address
                if self.tracknum is not None:
                    raise BmsError('pop from root thread')

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

                if poly_id >= 8:
                    LOG.error('Invalid poly_id at %06X = %02X (%02X v=%02X)', prev_addr, poly_id, note, velocity)
                    # poly_id %= 8
                else:
                    self.note_history[poly_id] = note

            elif ev in range(0x81, 0x88):
                note = self.note_history[ev % 8]
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

            assert prev_addr in self.file['at']
            assert self.file['at'][prev_addr] is not None

            if stop:
                break

    def child(self, ptr):
        tracknum = ptr.u8()
        addr = ptr.u24()

        # Symlink
        self.insert('child',
                    tracknum=tracknum,
                    addr=addr
                    )

        BmsTrack(self.file, addr, tracknum).parse()

    def call_jump(self, ev, ptr):
        jumps = {0xC4: 'call', 0xC8: 'jump'}
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

        if hist == Visit.NONE:

            # Call address.
            if evtype == 'call':
                BmsTrack(self.file, addr, None).parse()
            elif evtype == 'jump':
                self.ptr.addr = addr
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

        # FIX CCTYPE
        try:
            cctype = BmsPerfType(cctype)
        except ValueError:
            LOG.info('[CC %s] Unknown control change %s = %s', b2h(ev), b2h(cctype), value)
            cctype = 'unknown %s' % b2h(cctype)


        LOG.info('control change - %s, %02X, %02X', cctype, value, duration)

        self.insert('control_change',
                    cctype=cctype,
                    value=value,
                    length=duration
                    )


from ruamel import yaml
from ruamel.yaml.representer import SafeRepresenter


def represents(cls):
    def _represents(func):
        yaml.add_representer(cls, func)
        return func
    return _represents


@represents(int)
@represents(BmsPerfType)
def int_presenter(dumper: SafeRepresenter, data):
    return dumper.represent_int(data)

@represents(BmsEvent)
def event_pres(dumper: SafeRepresenter, data):

    data = dict(data)
    for k in ['addr', 'next']:
        if k in data:
            data[k] = hex(data[k])

    tag = data['type']
    # print(tag)
    # print(without(data, 'type'))

    rep = dumper.represent_mapping(
        tag,
        without(data, 'type')
    )

    # print(type(rep))
    return rep


@represents(BmsTrack)
def track_pres(dumper: SafeRepresenter, data):
    data = dict(data)

    k = 'addr'
    if k in data:
        data[k] = hex(data[k])

    return dumper.represent_dict(data)

@represents(BmsFile)
def track_pres(dumper: SafeRepresenter, data):
    new = {}
    for k,v in data.items():
        if k == 'at':
            new[k] = {'$%04X'%addr: event for addr,event in v.items()}
        else:
            new[k] = v

    return dumper.represent_dict(new)


@represents(BmsPerfType)
@represents(BmsSeekMode)
def track_pres(dumper: SafeRepresenter, data):
    return dumper.represent_int(str(data))

def get_tree(tree: dict) -> str:
    return yaml.dump(tree, indent=2)





def main():
    argv = sys.argv

    with open(argv[1], 'rb') as f:
        data = f.read()
        tree = BmsFile(data).parse()

        print(get_tree(tree))

if __name__ == '__main__':
    main()

import sys
from enum import Enum, IntEnum
from typing import Callable, Any
from typing import Dict
from typing import List

from util import get_tree, LOG, b2h
from utils.pointer import Pointer

Function = Callable[..., Any]



class BmsError(ValueError):
    pass




# **** BEGIN CLASS

class BmsPerfType(IntEnum):
    VOLUME = 0
    PITCH = 1
    PAN = 3


class BmsEvent(dict):
    def __init__(self, cmd: str, **evdata):
        super().__init__(**evdata)
        self['type'] = cmd


class BmsTrack(dict):

    def __init__(self, data: bytes, addr:int, tracknum:int):
        super().__init__()
        self.data = data
        self.ptr = Pointer(data, addr)

        self['type'] = 'track'
        self['tracknum'] = tracknum
        self['children'] = {tracknum: None}     # type: Dict[int, BmsTrack]
        self['track'] = []                      # type: List[BmsEvent]

        self.note_history = [None]*8


    def insert(self, cmd: str, **evdata: dict) -> dict:
        # Add "type=cmd".
        self['track'].append(BmsEvent(cmd, **evdata))
        return evdata

    def parse(self):
        insert = self.insert

        track = self['track']
        ptr = self.ptr

        stop = False

        while 1:
            ev = ptr.u8()
            LOG.debug('%06X - %02X', ptr.addr-1, ev)

            old = None
            if track:
                old = track[-1]

            # **** FLOW COMMANDS

            if 0:
                pass

            elif ev == 0xC1:
                self.child(ptr)

            elif ev == 0xFF:
                insert('end_track')
                stop = True

            # todo finish jump/call
            elif ev == 0xC4:
                insert('call',
                       mode=ptr.u8(),
                       addr=ptr.u24()
                       )

            elif ev == 0xC8:
                insert('jump',
                       mode=ptr.u8(),
                       addr=ptr.u24()
                       )

            # **** SPECIAL COMMANDS

            elif ev == 0xE7:
                unknown = ptr.u16()
                if unknown != 0:
                    LOG.warn('Track init != 0x0000')

                insert('init', unknown=unknown)

            elif ev in [0xA4, 0xAC]:
                self.instr_change(ptr, ev)

            elif ev == 0xFE:
                insert('tick_rate', value=ptr.u16())

            elif ev == 0xFD:
                insert('tempo', value=ptr.u16())

            elif ev == 0xE6:    # TODO unknown
                msg = 'unknown [arookas]WriteRemovePool'
                LOG.debug(msg)
                insert(msg, unknown=ptr.u16())

            # **** NOTES

            elif ev < 0x80:
                addr = ptr.addr
                poly_id = ptr.u8()
                note = ev
                velocity = ptr.u8()

                insert('note_on',
                       poly_id=poly_id,
                       note=note,
                       velocity=velocity
                       )

                if poly_id >= 8:
                    LOG.error('Invalid poly_id at %06X = %02X (%02X v=%02X)', addr, poly_id, note, velocity)
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
                insert('unknown event %s' % b2h(ev))
                stop = True

            if track[-1] is None:
                assert False

            if track[-1] is old:
                assert False

            if stop:
                break
        return self


    def child(self, ptr):
        tracknum = ptr.u8()
        addr = ptr.u24()

        # Symlink
        self.insert('child',
                    tracknum=tracknum,
                    addr=addr
                    )

        # Parse
        child = BmsTrack(self.data, addr, tracknum).parse()

        children = self['children']     # type: Dict[int, BmsTrack]
        grand = child['children']       # type: Dict[int, BmsTrack]

        # Don't add child to children. That will create false-positive recursion.

        # Check for duplicates
        # Each track has a subtree dict.
        # TODO: Do we need a separate "subtree" function? subtree ids only?
        # .children{.tracknum...} + child.children{.tracknum...}

        # 1+2 = collision
        intersect = children.keys() & grand.keys()
        if intersect:
            LOG.warning('Duplicate tracks %s', str(intersect))
            if self['tracknum'] in grand:
                LOG.warning('Parent track collision %s', self['tracknum'])
            if tracknum in children:
                LOG.warning('Child track collision %s', tracknum)

        # FIXME Uh, we're kinda overwriting grandchildren with children.
        # But we don't overwrite children with self.
        children.update(grand)
        children[tracknum] = child
        # grand.clear()
        del child['children']


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
            LOG.warning('[CC %s] Unknown control change %s = %s', b2h(ev), b2h(cctype), value)
            cctype = 'unknown %s' % b2h(cctype)


        LOG.debug('control change - %s, %02X, %02X', cctype, value, duration)

        self.insert('control_change',
                    cctype=cctype,
                    value=value,
                    length=duration
                    )



class BmsFile:
    def __init__(self):

        # Bind methods.
        self._stack = []

        self.tracks = {}    # TODO unused

        # TODO: BmsFile.output = parse()
        # versus BmsTrack: BmsFile[] = result
        # OrderedDict()

    def load(self, data: bytes):
        self.data = data

        track = BmsTrack(data, 0, tracknum=-1).parse()

        return track

    # def pushpop(self, addr: int) -> Pointer:
    #     ptr = Pointer(self.data, addr)
    #     self.push(ptr)
    #     yield ptr
    #
    #     return self.pop()
    #
    # def push(self, frame: Pointer) -> Pointer:
    #     self._stack.append(frame)
    #     return frame
    #
    # def pop(self) -> Pointer:
    #     return self._stack.pop()



def main():
    argv = sys.argv

    with open(argv[1], 'rb') as f:
        data = f.read()
        tree = BmsFile().load(data)

        print(get_tree(tree))

if __name__ == '__main__':
    main()

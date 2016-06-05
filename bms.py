import sys
from enum import Enum, IntEnum
from typing import Callable, Any
from typing import Dict
from typing import List

from util import get_tree, LOGGER
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

    def __init__(self, data: bytes, **kwargs):
        super().__init__(**kwargs)
        self._data = data

        self['type'] = 'track'
        self['children'] = {}   # type: Dict[int, BmsTrack]
        self['track'] = []      # type: List[BmsEvent]

    def insert(self, cmd: str, **evdata: dict) -> dict:
        # Add "type=cmd".
        self['track'].append(BmsEvent(cmd, **evdata))
        return evdata

    def parse(self, addr:int):

        track = self['track']

        insert = self.insert

        # # Add out_dict to JSON parent.
        # if tracknum in self.tracks:
        #     raise BmsError('duplicate track numbers')
        # self.tracks[tracknum] = out_dict

        ptr = Pointer(self._data, addr)

        stop = False

        while 1:
            ev = ptr.u8()
            LOGGER.debug(hex(ev))

            # **** FLOW COMMANDS

            old = None
            if track:
                old = track[-1]

            if 0:
                pass

            elif ev == 0xC1:
                self.child(ptr)


            elif ev == 0xFF:
                insert('end_track')
                stop = True

            # SPECIAL COMMANDS

            elif ev == 0xE7:
                insert('init',
                       unknown = str(ptr.hexmagic('0000'))
                       )

            elif ev in [0xA4, 0xAC]:
                self.instr_change(ptr, ev)

            elif ev == 0xFE:
                insert('tick_rate', value=ptr.u16())

            elif ev == 0xFD:
                insert('tempo', value=ptr.u16())

            # **** NOTES

            elif ev < 0x80:
                insert('note_on',
                       poly_id = ptr.u8(),
                       note = ev,
                       velocity = ptr.u8()
                       )

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
                insert('unknown event 0x%X' % ev)
                stop = True

            if track[-1] is None:
                assert False

            if track[-1] is old:
                assert False

            if stop:
                break
        return self



    # Each track has a dict of children.
    # children + child + grandchildren
    # So check twice for errors.

    def child(self, ptr):
        tracknum = ptr.u8()
        addr = ptr.u24()

        # Symlink
        self.insert('child',
                    tracknum=tracknum,
                    addr=addr
                    )

        # Parse
        child = BmsTrack(self._data).parse(addr)

        children = self['children']     # type: Dict[int, BmsTrack]
        grand = child['children']       # type: Dict[int, BmsTrack]

        # Check for duplicates
        # children + tracknum + grand

        # 2+3 = recursion
        if tracknum in grand:
            LOGGER.warn('Recursive child ')

        # 1+2 = collision
        intersect = children.keys() & grand.keys()
        if intersect:
            LOGGER.warn('Duplicate tracks %s', str(intersect))

        children[tracknum] = child
        children.update(grand)
        grand.clear()


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
            LOGGER.warn('Unknown instr change %X %X %X', ev, ev2, value)
            ev2 = hex(ev2)

        self.insert('instr_change', ev2=ev2, value=value)


    def control_change(self, ptr, ev) -> BmsEvent:
        # u8 BmsPerfType, u? value, us? length
        layout = ev - 0x94

        # READ CCTYPE
        cctype = ptr.u8()
        try:
            cctype = BmsPerfType(cctype)
        except ValueError:
            LOGGER.warn('[CC %X] Unknown control change 0x%X', ev, cctype)

        # READ VALUE
        values = [ptr.u8, ptr.s8, ptr.s16]
        value = values[layout // 4]()

        # READ LENGTH
        lengths = [lambda: 0, None, ptr.u8, ptr.u16]
        length = lengths[layout % 4]

        if length is not None:
            length = length()
        else:
            length = None
            LOGGER.warn('Unknown event 0x%X', ev)

        LOGGER.debug('control change %X %X %X', cctype, value, length)

        self.insert('control_change',
                    cctype=cctype,
                    value=value,
                    length=length
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

        track = BmsTrack(data).parse(0)

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

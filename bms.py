import sys
from enum import Enum, IntEnum
from typing import Callable, Any
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


class BmsFile:
    def __init__(self):

        # Bind methods.
        self._stack = []

        self.tracks = {}

        # TODO: BmsFile.output = parse()
        # versus BmsTrack: BmsFile[] = result
        # OrderedDict()

    def load(self, data: bytes):
        self.data = data

        self.parse(addr=0, tracknum=-1, depth=0)

        return self.tracks

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


    def parse(self, *, addr:int, tracknum:int, depth:int) -> None:

        out_dict = {'type': 'track'}
        track = []  # type: List[BmsEvent]
        out_dict['track'] = track

        # Add out_dict to JSON parent.
        if tracknum in self.tracks:
            raise BmsError('duplicate track numbers')
        self.tracks[tracknum] = out_dict

        # etc.
        def insert(cmd: str, **evdata:dict) -> dict:
            # Add "type=cmd".
            track.append(BmsEvent(cmd, **evdata))
            return evdata

        def append(event:BmsEvent) -> None:
            track.append(event)

        ptr = Pointer(self.data, addr)
        stop = False

        while 1:
            ev = ptr.u8()
            LOGGER.debug(hex(ev))

            # **** FLOW COMMANDS

            if 0: pass

            elif ev == 0xC1:
                kwargs = insert('child',
                      tracknum = ptr.u8(),
                      addr = ptr.u24()
                      )
                self.parse(**kwargs, depth=depth+1)

            elif ev == 0xFF:
                insert('break')
                stop = True

            # SPECIAL COMMANDS

            elif ev == 0xE7:
                insert('init',
                       unknown = str(ptr.hexmagic('0000'))
                       )

            elif ev in [0xA4, 0xAC]:
                # FIXME APPEND
                append(self.instr_change(ptr, ev))

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
                # FIXME APPEND
                append(self.control_change(ptr, ev))



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

            if stop:
                break

    @staticmethod
    def instr_change(ptr, ev) -> BmsEvent:
        if ev == 0xA4:
            get = ptr.u8
        elif ev == 0xAC:
            get = ptr.u16
        else:
            assert False

        ev2 = ptr.u8()
        value = get()

        if ev2 == 0x20:
            return BmsEvent('bank_select', value=value)
        elif ev2 == 0x21:
            return BmsEvent('patch_change', value=value)
        else:
            LOGGER.warn('Unknown instr change %X %X %X', ev, ev2, value)
            return BmsEvent('unknown_instr_%X' % ev2, value=value)

    @staticmethod
    def control_change(ptr, ev) -> BmsEvent:
        # u8 BmsPerfType, u? value, us? length
        layout = ev - 0x94

        # READ CCTYPE
        try:
            cctype = BmsPerfType(ptr.u8())
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

        return BmsEvent('control_change',
                        cctype=cctype,
                        value=value,
                        length=length
                        )


def main():
    argv = sys.argv

    with open(argv[1], 'rb') as f:
        data = f.read()
        tree = BmsFile().load(data)

        print(get_tree(tree))

if __name__ == '__main__':
    main()

import sys
from contextlib import contextmanager
from typing import Dict

from formats.bms import BmsFile, BmsEvent, BmsTrack, BmsNames
from utils.classes import SeqError


@contextmanager
def redirect(file):
    stdout = sys.stdout
    sys.stdout = open(file, 'w')
    yield

    sys.stdout = stdout





def bms2amk(file: BmsFile):
    at = file['at']                 # type: Dict[int, BmsEvent]
    tracks = file['tracks']         # type: Dict[int, BmsTrack]


    def parse_track(tracknum: int, track: BmsTrack):
        if tracknum == -1:

            for ev in track.bms_iter():
                if ev.type == BmsNames.child:
                    parse_track()



            return

        for ev in track.bms_iter():
            raise SeqError


    for tracknum, track in sorted(tracks.items()):  # type: int, BmsTrack
        parse_track(tracknum, track)


    # print('#', tracknum, sep='')
    #
    # for ev in track.bms_iter():
    #     if ev.type == BmsTypes.end_track:
    #         break


def dragon_roost():
    with redirect('dragon-roost.txt'):
        print('#amk 2')

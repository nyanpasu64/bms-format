import fluidsynth as fs

from util import dict_from
from utils.classes import CC

if False:   # mypy type checking
    from bms import BmsFile

CC2MIDI = dict_from(
    CC,
    VOLUME=7,
    PITCH=0,
    PAN=10)


class SeqSynth:

    # def sfload(filename, update_midi_preset=0):
    # def sfunload(sfid, update_midi_preset=0):
    # def program_select(chan, sfid, bank, preset):

    # def noteon(chan, key, vel):
    # def noteoff(chan, key):
    # def pitch_bend(chan, val):

    # def cc(chan, ctrl, val):

    # def program_change(chan, prg):
    # def bank_select(chan, bank):

    def __init__(self, seq: BmsFile, **kwargs):
        kw = {'samplerate': 48000}
        kw.update(kwargs)

        self.seq = seq

        self.synth = fs.Synth(samplerate=48000, **kw)
        # 256 channels

    def render(self):

        # TODO time/segment-based iterator
        rofl = [
            (time, tnum, event)
            for tnum, track in self.seq.tracks
                for event in track
        ]


        # start() - NO!

        # get_samples()
        # 16-bit sample-interleaved stereo LLRRLLRR

        self.synth.get_samples(smp)

        pass

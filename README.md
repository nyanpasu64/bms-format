# BMS Format Project-
This is a project to document and decode GameCube BMS sequences. These are MIDI-like files used in games including Super Mario Sunshine, Zelda Wind Waker, and Twilight Princess.

See `bms.py`.

## Progress

- [x] raw binary file
- [x] parse to tree
    - [ ] protobuf/json
- [ ] generic file format
    - [ ] protobuf/json
- [ ] editor
- [ ] bms tree
- [ ] encode binary

## Future Goals

* At some point, I'll add support for SNES/DS audio formats.
* Build my own sequencer/DAW?
    * In the future, I'll add a script-based editor, a GUI sequencer, and an audio rendering engine.
    * All operations are concatenated into a process script, which can be transparently viewed and edited as a tree (or text). Undos are handled in a version tree, and files are automatically committed on save.
        * "Undo" mean "last change" (programming), not "last operation" (conventional sequencers)?
        * Undo repository state, or file state?

I'm looking into Ruby, Rust, Go, etc. for code flexibility and/or type safety.

Probably C++ with Juce for the audio rendering engine (and possibly interface).

* MIDI file export is not a primary goal. MIDIs are limited to 16 channels and have limited instrument choice.
* Realtime (clock-based, hardware, timecode-based VST) rendering is not an objective. All timings should be (sub-)sample-exact, based on samples and tempo only, unaffected by jitter, latency, or slow data transfers.

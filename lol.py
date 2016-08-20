def child(self, ptr):
    tracknum = ptr.u8()
    addr = ptr.u24()

    LOG.warning('Track %d', tracknum)

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

    hist = ptr.hist(addr)

    if hist == Visit.MIDDLE:
        raise OverlapError('%s %s - middle of command' % (jumps[ev], hex(addr)))

    if evtype == Call:

        if hist == Visit.NONE:
            track = BmsTrack(self._file, addr, None, self.note_history).parse()

        else:
            assert hist == Visit.BEGIN

            track = self._file.track_at[addr]

            different = (track.pre_history != self.note_history)
            if any(different & track.touched):
                LOG.error(
'''Invalid call from %06X to %06X
new:%s
old:%s
out:%s
touched:%s''', self._prev_addr, addr, self.note_history, track.pre_history, track.note_history, track.touched)


        if any(track.touched):
            untouched = ~track.touched
            if any(track.pre_history.astype(bool) & untouched):
                LOG.warning('Function leaves running notes untouched %s %s %s',
                            track.touched, track.pre_history, track.note_history)

        self.note_history[track.touched] = track.note_history[track.touched]


    elif evtype == Jump:
        if hist == Visit.NONE:
            self._ptr.addr = addr
    else:
        assert False


def instr_change(self, ptr, ev):
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

    note = self.note_history[poly_id]

    self.insert(NoteOff, note=note, poly_id=poly_id)

    self.note_history[poly_id] = OldNote(note)
    self.touched[poly_id] = True


    if not isinstance(note, int):
        LOG.error('Double note_off at %06X = %02X %s', self._prev_addr, poly_id, self.note_history)


def control_change(self, ptr, ev) -> ControlChange:
    layout = ev - 0x94

    cctype = ptr.u8()

    values = [ptr.u8, ptr.s8, ptr.s16]
    value = values[layout // 4]()

    durations = [lambda: 0, None, ptr.u8, ptr.u16]
    duration = durations[layout % 4]

    if duration is not None:
        duration = duration()
    else:
        duration = None
        LOG.error('Unknown event 0x%s', b2h(ev))

    try:
        cctype = BMS2CC[cctype]
    except KeyError:
        LOG.info('[CC %s] Unknown control change %s = %s', b2h(ev), b2h(cctype), value)
        cctype = 'unknown %s' % b2h(cctype)

    self.insert(ControlChange,
                cctype=cctype,
                value=value,
                length=duration
                )

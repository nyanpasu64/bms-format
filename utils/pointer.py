from binascii import unhexlify
from enum import Enum
from typing import ByteString, List


# todo save as json/protobuf


def wrap(val, bits):
    val %= 2 ** bits

    wraparound = 2 ** (bits - 1)
    if val >= wraparound:
        val -= wraparound * 2

    return val


def bytes2int(in_bytes, endian=False):
    return int.from_bytes(in_bytes, 'little' if endian else 'big')


class OverlapError(ValueError):
    pass


class MagicError(ValueError):
    pass


class Visit(Enum):
    NONE = 0
    BEGIN = 1
    MIDDLE = 2


class Pointer:
    def __init__(self,
                 data: bytes,
                 addr: int,
                 visited: List[Visit],
                 endian=False):

        if not isinstance(data, ByteString):
            raise TypeError('Pointer() requires bytes or bytearray (buffer API)')

        if len(data) != len(visited):
            raise ValueError(
                'Data %s != Visited log %s' % (len(data), len(visited))
            )

        self.data = data
        self.visited = visited

        self.addr = None
        self.seek(addr)

        # self.bytes() raises OverlapError
        self.u8 = self._get_unsignedf(8, endian)
        self.u16 = self._get_unsignedf(16, endian)
        self.u24 = self._get_unsignedf(24, endian)
        self.u32 = self._get_unsignedf(32, endian)

        self.s8 = self._get_signedf(8, endian)
        self.s16 = self._get_signedf(16, endian)
        self.s24 = self._get_signedf(24, endian)
        self.s32 = self._get_signedf(32, endian)

    def seek(self, addr):
        data = self.data

        if not isinstance(addr, int) or not (0 <= addr < len(data)):
            raise ValueError('Invalid address {} / {}'.format(addr, len(data)))

        self.addr = addr

        return addr

    def seek_rel(self, offset):
        return self.seek(self.addr + offset)

    # **** READ ****

    def hist(self, addr=None):
        if addr is None:
            addr = self.addr

        return self.visited[addr]

    def bytes(self, length, mode:Visit = Visit.MIDDLE):
        old_idx = self.addr
        self.addr += length
        idx = self.addr

        if idx > len(self.data):
            raise StopIteration

        for hist in self.visited[old_idx:idx]:
            if hist != Visit.NONE:
                raise OverlapError

        if length <= 0:
            raise ValueError('bytes() call, length %s (<= 0)' % length)

        self.visited[old_idx:idx] = [Visit.MIDDLE] * length
        self.visited[old_idx] = mode

        return self.data[old_idx:idx]

    def vlq(self):
        out = 0

        while 1:
            # Assemble a multi-byte int.
            byte = self.u8()
            sub = byte & 0x7f

            out <<= 7
            out |= sub

            if byte & 0x80 == 0:
                break

        return out

    def magic(self, magic):
        """ Assert the existence of magic constants. """
        pos = self.addr

        read = self.bytes(len(magic))
        if read != magic:
            raise MagicError('Invalid magic at {}: {} != {}'.format(pos, read, magic))

        return read

    def hexmagic(self, hexmagic):
        return self.magic(unhexlify(hexmagic))

    # self.bytes() raises OverlapError
    def _get_unsignedf(self, bits, endian):
        nbytes = bits // 8

        def get_unsigned(mode:Visit = Visit.MIDDLE):
                # endian=endian

            data = self.bytes(nbytes, mode)
            return bytes2int(data, endian)

        return get_unsigned

    def _get_signedf(self, bits, endian):
        def get_signed(endian=endian):
            return wrap(
                self._get_unsignedf(bits, endian)(),
                bits
            )

        return get_signed

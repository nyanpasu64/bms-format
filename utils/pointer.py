from typing import ByteString


def wrap(val, bits):
    val %= 2 ** bits

    wraparound = 2 ** (bits - 1)
    if val >= wraparound:
        val -= wraparound * 2

    return val


def bytes2int(in_bytes, endian=False):
    return int.from_bytes(in_bytes, 'little' if endian else 'big')


class MagicError(ValueError):
    pass


class Pointer:
    def __init__(self, data, addr: int = 0, endian=False):

        if not isinstance(data, ByteString):
            raise TypeError('Pointer() requires bytes or bytearray (buffer API)')

        self.data = data

        self.addr = None
        self.seek(addr)

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

    def str(self, length):
        old_idx = self.addr
        self.addr += length
        idx = self.addr

        if idx > len(self.data):
            raise StopIteration

        return self.data[old_idx:idx]

    def vlq(self):
        out = 0

        while 1:
            # Assemble a multi-byte int.
            byte = self.u8()
            next_delay = byte & 0x7f

            out <<= 7
            out |= next_delay

            if byte & 0x80 == 0:
                break

        return out

    def magic(self, magic):
        """ Assert the existence of magic constants. """
        pos = self.addr

        read = self.str(len(magic))
        if read != magic:
            raise MagicError('Invalid magic at {}: {} != {}'.format(pos, read, magic))

    def _get_unsignedf(self, bits, endian):
        def get_unsigned(endian=endian):
            bytes = bits // 8
            old_idx = self.addr
            self.addr += bytes

            if self.addr > len(self.data):
                raise StopIteration

            return bytes2int(self.data[old_idx: old_idx + bytes], endian)

        return get_unsigned

    def _get_signedf(self, bits, endian):
        def get_signed(endian=endian):
            return wrap(
                self._get_unsignedf(bits, endian)(),
                bits
            )

        return get_signed

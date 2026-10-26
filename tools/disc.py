"""The data track of the CD image (raw 2352-byte Mode 1 sectors) and its
ISO 9660 file system: read the files of the root directory, put new
contents in, write the track back.

A file that still fits in the sectors it had stays where it is; a larger
one goes after the last sector of the track, and its directory record is
updated (the game opens its files by name). Every rewritten sector gets
its header, EDC and ECC computed again.
"""
import struct

SECTOR = 2352
DATA = 2048
PREGAP = 150            # LBA 0 is 00:02:00


# --- EDC / ECC (ECMA-130) ----------------------------------------------------

def _edc_table():
    t = []
    for i in range(256):
        e = i
        for _ in range(8):
            e = (e >> 1) ^ (0xd8018001 if e & 1 else 0)
        t.append(e)
    return t


_EDC = _edc_table()
_ECC_F = [0] * 256
_ECC_B = [0] * 256
for _i in range(256):
    _j = (_i << 1) ^ (0x11d if _i & 0x80 else 0)
    _ECC_F[_i] = _j
    _ECC_B[_i ^ _j] = _i


def edc(data):
    e = 0
    t = _EDC
    for b in data:
        e = (e >> 8) ^ t[(e ^ b) & 0xff]
    return e


def _ecc_part(sec, major_count, minor_count, major_mult, minor_inc, out_off):
    size = major_count * minor_count
    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        a = b = 0
        for _ in range(minor_count):
            temp = sec[12 + index]
            index += minor_inc
            if index >= size:
                index -= size
            a ^= temp
            b ^= temp
            a = _ECC_F[a]
        a = _ECC_B[_ECC_F[a] ^ b]
        sec[out_off + major] = a
        sec[out_off + major + major_count] = a ^ b


def make_sector(lba, data):
    """a Mode 1 sector for LBA with 2048 bytes of user data"""
    assert len(data) == DATA
    sec = bytearray(SECTOR)
    sec[0:12] = b'\x00' + b'\xff' * 10 + b'\x00'
    f = lba + PREGAP
    m, s, fr = f // (75 * 60), (f // 75) % 60, f % 75

    def bcd(x):
        return (x // 10) << 4 | (x % 10)
    sec[12:16] = bytes((bcd(m), bcd(s), bcd(fr), 1))
    sec[16:16 + DATA] = data
    sec[0x810:0x814] = struct.pack('<I', edc(sec[0:0x810]))
    _ecc_part(sec, 86, 24, 2, 86, 0x81c)     # P
    _ecc_part(sec, 52, 43, 86, 88, 0x8c8)    # Q
    return bytes(sec)


# --- ISO 9660 ------------------------------------------------------------------

class Track:
    def __init__(self, path):
        self.raw = bytearray(open(path, 'rb').read())
        assert len(self.raw) % SECTOR == 0
        pvd = self.data(16)
        assert pvd[1:6] == b'CD001'
        root = pvd[156:190]
        self.root_lba = struct.unpack('<I', root[2:6])[0]
        self.root_size = struct.unpack('<I', root[10:14])[0]
        self.files = {}        # name -> (record offset in the track, lba, size)
        d = b''.join(self.data(self.root_lba + i) for i in range((self.root_size + DATA - 1) // DATA))
        o = 0
        while o < len(d):
            n = d[o]
            if n == 0:
                o = (o // DATA + 1) * DATA
                continue
            r = d[o:o + n]
            name = r[33:33 + r[32]]
            if name not in (b'\x00', b'\x01'):
                name = name.decode().split(';')[0]
                lba = struct.unpack('<I', r[2:6])[0]
                size = struct.unpack('<I', r[10:14])[0]
                self.files[name] = (o, lba, size)
            o += n

    @property
    def sectors(self):
        return len(self.raw) // SECTOR

    def data(self, lba):
        return bytes(self.raw[lba * SECTOR + 16:lba * SECTOR + 16 + DATA])

    def write_data(self, lba, data):
        if lba == self.sectors:
            self.raw.extend(bytes(SECTOR))
        self.raw[lba * SECTOR:(lba + 1) * SECTOR] = make_sector(lba, data)

    def read(self, name):
        o, lba, size = self.files[name]
        return b''.join(self.data(lba + i) for i in range((size + DATA - 1) // DATA))[:size]

    def put(self, name, blob):
        """new contents of a file: in place when it fits in its sectors,
        else after the end of the track"""
        o, lba, size = self.files[name]
        have = (size + DATA - 1) // DATA
        need = (len(blob) + DATA - 1) // DATA
        if need > have:
            lba = self.sectors
        padded = blob + bytes(need * DATA - len(blob))
        for i in range(need):
            self.write_data(lba + i, padded[i * DATA:(i + 1) * DATA])
        self.files[name] = (o, lba, len(blob))
        self._record(o, lba, len(blob))

    def _record(self, o, lba, size):
        """update the directory record at offset o of the root directory"""
        sec, off = divmod(o, DATA)
        d = bytearray(self.data(self.root_lba + sec))
        d[off + 2:off + 10] = struct.pack('<I', lba) + struct.pack('>I', lba)
        d[off + 10:off + 18] = struct.pack('<I', size) + struct.pack('>I', size)
        self.write_data(self.root_lba + sec, bytes(d))

    def finish(self):
        """volume size in the primary volume descriptor"""
        d = bytearray(self.data(16))
        d[80:88] = struct.pack('<I', self.sectors) + struct.pack('>I', self.sectors)
        self.write_data(16, bytes(d))
        return bytes(self.raw)

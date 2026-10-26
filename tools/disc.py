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

    def add(self, files):
        """new files {name: blob}: their data after the end of the track,
        the root directory rebuilt with them (sorted, as ISO 9660 wants)
        and moved after the end of the track when it needs more sectors"""
        d = b''.join(self.data(self.root_lba + i) for i in range(self.root_size // DATA))
        recs = []
        o = 0
        while o < len(d):
            n = d[o]
            if n == 0:
                o = (o // DATA + 1) * DATA
                continue
            recs.append(bytearray(d[o:o + n]))
            o += n
        dot, dotdot, rest = recs[0], recs[1], recs[2:]
        template = rest[0]
        for name, blob in files.items():
            assert name not in self.files, name
            lba = self.sectors
            need = (len(blob) + DATA - 1) // DATA
            padded = blob + bytes(need * DATA - len(blob))
            for i in range(need):
                self.write_data(lba + i, padded[i * DATA:(i + 1) * DATA])
            ident = (name + ';1').encode()
            n = 33 + len(ident)
            n += n & 1
            r = bytearray(n)
            r[0] = n
            r[18:25] = template[18:25]          # date
            r[25] = template[25]                # flags
            r[28:32] = template[28:32]          # volume sequence
            r[32] = len(ident)
            r[33:33 + len(ident)] = ident
            r[2:10] = struct.pack('<I', lba) + struct.pack('>I', lba)
            r[10:18] = struct.pack('<I', len(blob)) + struct.pack('>I', len(blob))
            rest.append(r)
        rest.sort(key=lambda r: bytes(r[33:33 + r[32]]))
        sectors = [bytearray()]
        for r in [dot, dotdot] + rest:
            if len(sectors[-1]) + len(r) > DATA:
                sectors.append(bytearray())
            sectors[-1] += r
        size = len(sectors) * DATA
        lba = self.root_lba if size <= self.root_size else self.sectors
        for r in (dot, dotdot):
            r[2:10] = struct.pack('<I', lba) + struct.pack('>I', lba)
            r[10:18] = struct.pack('<I', size) + struct.pack('>I', size)
        sectors[0][:len(dot)] = dot
        sectors[0][len(dot):len(dot) + len(dotdot)] = dotdot
        for i, sec in enumerate(sectors):
            self.write_data(lba + i, bytes(sec + bytes(DATA - len(sec))))
        for i in range(len(sectors), self.root_size // DATA):
            if lba == self.root_lba:
                self.write_data(lba + i, bytes(DATA))
        pvd = bytearray(self.data(16))
        pvd[156 + 2:156 + 10] = struct.pack('<I', lba) + struct.pack('>I', lba)
        pvd[156 + 10:156 + 18] = struct.pack('<I', size) + struct.pack('>I', size)
        self.write_data(16, bytes(pvd))
        # the path tables: one entry, the root
        for at, fmt in ((struct.unpack('<I', pvd[140:144])[0], '<I'), (struct.unpack('>I', pvd[148:152])[0], '>I')):
            pt = bytearray(self.data(at))
            pt[2:6] = struct.pack(fmt, lba)
            self.write_data(at, bytes(pt))
        self.root_lba, self.root_size = lba, size
        # the file table again
        self.files = {}
        off = 0
        for i, sec in enumerate(sectors):
            o = 0
            while o < len(sec):
                r = sec[o:o + sec[o]]
                name = r[33:33 + r[32]]
                if name not in (b'\x00', b'\x01'):
                    self.files[name.decode().split(';')[0]] = (i * DATA + o, struct.unpack('<I', r[2:6])[0],
                                                                struct.unpack('<I', r[10:14])[0])
                o += sec[o]

    def finish(self):
        """volume size in the primary volume descriptor"""
        d = bytearray(self.data(16))
        d[80:88] = struct.pack('<I', self.sectors) + struct.pack('>I', self.sectors)
        self.write_data(16, bytes(d))
        return bytes(self.raw)

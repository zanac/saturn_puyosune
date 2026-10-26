"""The .SPR files of the disc: sprite sets.

u16 count, u16 0, count x (u16 w, u16 h, u16 offset/8, u16 VDP1 size word
(w/8 << 8 | h)), then the 4bpp pixels of all the cells, compressed
(cmpdec). The same format as the sprite sets of the arcade cartridge.

On the disc a set may grow: a cell can be made wider, its pixels then go
after the others.
"""
import struct

import cmpdec
import cmpenc


class Spr:
    def __init__(self, blob):
        n = struct.unpack('>H', blob[:2])[0]
        self.head = bytes(blob[2:4])
        self.desc = [list(struct.unpack('>4H', blob[4 + i * 8:12 + i * 8])) for i in range(n)]
        pix, end = cmpdec.decompress(blob, 4 + n * 8)
        self.pix = bytearray(pix)

    def get(self, k):
        w, h, o, s = self.desc[k]
        out = []
        for b in self.pix[o * 8:o * 8 + w * h // 2]:
            out += [b >> 4, b & 15]
        return w, h, out

    def put(self, k, px, w=None, h=None):
        """new pixels of cell k; with w/h, a cell of a new size (its pixels
        go at the end)"""
        ow, oh, o, s = self.desc[k]
        w = ow if w is None else w
        h = oh if h is None else h
        assert w % 8 == 0 and len(px) == w * h and max(px) < 16
        if (w, h) != (ow, oh):
            o = (len(self.pix) + 7) // 8
            self.pix.extend(bytes(o * 8 - len(self.pix) + w * h // 2))
            self.desc[k] = [w, h, o, (w // 8) << 8 | h]
        self.pix[o * 8:o * 8 + w * h // 2] = bytes((px[i] << 4) | px[i + 1] for i in range(0, w * h, 2))

    def blob(self):
        out = struct.pack('>H', len(self.desc)) + self.head
        out += b''.join(struct.pack('>4H', *d) for d in self.desc)
        return out + cmpenc.compress(bytes(self.pix))

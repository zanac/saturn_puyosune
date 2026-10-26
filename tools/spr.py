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

    def repack(self, cells):
        """cells: {k: (w, h, pixels)} new cells (any size); all the cells
        are laid out again one after the other. The pixels may not take
        more room than the original set (the game gives each set the
        room of the original in video memory)."""
        room = len(self.pix)
        allc = []
        for k in range(len(self.desc)):
            allc.append(cells[k] if k in cells else self.get(k))
        pix = bytearray()
        for k, (w, h, px) in enumerate(allc):
            assert w % 8 == 0 and len(px) == w * h and max(px) < 16, k
            o = len(pix) // 8
            pix += bytes((px[i] << 4) | px[i + 1] for i in range(0, w * h, 2))
            pix += bytes(-len(pix) % 8)
            self.desc[k] = [w, h, o, (w // 8) << 8 | h]
        assert len(pix) <= room, 'sprite set too big: %d > %d' % (len(pix), room)
        self.pix = pix

    def blob(self):
        out = struct.pack('>H', len(self.desc)) + self.head
        out += b''.join(struct.pack('>4H', *d) for d in self.desc)
        return out + cmpenc.compress(bytes(self.pix))

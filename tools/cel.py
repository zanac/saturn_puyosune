"""The background pictures of the disc: a .CEL file holds the 8x8 cells
of a VDP2 plane, 8bpp (4 bytes of header, c0 10 00 00, then the cells
compressed as cmpdec), the .MAP file of the same name the 64x64 plane
map (compressed; one word per position: the cell number in units of 32
bytes).
"""
import struct

import cmpdec
import cmpenc

HEAD = b'\xc0\x10\x00\x00'


class Plane:
    def __init__(self, cel, map_):
        assert cel[:4] == HEAD, cel[:4].hex()
        self.cells = bytearray(cmpdec.decompress(cel, 4)[0])
        m = cmpdec.decompress(map_, 0)[0]
        self.map = list(struct.unpack('>%dH' % (len(m) // 2), m))
        self.w = 64

    def _at(self, x, y):
        v = self.map[(y // 8) * self.w + x // 8]
        return v * 32 + (y % 8) * 8 + x % 8

    def get(self, x, y):
        return self.cells[self._at(x, y)]

    def put(self, x, y, v):
        self.cells[self._at(x, y)] = v

    def shared(self, x0, y0, x1, y1):
        """cells of the box also used elsewhere in the map"""
        inside = {self.map[(y // 8) * self.w + x // 8] for y in range(y0, y1) for x in range(x0, x1)}
        out = set()
        for i, v in enumerate(self.map):
            x, y = (i % self.w) * 8, (i // self.w) * 8
            if v in inside and not (x0 - 7 <= x < x1 and y0 - 7 <= y < y1):
                out.add(v)
        return out

    def cel(self):
        return HEAD + cmpenc.compress(bytes(self.cells))

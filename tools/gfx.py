"""Sprite sets of the cartridge and English lettering drawn into them.

A sprite set: u16 count, u16 0, count x (u16 w, u16 h, u16 offset/8,
u16 VDP1 size word), then 4bpp pixels, raw or compressed (cmpdec). Sets are
rewritten in place: a raw set keeps its size, a compressed one must fit in
the room up to the next set.
"""
import struct

import cmpdec
import cmpenc


class SpriteSet:
    def __init__(self, reg, at, room=None, compressed=None, bpp=4):
        self.reg, self.at, self.bpp = reg, at, bpp
        n = struct.unpack('>H', reg[at:at + 2])[0]
        self.desc = [list(struct.unpack('>4H', reg[at + 4 + i * 8:at + 12 + i * 8])) for i in range(n)]
        self.base = at + 4 + n * 8
        size = max(o * 8 + w * h * bpp // 8 for w, h, o, s in self.desc)
        if compressed is None:
            compressed = reg[self.base] != 0
        self.compressed = compressed
        if compressed:
            pix, end = cmpdec.decompress(reg, self.base)
            self.room = room
        else:
            pix = reg[self.base:self.base + size]
        self.pix = bytearray(pix)
        self.size = size

    def get(self, k):
        w, h, o, s = self.desc[k]
        if self.bpp == 8:
            return w, h, list(self.pix[o * 8:o * 8 + w * h])
        out = []
        for b in self.pix[o * 8:o * 8 + w * h // 2]:
            out += [b >> 4, b & 15]
        return w, h, out

    def put(self, k, px):
        w, h, o, s = self.desc[k]
        assert len(px) == w * h
        if self.bpp == 8:
            self.pix[o * 8:o * 8 + w * h] = bytes(px)
            return
        self.pix[o * 8:o * 8 + w * h // 2] = bytes((px[i] << 4) | px[i + 1] for i in range(0, w * h, 2))

    def write(self):
        """back into the region (bytearray)"""
        if not self.compressed:
            self.reg[self.base:self.base + self.size] = self.pix
            return
        blob = cmpenc.compress(bytes(self.pix))
        if self.base + len(blob) > self.room:
            blob = cmpenc.compress_optimal(bytes(self.pix))
            assert cmpdec.decompress(blob)[0] == bytes(self.pix)
        assert self.base + len(blob) <= self.room, 'sprite set at %x too big' % self.at
        self.reg[self.base:self.room] = blob + bytes(self.room - self.base - len(blob))


class Canvas:
    def __init__(self, w, h, px=None):
        self.w, self.h = w, h
        self.px = list(px) if px is not None else [0] * (w * h)

    def clear(self, x0, y0, x1, y1, keep=()):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                if self.px[y * self.w + x] not in keep:
                    self.px[y * self.w + x] = 0

    def blit(self, cell, cw, ch, x, y, colmap):
        for yy in range(ch):
            for xx in range(cw):
                v = cell[yy * cw + xx]
                if v and 0 <= x + xx < self.w and 0 <= y + yy < self.h:
                    c = colmap.get(v, v) if isinstance(colmap, dict) else colmap(v, yy)
                    if c is not None:
                        self.px[(y + yy) * self.w + x + xx] = c


class Font:
    """glyphs: {char: (advance, cell w, cell h, cell pixels)}"""
    def __init__(self, glyphs, height):
        self.g, self.height = glyphs, height

    def width(self, text, track=0):
        return sum(self.g[c][0] + track for c in text) - track if text else 0

    def draw(self, cv, text, x, y, colmap, track=0):
        for c in text:
            adv, cw, ch, cell = self.g[c]
            cv.blit(cell, cw, ch, x, y, colmap)
            x += adv + track
        return x


def pc_font(build_font):
    """the font of the PC patch (from build.pc_font): outline 1, AA 9, body 15"""
    g = {}
    for code, (adv, cell) in build_font.items():
        ch = '…' if code == 0x7f else '♪' if code == 0x80 else chr(code)
        g[ch] = (adv, 16, 16, cell)
    return Font(g, 16)


BLOCK_ORDER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .\u00b7:\'"'


def block_font(dialogue_set):
    """the arcade 8x16 block letters (first entries of the dialogue set)"""
    g = {}
    for i, ch in enumerate(BLOCK_ORDER):
        w, h, px = dialogue_set.get(i)
        g[ch] = (8, w, h, px)
    # the apostrophe, narrower; a hyphen made in the same shading
    adv, w, h, px = g["'"]
    g["'"] = (4, w, h, [px[y * w + x + 2] if x + 2 < w else 0 for y in range(h) for x in range(w)])
    hy = [0] * (8 * 16)
    for x, (a, b, c) in enumerate(((6, 5, 0), (10, 8, 4), (10, 8, 4), (10, 8, 4), (10, 8, 4), (6, 4, 2))):
        hy[7 * 8 + x + 1], hy[8 * 8 + x + 1] = a, b
        if c:
            hy[9 * 8 + x + 1] = c
    g['-'] = (8, 8, 16, hy)
    return Font(g, 16)

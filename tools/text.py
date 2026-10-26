"""The texts of the program: the font of the patch in the two text sprite
sets, proportional spacing in the text engine, and the win quotes.

The program (file "0", loaded at 0x06004000) runs the same text engine as
the arcade game: a text is a list of words, a character code is the index
of its cell in the sprite set, 0xffxx are commands. FONT.SPR is the set
of the win quotes (cells 0x00-0x2f are 8x16 block letters the results
and time screens use, kana from 0x30), FONT_DM.SPR the set of the story
scenes and the rules demo (16x16 from 0, balloon pieces from 0x150).

The English glyphs go at their ASCII codes; in FONT.SPR the codes
0x20-0x2f of the punctuation go to unused kana cells (0x90-0x9f) and the
quotes use those codes. The new texts and the table of advance widths go
in the free end of the program file (0x060d1000-0x060dc000: zeros up to
the heap, not referenced by the code).
"""
import struct

import grpdat
from quotes import QUOTES
from spr import Spr

BASE = 0x06004000
FREE_FROM, FREE_TO = 0x060d1000, 0x060dc000

EXTRA = {'…': 0x7f, '♪': 0x80}
SPACE_W = 6
LOW = {c: 0x90 + c - 0x20 for c in range(0x20, 0x30)}    # FONT.SPR only
PROP = 0x40          # text engine flag (FF0F): x advance from the widths

QUOTE_FIRST, QUOTE_LAST = 0x0607166c, 0x06072850
QUOTE_HEAD = bytes.fromhex('ff0f0500ff1100100018ff0600300098')
TEXT_X, TEXT_Y = 0x30, 0x98
QUOTE_W = 244

PC_COLOURS = {0: 0, 1: 1, 12: 9, 15: 15}


def code(ch):
    return EXTRA[ch] if ch in EXTRA else ord(ch)


def be16(b, a):
    return struct.unpack('>H', b[a:a + 2])[0]


class Program:
    """the program file, with room for new data in its free end"""

    def __init__(self, blob):
        self.b = bytearray(blob)
        self.base = BASE
        assert not any(self.b[FREE_FROM - BASE:FREE_TO - BASE])
        self.free = FREE_FROM

    def place(self, blob, align=2):
        at = (self.free + align - 1) & ~(align - 1)
        assert at + len(blob) <= FREE_TO, 'free area of the program full'
        self.b[at - BASE:at - BASE + len(blob)] = blob
        self.free = at + len(blob)
        return at

    def words(self, at):
        """the words of the text at CPU address `at`, to FF00"""
        a = at - BASE
        w = []
        while True:
            x = be16(self.b, a)
            w.append(x)
            a += 2
            if x == 0xff00:
                return w

    def pointers(self, value):
        pat = struct.pack('>I', value)
        return [i for i in range(0, len(self.b) - 3, 2) if self.b[i:i + 4] == pat]

    def repoint(self, old, new, count=None):
        refs = self.pointers(old)
        assert refs and (count is None or len(refs) == count), (hex(old), len(refs))
        for r in refs:
            self.b[r:r + 4] = struct.pack('>I', new)


# --- font --------------------------------------------------------------------

def glyphs(grp):
    """{code: (advance, 16x16 cell)} of the patch's font (grp.dat entry 21,
    ASCII order, 30 the ellipsis); the note from a quote picture"""
    ents = grpdat.entries(grp)
    o, s = ents[21]
    d = grp[o:o + s]
    t, frames, parts, base = grpdat.parse(d)
    out = {}
    for k in list(range(0x21, 0x7f)) + [30]:
        pw, ph, px, py, a, fl, off = parts[k]
        src = d[base + off:base + off + pw * ph]
        cell = [0] * 256
        for y in range(ph):
            for x in range(pw):
                if px + x < 16 and py + y < 16:
                    cell[(py + y) * 16 + px + x] = PC_COLOURS[src[y * pw + x]]
        out[EXTRA['…'] if k == 30 else k] = (pw, cell)
    # the note: only in the quote pictures (entry 1, quote 74, end of line 1)
    o, s = ents[1]
    w, h, px = grpdat.sprites(grp[o:o + s])[74]
    cell = [0] * 256
    for y in range(16):
        for x in range(11):
            cell[y * 16 + 1 + x] = PC_COLOURS[px[y * w + 185 + x]]
    out[EXTRA['♪']] = (11, cell)
    out[0x20] = (SPACE_W, [0] * 256)
    return out


def font_set(blob, font, redirect):
    s = Spr(blob)
    for c, (adv, cell) in font.items():
        e = redirect.get(c, c)
        assert tuple(s.desc[e][:2]) == (16, 16), (hex(c), hex(e))
        s.put(e, cell)
    return s.blob()


def widths_table(font):
    widths = bytearray([16] * 256)
    for c, (adv, cell) in font.items():
        widths[c] = adv
    for c, e in LOW.items():
        widths[e] = font[c][0]
    return widths


# --- text engine ---------------------------------------------------------------

def asm(*words):
    return struct.pack('>%dH' % len(words), *words)


def patch_engine(prog, widths_at):
    """0x06028760-0x060287b6: the glyph table load (spacing 0, 0) made
    shorter, and the advance: with flag 0x40 the x advance of a character
    is widths[code], otherwise as before. r8 the text object, r10 the code,
    r11 its copy, r13/r14 the x/y spacing, r9 the glyph base."""
    a = 0x06028760 - BASE
    old = bytes(prog.b[a:0x060287b6 - BASE])
    assert old[:4] == bytes.fromhex('61d22118') and old[-6:] == bytes.fromhex('62d2312c1818')
    new = asm(
        # 06028760: spacing 0, 0: w and h from the glyph table
        0x61d2,     # mov.l @r13,r1
        0x2118,     # tst r1,r1
        0x8b10,     # bf 0x06028788
        0x61e2,     # mov.l @r14,r1
        0x2118,     # tst r1,r1
        0x8b0d,     # bf 0x06028788
        0x62b1,     # mov.w @r11,r2
        0x6192,     # mov.l @r9,r1
        0x622d,     # extu.w r2,r2
        0x321c,     # add r1,r2
        0x4208,     # shll2 r2
        0x4200,     # shll r2               ; 8 bytes an entry
        0xd03a,     # mov.l @(0x06028864),r0 ; the glyph table
        0x012d,     # mov.w @(r0,r2),r1
        0x7002,     # add #2,r0
        0x002d,     # mov.w @(r0,r2),r0
        0x4128,     # shll16 r1
        0x2d12,     # mov.l r1,@r13
        0x4028,     # shll16 r0
        0x2e02,     # mov.l r0,@r14
        # 06028788: advance
        0xd12c,     # mov.l @(0x0602883c),r1 ; the flags
        0x6011,     # mov.w @r1,r0
        0xc802,     # tst #2,r0
        0x8b0d,     # bf 0x060287ac (vertical)
        0xc840,     # tst #64,r0
        0x8d05,     # bt/s 0x060287a0 (fixed)
        0x62d2,     # mov.l @r13,r2
        0xd004,     # mov.l @(0x060287a8),r0 ; widths
        0x62ad,     # extu.w r10,r2
        0x022c,     # mov.b @(r0,r2),r2
        0x622c,     # extu.b r2,r2
        0x4228,     # shll16 r2
        # 060287a0
        0x5188,     # mov.l @(32,r8),r1
        0x312c,     # add r2,r1
        0xa007,     # bra 0x060287b6
        0x1818,     # mov.l r1,@(32,r8)
    ) + struct.pack('>I', widths_at) + asm(
        # 060287ac
        0x5189,     # mov.l @(36,r8),r1
        0x62e2,     # mov.l @r14,r2
        0x312c,     # add r2,r1
        0x1819,     # mov.l r1,@(36,r8)
        0x0009,     # nop
    )
    assert len(new) == len(old), (len(new), len(old))
    prog.b[a:a + len(new)] = new


# --- win quotes ----------------------------------------------------------------

def encode_quote(text, font):
    w = [0xff0f, 0x0500 | PROP,     # clear flags 5, set proportional
         0xff11, 0x0000, 0x0018,    # spacing: x from the widths, 24 a line
         0xff06, TEXT_X, TEXT_Y]
    for k, line in enumerate(text.split('/')):
        if k:
            w.append(0xff02)
        width = 0
        for ch in line:
            w.append(LOW.get(code(ch), code(ch)))
            width += font[code(ch)][0]
        assert width <= QUOTE_W, 'line too wide: %r (%d)' % (line, width)
    w.append(0xff00)
    return struct.pack('>%dH' % len(w), *w)


def quote_starts(prog):
    out = []
    a = QUOTE_FIRST
    while a <= QUOTE_LAST:
        assert prog.b[a - BASE:a - BASE + len(QUOTE_HEAD)] == QUOTE_HEAD, hex(a)
        out.append(a)
        a += 2 * len(prog.words(a))
        while a <= QUOTE_LAST and prog.b[a - BASE:a - BASE + 2] != b'\xff\x0f':
            a += 2
    return out


def build(files, grp):
    """files: {name: bytes}, changed in place. Returns (Program, font,
    widths, log); the program is written back by the caller."""
    font = glyphs(grp)
    files['FONT.SPR'] = font_set(files['FONT.SPR'], font, LOW)
    files['FONT_DM.SPR'] = font_set(files['FONT_DM.SPR'], font, {})
    prog = Program(files['0'])
    widths = widths_table(font)
    patch_engine(prog, prog.place(bytes(widths), 4))
    starts = quote_starts(prog)
    assert len(starts) == len(QUOTES), len(starts)
    size = 0
    for at, text in zip(starts, QUOTES):
        blob = encode_quote(text, font)
        size += len(blob)
        prog.repoint(at, prog.place(blob), 1)
    log = ['text font in FONT.SPR, FONT_DM.SPR; %d quotes, %x bytes' % (len(starts), size)]
    return prog, font, widths, log

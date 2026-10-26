"""The ending (after the last stage): Arle and Carbuncle on the terrace
under the moon, with short lines written down the side of the screen in
a kana font (END_MES.SPR, the arcade set 228, 55 cells of 16x16).

A line is an entry of 32 words (speaker, 26 cells, two columns of 13);
the object script at 0x060613f0 copies each cell into a child object
and moves down the column, a child per character, each appearing two
frames after the one before (the delay chain at 0x06061638) and sliding
away at the end.

In English the lines are written across, in the PC font, proportional:
the kana cells become the glyphs the English lines use, the entries are
rebuilt (speaker, then cell, x, y of each glyph) in the free area, and
the column script becomes one that takes the x and y of each glyph from
the entry. Arle (speaker 0) speaks on the left, under the moon's left;
the other side on the right.
"""
import struct

from gfx import Canvas
from spr import Spr

STAR = 52                     # the star of the kana font, kept
ENTRY_TABLE = 0x060616ec      # 18 pointers
SCRIPT = 0x060613f0           # the column script, replaced by a jump
CHILD = 0x0606169c            # body of the character objects
CHILD_END = 0x060616ec
LOOP = 0x060613cc              # the script before the columns

LINES = [   # (speaker, English), in the order of the entries
    (1, "I'll get a nice, even tan~!"),
    (1, "Gyoeeeeh~~!!"),
    (0, "That was a really heated battle…"),
    (1, "Guuu…"),
    (0, "Carby…"),
    (1, "Gu! Gu! Gu! Gu!"),
    (0, "Hm?"),
    (1, "Guuu!"),
    (0, "Ka…thunk!"),
    (0, "Light!"),
    (1, "Woo-hooo★"),
    (0, "Whoa!!"),
    (1, "Uhohohoho★"),
    (0, "Why you… Satan!!"),
    (1, "Nuhuhuhuhu★"),
    (0, "Gyaaaaah!!"),
    (1, "Yahoo-hoo★"),
    (0, "So it ends like this, after all!?"),
]
MAX_GLYPHS = 41
WIDTH = 150                   # of a block of text
LEFT_X, RIGHT_X = 8, 312 - WIDTH
TOP_Y, LINE_H = 16, 16        # centre of the first line
DELAY = 2                     # frames between characters


def wrap(text, adv):
    lines = ['']
    for word in text.split(' '):
        t = (lines[-1] + ' ' + word).strip()
        if sum(adv(c) for c in t) <= WIDTH:
            lines[-1] = t
        else:
            lines.append(word)
    assert all(sum(adv(c) for c in l) <= WIDTH for l in lines), text
    return lines


def words(*w):
    return struct.pack('>%dH' % len(w), *w)


def build(files, program, pc):
    ss = Spr(files['END_MES.SPR'])
    base, prog, place = program.base, program.b, lambda b, align=2: program.place(b, align)
    star = ss.get(STAR)[2]
    chars = sorted(set(''.join(t for s, t in LINES)) - {' '})
    assert len(chars) <= len(ss.desc), len(chars)
    cell = {}
    for k, ch in enumerate(chars):
        if ch == '★':
            px = star
        else:
            cv = Canvas(16, 16)
            pc.draw(cv, ch, 0, 0, {})
            px = cv.px
        ss.put(k, px)
        cell[ch] = k
    files['END_MES.SPR'] = ss.blob()

    def adv(c):
        return 14 if c == '★' else pc.width(c) if c != ' ' else pc.width(' ')

    def pos(pt):
        return struct.unpack('>I', struct.pack('>i', pt))[0] >> 16 if pt < 0 else pt
    # the character objects: a delay chain and the body, relocated
    body = bytearray(prog[CHILD - base:CHILD_END - base])
    chain = words(*([0x0200, DELAY] * MAX_GLYPHS))
    at = place(chain, 4)
    new_body = at + len(chain)
    for i in range(0, len(body) - 3, 2):
        v = struct.unpack('>I', body[i:i + 4])[0]
        if CHILD <= v < CHILD_END:
            body[i:i + 4] = struct.pack('>I', new_body + v - CHILD)
    assert place(bytes(body), 4) == new_body
    starts = [at + 4 * k for k in range(MAX_GLYPHS)]
    # the column script: per glyph, cell, x, y from the entry, then a child
    s = words(0x1280, 0x2000, 0, 0, 0x1280, 0x2400, 0, 0)
    for k in range(MAX_GLYPHS):
        o = 2 + 6 * k
        s += words(0x11b0, 0x4000 | o, 0x11b0, 0x2000 | (o + 2), 0x11b0, 0x2400 | (o + 4))
        s += words(0xdb05, 0) + struct.pack('>I', starts[k])
    s += words(0x1240, 0xf700, 0, 0xff, 0x0300, 0) + struct.pack('>I', LOOP)
    script = place(s, 4)
    # entries: speaker, then (cell, x, y) per glyph; unused glyphs stay out
    # of sight (cell of the space, off screen)
    ptrs = []
    for speaker, text in LINES:
        lines = wrap(text, adv)
        glyphs = []
        for n, line in enumerate(lines):
            x = LEFT_X if speaker == 0 else RIGHT_X + WIDTH - sum(adv(c) for c in line)
            y = TOP_Y + LINE_H * n
            for c in line:
                if c != ' ':
                    glyphs.append((cell[c], x + 8, y))
                x += adv(c)
        assert len(glyphs) <= MAX_GLYPHS, text
        while len(glyphs) < MAX_GLYPHS:
            glyphs.append((cell[chars[0]], 0x200, 0x200))
        e = words(speaker) + b''.join(words(c, pos(x), pos(y)) for c, x, y in glyphs)
        ptrs.append(place(e, 2))
    t = ENTRY_TABLE - base
    for i, p in enumerate(ptrs):
        prog[t + 4 * i:t + 4 * i + 4] = struct.pack('>I', p)
    j = SCRIPT - base
    assert prog[j:j + 4] == b'\x11\x70\xf6\x00'
    prog[j:j + 8] = words(0x0300, 0) + struct.pack('>I', script)
    return ['ending: %d lines, %d glyphs' % (len(LINES), len(chars))]

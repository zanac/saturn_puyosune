"""The title of the name entry screen, said by the character you played:
Draco 'o-namae oshiete <3', Arle 'namae o irete ne!', Schezo 'namae ga
hoshii!!'.

Each title is 8 objects of the object script at 0x06068d28 (24 slots,
Draco, Arle, Schezo); a slot sets the x of its object and the cell it
shows, one 24x24 kana cell of ENTR01S.SPR (cells 24-39; the arcade set). The 16
cells are redrawn as English words (Enter, Tell, I want, your, name, me,
!) in the PC font, shaded like the kana; the heart and the '!!' are kept.
The words are wider than a kana, so the cell sizes and pixel offsets of
the set change (the pixels of the 16 cells keep their room).
"""
import struct

from gfx import Canvas
from spr import Spr

FIRST_CELL = 24
HEART, BANG2 = 35, 39            # kept as they are
SLOTS_FROM, SLOTS_TO = 0x06068d00, 0x06069100
SLOT_MARK = b'\x11\xc0\x40\x00'   # set the cell field; the x is 12 bytes before

WORDS = ['Enter', 'Tell', 'I want', 'your', 'name', 'me', '!']
TITLES = [                       # in the order of the slots
    ['Tell', 'me', 'your', 'name', HEART],        # Draco
    ['Enter', 'your', 'name', '!'],               # Arle
    ['I want', 'your', 'name', BANG2],            # Schezo
]
GAP = 5
H = 24


def shade(v, y):
    """PC font (outline 1, AA 9, body 15) to the colours of the kana"""
    if v == 1:
        return 2
    if v == 9:
        return 8
    return 15 if y < 11 else 10


def build(files, prog, pc):
    ss = Spr(files['ENTR01S.SPR'])
    base = prog.base
    prog = prog.b
    at = ss.desc[FIRST_CELL][2]
    end = ss.desc[BANG2][2] + 36
    kept = {k: ss.get(k)[2] for k in (HEART, BANG2)}
    pix = {}
    widths = {}
    for word in WORDS:
        tw = pc.width(word)
        w = (tw + 2 + 7) & ~7
        cv = Canvas(w, H)
        pc.draw(cv, word, 1, 5, lambda v, y: 6)       # shade below right
        pc.draw(cv, word, 0, 4, shade)
        pix[word] = (w, cv.px)
        widths[word] = tw
    for k in (HEART, BANG2):
        pix[k] = (24, kept[k])
        widths[k] = 24
    pix['blank'] = (8, [0] * (8 * H))
    # new cells: words, heart, !!, blank; the cells left over show the blank
    order = WORDS + [HEART, BANG2, 'blank']
    cell = {}
    for i, key in enumerate(order):
        w, px = pix[key]
        k = FIRST_CELL + i
        ss.desc[k] = [w, H, at, (w // 8) << 8 | H]
        cell[key] = k
        at += w * H // 16
    assert at <= end, (at, end)
    for k in range(FIRST_CELL + len(order), BANG2 + 1):
        ss.desc[k] = list(ss.desc[cell['blank']])
    for key in order:
        ss.put(cell[key], pix[key][1])
    files['ENTR01S.SPR'] = ss.blob()
    # the slots: x (16.16, the centre of the object) and the cell
    marks = []
    a = SLOTS_FROM - base
    while a < SLOTS_TO - base:
        if prog[a:a + 4] == SLOT_MARK:
            marks.append(a)
        a += 2
    assert len(marks) == 24, len(marks)
    for t, words in enumerate(TITLES):
        slots = marks[8 * t:8 * t + 8]
        total = sum(widths[w] for w in words) + GAP * (len(words) - 1)
        # the kana titles span 8 cells of 24 from the first centre
        x = 84 - total // 2
        # one baseline: the y of the first slot for every word
        assert prog[slots[0] - 8:slots[0] - 4] == b'\x12\xc0\xa4\x00'
        y0 = prog[slots[0] - 4:slots[0]]
        for i, a in enumerate(slots):
            prog[a - 4:a] = y0
            if i < len(words):
                w = words[i]
                k = cell[w]
                cw = pix[w][0]
                centre = x + cw // 2
                nxt = words[i + 1] if i + 1 < len(words) else None
                x += widths[w] + (1 if nxt == '!' else 3 if nxt in (HEART, BANG2) else GAP)
            else:
                k, centre = cell['blank'], 84
            assert prog[a - 16:a - 12] == b'\x12\xc0\x84\x00'
            prog[a - 12:a - 8] = struct.pack('>i', centre << 16)
            prog[a + 4:a + 6] = struct.pack('>H', k)
    return ['name entry titles: %d words' % len(WORDS)]

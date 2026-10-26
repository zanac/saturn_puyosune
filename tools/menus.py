"""English lettering of MENU_1.SPR (the course select of the 1 player
game; the same set as the arcade's): the screen titles are rows of 16x16
cells that the text engine puts at fixed places; the English line is
drawn across the same places and cut into the cells.
"""
from gfx import Canvas
from spr import Spr

# title cells: (first entry, screen x of each cell, English per run of cells)
TITLES = [
    (6, [51, 67, 83, 99, 123, 139, 155, 171, 187], ['SELECT', 'A GAME']),
    (15, [27, 43, 59, 75, 91, 107, 123, 147, 163, 179, 195, 211], ['SELECT YOUR', 'FIGHTER']),
]

TITLE_COLOURS = {1: 2, 9: 9, 15: 15}       # outline, AA, body
LABEL_COLOURS = {1: 1, 9: 9, 15: 15}


def runs(xs):
    """cells next to each other: [(first cell, x0, x1)]"""
    out = []
    for i, x in enumerate(xs):
        if out and out[-1][2] == x:
            out[-1][2] = x + 16
        else:
            out.append([i, x, x + 16])
    return out


def title(ss, first, xs, words, font):
    rs = runs(xs)
    assert len(rs) == len(words)
    x0 = xs[0]
    cv = Canvas(xs[-1] + 16 - x0, 16)
    for (i, a, b), word in zip(rs, words):
        track = 0
        while font.width(word, track) > b - a and track > -2:
            track -= 1
        wd = font.width(word, track)
        assert wd <= b - a, (word, wd, b - a)
        # the words meet at the gap between the runs of cells
        pos = a - x0 + (b - a - wd) if i == 0 and len(rs) > 1 else a - x0 if len(rs) > 1 else a - x0 + (b - a - wd) // 2
        font.draw(cv, word, pos, 0, TITLE_COLOURS, track)
    for k, x in enumerate(xs):
        px = []
        for y in range(16):
            px += cv.px[y * cv.w + x - x0:y * cv.w + x - x0 + 16]
        ss.put(first + k, px)


def label(ss, k, text, font, colours, track=0, align='center'):
    """a sprite that is only lettering: replaced by the English text"""
    w, h, old = ss.get(k)
    cv = Canvas(w, h)
    wd = font.width(text, track)
    assert wd <= w, (text, wd, w)
    x = (w - wd) // 2 if align == 'center' else 0
    font.draw(cv, text, x, (h - font.height) // 2, colours, track)
    ss.put(k, cv.px)


def segments(px, w, h, gap=6):
    cols = [any(px[y * w + x] for y in range(h)) for x in range(w)]
    out = []
    x = 0
    while x < w:
        if cols[x]:
            a = x
            while x < w and any(cols[x:x + gap]):
                x += 1
            out.append((a, x))
        x += 1
    return out


def build(files, pc, block):
    ss = Spr(files['MENU_1.SPR'])
    for first, xs, words in TITLES:
        title(ss, first, xs, words, pc)
    for k, text in ((76, 'EASY'), (77, 'NORMAL'), (78, 'HARD'),
                    (141, 'DRACO'), (142, 'ARLE'), (143, 'SCHEZO')):
        label(ss, k, text, block, BLOCK_COLOURS)
    practice(ss, pc)
    files['MENU_1.SPR'] = ss.blob()
    return ['course select: titles, difficulty, names, practice note']


# the block letters are shaded 2 (dark) .. 0xa; in white for the labels
BLOCK_COLOURS = {2: 1, 3: 1, 4: 2, 5: 9, 6: 9, 7: 15, 8: 15, 9: 15, 10: 15, 11: 15}


def practice(ss, pc):
    """the balloon of the practice game: '3 stages and it is over, this is
    the practice mode'"""
    w, h, px = ss.get(79)
    cv = Canvas(w, h, px)
    cv.clear(16, 8, 126, 56, keep=())
    # the dotted inner border is kept: redraw it from the original rows
    for x in range(w):
        for y in (7, 56):
            cv.px[y * w + x] = px[y * w + x]
    lines = [('Practice', {1: 3, 9: 13, 15: 12}),
             ('mode: just', {1: 3, 9: 13, 15: 15}),
             ('3 stages!', {1: 3, 9: 13, 15: 12})]
    for i, (t, col) in enumerate(lines):
        track = 0 if pc.width(t) <= 108 else -1
        wd = pc.width(t, track)
        assert wd <= 108, (t, wd)
        pc.draw(cv, t, 17 + (108 - wd) // 2, 8 + 16 * i, col, track)
    ss.put(79, cv.px)

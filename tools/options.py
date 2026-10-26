"""The options menu (OPTION.SPR): its labels drawn again in English with
the font of the patch.

The patch has these pictures in English too, but wider than their
cells; the game gives each sprite set the room of the original in video
memory, so a set may not grow: the cells are made as wide as their
English label and laid out again, the whole within the original room.
"""
from gfx import Canvas
from font import label
from spr import Spr

LABELS = {
    10: 'Key Config', 11: 'Difficulty', 12: 'Matches', 13: 'Sound',
    14: 'Battle Character', 15: 'Effects', 16: 'Cutscenes',
    17: 'Chain Animation', 18: 'Rules Explanation', 19: 'Exit',
    20: 'Margin Time', 21: 'Chain Limit', 22: 'Offsetting', 23: 'Nuisance',
    24: 'Puyos to Clear', 25: 'Scoring', 26: 'Reset Rules', 27: 'Music',
    28: 'Sound Effects', 29: 'Voice', 30: 'Watch Cutscenes', 31: 'Gallery',
    32: 'High Scores', 33: 'Message from AAA',
    44: 'Easiest', 45: 'Very Easy', 46: 'Easy', 47: 'Normal', 48: 'Hard',
    49: 'Very Hard', 50: 'Mania', 51: 'Master', 52: 'Stereo', 53: 'Mono',
    54: 'Choose', 55: 'Arle & Schezo', 56: 'Different', 57: 'All Same',
    58: 'Yes', 59: 'No', 60: 'SUN', 61: 'Normal', 62: 'Point Puyo',
    63: 'Hard Puyo', 64: 'Super Hard Puyo',
    65: 'Draco', 66: 'Skeleton T', 67: 'Harpy', 68: 'Choppun', 69: 'Incubus',
    70: 'Suketoudara', 71: 'Kikimora', 72: 'Nohoho', 73: 'Kodomo Dragon 1',
    74: 'Kodomo Dragon 2', 75: 'Witch 1', 76: 'Witch 2', 77: 'Zou Daimaoh 1',
    78: 'Zou Daimaoh 2', 79: 'Honeybee 1', 80: 'Honeybee 2', 81: 'Lagnus 1',
    82: 'Lagnus 2', 83: 'Rulue 1', 84: 'Rulue 2', 85: 'Schezo', 86: 'Arle',
    87: 'Satan 1', 88: 'Satan 2', 89: 'Ending 1', 90: 'Ending 2',
    91: 'Ending 3', 92: 'Opening',
    93: 'Options', 94: 'Versus Mode Rules', 95: 'Gallery', 96: 'New!',
}


def style(px):
    """colours of the original label: white (outline 1, body 15), or a
    grey one (the most used colour as body)"""
    used = {}
    for v in px:
        if v:
            used[v] = used.get(v, 0) + 1
    if used.get(15, 0) * 4 >= sum(used.values()):
        return {1: 1, 9: 12, 15: 15}
    body = max((n, c) for c, n in used.items() if c not in (1, 2))[1]
    return {1: 1, 9: body, 15: body}


def build(files, font):
    s = Spr(files['OPTION.SPR'])
    cells = {}
    for k, text in LABELS.items():
        w0, h, px = s.get(k)
        col = style(px)
        tw = font.width(text, -1)
        w = (tw + 1 + 7) & ~7
        cells[k] = (w, h, label(font, text, w, h, 'left', col, squeeze=1.0, track=-1))
    # the small labels by L and R in the title bar: the page on the left
    # (left aligned, may run toward the title) and on the right (inside
    # the original cell, right aligned: it ends at the R)
    for k, text, w, align in ((36, 'Rules', 48, 'left'), (38, 'Setup', 56, 'left'), (37, 'Art', 40, 'right')):
        w0, h, px = s.get(k)
        cells[k] = (w, h, label(font, text, w, h, align, style(px), squeeze=1.0, track=-1))
    # key config rows: 1P/2P A:x B:x C:x, the kanji left/right become L/R
    for k in (40, 41, 42, 43):
        w, h, px = s.get(k)
        cells[k] = (w, h, keys(font, w, h, px))
    s.repack(cells)
    files['OPTION.SPR'] = s.blob()
    return ['options menu: %d labels' % len(cells)]


def keys(font, w, h, px):
    """the three kanji (left / right) of a key config row as L / R"""
    cols = [any(px[y * w + x] for y in range(h)) for x in range(w)]
    segs = []
    x = 0
    while x < w:
        if cols[x]:
            a = x
            while x < w and cols[x]:
                x += 1
            segs.append((a, x))
        x += 1
    # 1 P A : K B : K C : K; the first kanji is always left, the last
    # always right, the middle one is the same as one of them
    assert len(segs) == 11, segs

    def glyph(i):
        a = segs[i][0]
        return [px[y * w + x] if x < w else 0 for y in range(h) for x in range(a, a + 16)]

    def diff(i, j):
        return sum(p != q for p, q in zip(glyph(i), glyph(j)))
    middle = 'L' if diff(7, 4) < diff(7, 10) else 'R'
    out = list(px)
    for i, letter in ((4, 'L'), (7, middle), (10, 'R')):
        a, b = segs[i]
        for y in range(h):
            for x in range(a, b):
                out[y * w + x] = 0
        cv = Canvas(16, h)
        lw = font.width(letter)
        font.draw(cv, letter, (16 - lw) // 2, (h - 16) // 2, {1: 1, 9: 12, 15: 15})
        for y in range(h):
            for x in range(16):
                if cv.px[y * 16 + x] and a + x < w:
                    out[y * w + a + x] = cv.px[y * 16 + x]
    return out


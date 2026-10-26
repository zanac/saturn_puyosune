"""In-game lettering that the patch does not have: the vertical tags at
the sides of the playfields and the handicap names of the 2 player game
(EFFECT.SPR, the same cells as the arcade set).
"""
from font import label
from gfx import Canvas
from spr import Spr

# 'n wins', 'join in', 'bring it on', 'challenger', 'no joining': English
# block letters turned a quarter to the right
TAGS = {128: 'WINS', 129: 'JOIN OK', 130: 'COME ON', 131: 'RIVAL', 132: 'NO ENTRY'}


def tags(ss, block):
    for i, text in TAGS.items():
        w, h, old = ss.get(i)
        wd = block.width(text)
        assert w == 16 and wd <= h, (text, wd, h)
        cv = Canvas(h, 16)
        block.draw(cv, text, (h - wd) // 2, 0, {})
        # turn right: column x of the sprite is row 15 - x of the line
        px = [cv.px[(15 - x) * h + y] for y in range(h) for x in range(16)]
        ss.put(i, px)


# the handicap levels of the 2 player game, top to bottom
HANDICAP = 66
LEVELS = ['Silver', 'Kids', 'Regular', 'Mania', 'Master']
INNER = (12, 68)                # inside the frame


def handicap(ss, pc):
    w, h, px = ss.get(HANDICAP)
    x0, x1 = INNER
    rows = [y for y in range(8, h - 8) if any(px[y * w + x] for x in range(x0, x1))]
    bands = []
    for y in rows:
        if bands and y - bands[-1][1] <= 2:
            bands[-1][1] = y
        else:
            bands.append([y, y])
    assert len(bands) == len(LEVELS), bands
    cv = Canvas(w, h, px)
    cv.clear(x0, 8, x1, h - 8)
    for (a, b), word in zip(bands, LEVELS):
        cell = label(pc, word, x1 - x0, 16, 'center', {1: 1, 9: 13, 15: 15}, squeeze=0.75)
        cv.blit(cell, x1 - x0, 16, x0, (a + b + 1) // 2 - 8, {})
    ss.put(HANDICAP, cv.px)


def build(files, pc, block):
    ss = Spr(files['EFFECT.SPR'])
    tags(ss, block)
    handicap(ss, pc)
    files['EFFECT.SPR'] = ss.blob()
    return ['side tags: %d; handicap levels' % len(TAGS)]

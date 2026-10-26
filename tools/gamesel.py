"""The game select screen: the TV screens of MENU_2.SPR (8bpp, cells 2-5:
1 player, 2 players, endless, options), white lettering on the blue of
the screen. The screen is filled with its blue again and the English is
drawn in the PC font, in the white and the light blues of the kana.
"""
from font import label
from spr import Spr

SCREEN = (18, 12, 94, 68)        # x0, y0, x1, y1 of the screen in a cell
BLUE = 27
SCREEN_COLOURS = range(24, 32)
INK = {1: BLUE, 9: 29, 15: 31}
GAMES = {2: ['1 Player', 'Puyo Puyo'], 3: ['2 Players', 'Puyo Puyo'],
         4: ['Endless', 'Puyo Puyo'], 5: ['Options']}


def build(files, pc):
    s = Spr(files['MENU_2.SPR'])
    assert s.head == b'\x00\x20'
    x0, y0, x1, y1 = SCREEN
    for k, lines in GAMES.items():
        w, h, off, size = s.desc[k]
        px = list(s.pix[off * 8:off * 8 + w * h])
        for y in range(y0, y1):
            for x in range(x0, x1):
                if px[y * w + x] in SCREEN_COLOURS:
                    px[y * w + x] = BLUE
        top = (y0 + y1) // 2 - 9 * len(lines)
        for n, line in enumerate(lines):
            cell = label(pc, line, x1 - x0 - 4, 16, 'center', INK, squeeze=0.8, track=-1 if pc.width(line) > 60 else 0)
            for yy in range(16):
                for xx in range(x1 - x0 - 4):
                    v = cell[yy * (x1 - x0 - 4) + xx]
                    if v and v != BLUE:
                        px[(top + 18 * n + yy) * w + x0 + 2 + xx] = v
        s.pix[off * 8:off * 8 + w * h] = bytes(px)
    files['MENU_2.SPR'] = s.blob()
    return ['game select: %d screens' % len(GAMES)]

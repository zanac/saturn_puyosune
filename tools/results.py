"""The results screen after the last game (VS, SCORE, CLEAR TIME, MAX
chains, CONTINUE), the same as the arcade's.

RS_WAKU.SPR is one 8bpp picture: 'MAX' is followed by the kanji 'rensa'
(chain); they become CHAIN, in the letters of the picture itself (C, A,
I, N), with an H made of the U and the bar of the A.

FONT_RS.SPR has the opponent names (VS ...) and Total: the patch has
them, but cut where a name is wider than the cell; they are drawn again
in the PC font, right aligned like the PC ones; a name wider than its
cell is drawn closer and then narrowed to fit.
"""
from gfx import Canvas
from spr import Spr

# letter cells (8x14) in the picture: x, y of the top left
CELL = {'C': (136, 109), 'A': (160, 109), 'I': (192, 109), 'N': (152, 189), 'U': (184, 189)}
ROW_Y = 149                  # the MAX line
KANJI = (160, 145, 200, 166)  # cleared
CHAIN_X = 163

NAMES = ['Skeleton T', 'Harpy', 'Choppun', 'Draco', 'Incubus', 'Suketoudara',
         'Kikimora', 'Nohoho', 'Kodomo Dragon', 'Witch', 'Zou Daimaoh',
         'Honeybee', 'Lagnus', 'Rulue', 'Schezo', 'Satan', 'Arle', 'Carbuncle',
         'Total']
NAME_COLOURS = {1: 1, 9: 12, 15: 15}


def picture(files):
    s = Spr(files['RS_WAKU.SPR'])
    w, h = 320, 240
    assert s.head == b'\x00\x20' and tuple(s.desc[0][:2]) == (w, h)
    px = list(s.pix[:w * h])

    def cell(x0, y0):
        return [px[(y0 + y) * w + x0:(y0 + y) * w + x0 + 8] for y in range(14)]
    letters = {k: cell(*v) for k, v in CELL.items()}
    u, a, n = letters['U'], letters['A'], letters['N']
    letters['H'] = u[0:6] + a[7:9] + u[6:10] + n[12:14]
    out = list(px)
    x0, y0, x1, y1 = KANJI
    for y in range(y0, y1):
        for x in range(x0, x1):
            out[y * w + x] = 0
    for i, ch in enumerate('CHAIN'):
        for y, row in enumerate(letters[ch]):
            for x, v in enumerate(row):
                out[(ROW_Y + y) * w + CHAIN_X + 8 * i + x] = v
    s.pix[:w * h] = bytes(out)
    files['RS_WAKU.SPR'] = s.blob()


def names(files, pc):
    ss = Spr(files['FONT_RS.SPR'])
    for i, name in enumerate(NAMES, 12):
        w, h, off, size = ss.desc[i]
        track = 0 if pc.width(name) <= w - 1 else -1
        tw = pc.width(name, track)
        big = Canvas(tw + 2, h)
        pc.draw(big, name, 0, 0, NAME_COLOURS, track)
        cv = Canvas(w, h)
        if tw + 1 <= w - 1:
            for y in range(h):
                for x in range(tw + 1):
                    cv.px[y * w + w - 2 - tw + x] = big.px[y * big.w + x]
        else:
            for y in range(h):
                for x in range(w - 1):
                    cv.px[y * w + x] = big.px[y * big.w + x * (tw + 1) // (w - 1)]
        ss.put(i, cv.px)
    files['FONT_RS.SPR'] = ss.blob()


def build(files, pc):
    picture(files)
    names(files, pc)
    return ['results screen: MAX CHAIN, %d names' % len(NAMES)]

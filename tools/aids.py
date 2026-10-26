"""The 'Act Against AIDS' screen of the attract mode: the logo of the 1990s
Japanese charity campaign, with its slogan under the line. The logo, the
'Act Against AIDS' lettering and the credit stay; the slogan (yuuki to
aiki, 'courage and love') and the three lines (learn about AIDS, prevent
AIDS, live with AIDS) are redrawn in English in the PC font, dark grey on
white like the picture. AAA.SPR: one 4bpp 320x240 picture, the same as
the arcade's.
"""
from gfx import Canvas
from spr import Spr

WHITE = 15
CLEAR = (60, 155, 260, 226)          # the Japanese, below the line
BULLET = (114, 175, 124, 186)        # one of the round bullets, kept
TITLE = ('Courage and Love', 157, 156)
LINES = ['Learn about AIDS', 'Prevent AIDS', 'Live with AIDS']
LINE_Y, PITCH, CENTRE = 174, 16, 157


def ink(v, y):
    if v == 15:
        return 10
    if v == 9:
        return 12
    return None


def build(files, pc):
    ss = Spr(files['AAA.SPR'])
    w, h, px = ss.get(0)
    cv = Canvas(w, h, px)
    bx0, by0, bx1, by1 = BULLET
    bullet = [px[y * w + x] for y in range(by0, by1) for x in range(bx0, bx1)]
    x0, y0, x1, y1 = CLEAR
    for y in range(y0, y1):
        for x in range(x0, x1):
            cv.px[y * w + x] = WHITE
    text, cx, ty = TITLE
    pc.draw(cv, text, cx - pc.width(text) // 2, ty, ink)
    bw = bx1 - bx0
    # the block of bullet and lines, centred
    left = CENTRE - (bw + 4 + max(pc.width(t) for t in LINES)) // 2
    for i, line in enumerate(LINES):
        y = LINE_Y + PITCH * i
        for yy in range(by1 - by0):
            for xx in range(bw):
                cv.px[(y + 2 + yy) * w + left + xx] = bullet[yy * bw + xx]
        pc.draw(cv, line, left + bw + 4, y, ink)
    ss.put(0, cv.px)
    files['AAA.SPR'] = ss.blob()
    return ['Act Against AIDS screen: slogan in English']

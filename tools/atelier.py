"""The atelier (gallery) of the options: the information page
(AT_SAKAI.SPR, a 16bpp picture) has 'mainichi asobu to e ga fueru yo'
(play every day and there will be more pictures) written across its top
left in big white letters. The letters are painted over (each column
blended from the row above to the row below them) and the English is
written in the PC font, white with a black outline, like the Japanese.
"""
from gfx import Canvas
from spr import Spr

BAND = (4, 7, 218, 41)            # x0, y0, x1, y1 of the Japanese
LINES = ['Play every day and', 'more pictures will appear!']
X, Y = 8, 9
WHITE, BLACK = 0xffff, 0x8000


def build(files, pc):
    s = Spr(files['AT_SAKAI.SPR'])
    w, h, off, size = s.desc[0]
    assert (w, h) == (288, 208)
    p = s.pix[off * 8:off * 8 + w * h * 2]
    v = [p[i] << 8 | p[i + 1] for i in range(0, len(p), 2)]
    x0, y0, x1, y1 = BAND
    for x in range(x0, x1):
        a, b = v[(y0 - 1) * w + x], v[y1 * w + x]
        for y in range(y0, y1):
            t = (y - y0 + 1) / (y1 - y0 + 1)
            c = 0x8000
            for sh in (0, 5, 10):
                ca, cb = (a >> sh) & 31, (b >> sh) & 31
                c |= int(round(ca + (cb - ca) * t)) << sh
            v[y * w + x] = c
    cv = Canvas(w, 2 + 16 * len(LINES))
    for n, line in enumerate(LINES):
        assert X + pc.width(line) <= w
        pc.draw(cv, line, 0, 16 * n, {1: 1, 9: 15, 15: 15})
    for y in range(cv.h):
        for x in range(cv.w):
            c = cv.px[y * cv.w + x]
            if c:
                v[(Y + y) * w + X + x] = WHITE if c == 15 else BLACK
    s.pix[off * 8:off * 8 + w * h * 2] = b''.join(bytes((c >> 8, c & 255)) for c in v)
    files['AT_SAKAI.SPR'] = s.blob()
    return ['atelier: information page']

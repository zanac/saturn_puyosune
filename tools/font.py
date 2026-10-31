"""The font of the Puyo Nexus patch (grp.dat entry 21: 16x16 cells in
ASCII order, proportional), and English labels drawn with it into the
cells of a sprite set.
"""
from gfx import Canvas, Font

# colours of the patch's font pictures: outline 1, shading 12, body 15
PC_COLOURS = {0: 0, 1: 1, 12: 9, 15: 15}
SPACE_W = 6
ELLIPSIS = '…'


def from_glyphs(glyphs):
    """the Font of the patch's glyphs (text.glyphs(), from assets.py)"""
    from text import EXTRA
    g = {}
    for c, (adv, cell) in glyphs.items():
        if 0x21 <= c < 0x7f:
            g[chr(c)] = (adv, 16, 16, cell)
        elif c == EXTRA[ELLIPSIS]:
            g[ELLIPSIS] = (adv, 16, 16, cell)
    g[' '] = (SPACE_W, 16, 16, [0] * 256)
    return Font(g, 16)


# the patch draws menu labels in these colours (outline, shading, body)
MENU_COLOURS = {1: 1, 9: 12, 15: 15}


def label(font, text, w, h, align='left', colours=MENU_COLOURS, y=None, squeeze=0.8, track=0):
    """pixels of a w x h cell with text: tracking -1 if needed, then the
    picture narrowed down to `squeeze` of its width at most"""
    if font.width(text, track) > w:
        track = -1
    tw = font.width(text, track)
    cv = Canvas(tw, 16)
    font.draw(cv, text, 0, 0, colours, track)
    if tw > w:
        assert w >= tw * squeeze, 'label too wide: %r (%d > %d)' % (text, tw, w)
        cv = narrow(cv, w)
        tw = w
    x = {'left': 0, 'right': w - tw, 'center': (w - tw) // 2}[align]
    if y is None:
        y = (h - 16) // 2
    out = Canvas(w, h)
    for yy in range(16):
        if 0 <= y + yy < h:
            for xx in range(tw):
                v = cv.px[yy * cv.w + xx]
                if v:
                    out.px[(y + yy) * w + x + xx] = v
    return out.px


def narrow(cv, w):
    """the picture squeezed to w columns (nearest column)"""
    out = Canvas(w, cv.h)
    for y in range(cv.h):
        for x in range(w):
            out.px[y * w + x] = cv.px[y * cv.w + x * cv.w // w]
    return out

"""Pictures copied from the Puyo Nexus patch.

The Windows version is a port of the Saturn one: the .SPR files below are
grp.dat entries with the same frames and colour numbers, and the
pictures the patch translated go in as they are. A translated picture
wider or taller than its frame (the Windows game draws the whole part)
gets a cell of its size, the picture from the cell's top left corner.
"""
from spr import Spr

# (file, grp.dat entry, pictures); a picture is an index, or (Saturn, PC)
PICTURES = [
    ('TITLE1', 158, [0, 1, 2, 3]),          # 'Puyo Puyo' of the logo, no eyes on the kana
    ('PUYO', 0, [379, 380, 381, 382]),      # chain tag, YEAH!, OH NO!, Pause
    ('EFFECT', 5, list(range(28, 49))),     # All Clear!, Offset
    ('LEVEL', 7, [5, 6, 7, 8, 9]),          # curry strength labels
    ('RULE', 19, [7]),                      # 'Rules' of the rules demo
    ('CUT_SKEL', 36, [0, 2, 7, 9, 12, 16]),  # tea signs of Nohoho's stage
    ('CUT_TARA', 37, [17, 18]),             # WOOSH of the splash
    ('SND_TITL', 180, list(range(30))),     # sound test: titles of the music
    ('SND_MES', 179, [1, 2, 3, 4, 5, 7]),   # sound test: Music, controls
    ('RMENU', 226, [38, 39, 40, 41, 47]),   # rules for two players
    ('STAFF', 227, [0]),
]


def wide(p):
    """the picture in a cell of its own size (w a multiple of 8)"""
    w = (p.W + 7) & ~7
    px = []
    for y in range(p.H):
        px += p.px[y * p.W:(y + 1) * p.W] + [0] * (w - p.W)
    return w, p.H, px


def build(files, grp):
    """files: {name: bytes} of the disc, changed in place"""
    log = []
    for name, entry, ids in PICTURES:
        s = Spr(files[name + '.SPR'])
        pics = grp.frames(entry)
        n = grown = 0
        for i in ids:
            i, j = i if isinstance(i, tuple) else (i, i)
            p = pics[j]
            w, h, o, size = s.desc[i]
            assert (p.w, p.h) == (w, h), (name, i)
            if p.inside():
                s.put(i, [v & 15 if v else 0 for v in p.px])
            else:
                W, H, px = wide(p)
                s.put(i, [v & 15 if v else 0 for v in px], W, H)
                grown += 1
            n += 1
        files[name + '.SPR'] = s.blob()
        log.append('%s: %d pictures from the patch (%d wider)' % (name, n, grown))
    return log

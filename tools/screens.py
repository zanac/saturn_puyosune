"""English lettering of the character select and of the map screen.

CHR_SEL.SPR (the arcade set 183): the character select title cells and
the full names of the characters. TRAV01S.SPR (the arcade set 168): the
map screen, with the story titles, the difficulty and the big glyphs of
the opponent name (text engine, 24 pixels per glyph); the Latin letters
for the names come from the 16x16 letters of the ranking set (FONT_RK),
shaded like the map glyphs, and the name texts are rewritten for 16
pixels per letter.
"""
import struct

from gfx import Canvas
from spr import Spr
import menus

LETTER_A, LETTER_DOT = 46, 82       # in FONT_RK.SPR

NAMES = {33: 'SKELETON-T', 34: 'HARPY', 35: 'CHOPPUN', 36: 'DRACO CENTAUROS',
         37: 'INCUBUS', 38: 'SUKETOUDARA', 39: 'KIKIMORA', 40: 'NOHOHO',
         41: 'KODOMO DRAGON', 42: 'WITCH', 43: 'ZOH DAIMAO', 44: 'HONEY BEE',
         45: 'HERO LAGNUS', 46: 'RULUE', 47: 'SCHEZO WEGEY', 48: 'SATAN',
         49: 'ARLE NADJA', 50: 'CARBUNCLE'}

# the opponents on the map (texts at 0x0604c5f2, in this order)
MAP_TEXTS = 0x06071062
MAP_NAMES = ['SKELETON-T', 'HARPY', 'CHOPPUN', 'DRACO CENTAUROS', 'INCUBUS',
             'SUKETOUDARA', 'KIKIMORA', 'NOHOHO', 'KODOMO DRAGON', 'WITCH',
             'ZOH DAIMAOH', 'HONEY BEE', 'LAGNUS BISHASI', 'RULUE',
             'SCHEZO WEGEY', 'SATAN', 'ARLE NADJA', 'CARBUNCLE']
MAP_GLYPH = 80          # first glyph cell of the map set
MAP_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ- .'
MAP_RIGHT = 318         # names end at the right of the screen
# horizontal shading of the map glyphs, left to right
SHADE = [15, 15, 11, 11, 10, 10, 9, 9, 8, 8, 7, 6, 6, 5, 5, 5]

TITLES = {63: "DRACO'S BREAK", 64: "ARLE'S QUEST", 65: "SCHEZO'S BACK"}
DIFFICULTY = {77: 'EASY', 78: 'NORMAL', 79: 'HARD'}


def map_glyph(letter):
    """24x24 cell: a 16x16 letter of the name entry set, outlined and shaded"""
    w, h, px = letter
    mask = [[px[y * w + x] for x in range(w)] for y in range(h)]
    cell = [0] * (24 * 24)
    ox, oy = 3, 4
    for y in range(h):
        for x in range(w):
            v = mask[y][x]
            if not v:
                continue
            cell[(y + oy) * 24 + x + ox] = 2 if v <= 2 else SHADE[x]
    # outline
    out = list(cell)
    for y in range(24):
        for x in range(24):
            if cell[y * 24 + x]:
                continue
            if any(0 <= x + dx < 24 and 0 <= y + dy < 24 and cell[(y + dy) * 24 + x + dx]
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y * 24 + x] = 2
    return out


def block_label(ss, k, text, block, colours, shadow=None):
    w, h, px = ss.get(k)
    cv = Canvas(w, h)
    wd = block.width(text)
    assert wd <= w, (text, wd, w)
    block.draw(cv, text, (w - wd) // 2, (h - 16) // 2, colours)
    ss.put(k, cv.px)


def plaque(ss, k, text, block):
    """the story title plaques: frame kept, new lettering with its shadow"""
    w, h, px = ss.get(k)
    cv = Canvas(w, h, px)
    for y in range(5, 27):
        for x in range(5, 107):
            cv.px[y * w + x] = 4 if y in (5, 6) or x in (5, 6) else 10
    text_cv = Canvas(w, h)
    wd = block.width(text)
    assert wd <= 100, (text, wd)
    block.draw(text_cv, text, 6 + (100 - wd) // 2, 8, menus.BLOCK_COLOURS)
    for y in range(h):
        for x in range(w):
            if text_cv.px[y * w + x]:
                cv.px[y * w + x] = text_cv.px[y * w + x]
            elif x and y and text_cv.px[(y - 1) * w + x - 1] and 5 <= y < 27:
                cv.px[y * w + x] = 4
    ss.put(k, cv.px)


def map_texts(prog):
    """the opponent names, 16 pixels per letter (prog: text.Program)"""
    a = MAP_TEXTS
    for name in MAP_NAMES:
        old = prog.words(a)
        assert old[:5] == [0xff0f, 0x0500, 0xff11, 0x18, 0x10] and old[5] == 0xff06
        w = [0xff0f, 0x0500, 0xff11, 0x10, 0x10, 0xff06, MAP_RIGHT - 16 * len(name), old[7]]
        w += [MAP_GLYPH + MAP_CHARS.index(c) for c in name] + [0xff00]
        prog.repoint(a, prog.place(struct.pack('>%dH' % len(w), *w)))
        a += 2 * len(old)


def build(files, prog, pc, block):
    log = []
    # character select
    ss = Spr(files['CHR_SEL.SPR'])
    menus.title(ss, 21, [27, 43, 59, 75, 91, 107, 123, 147, 163, 179, 195, 211],
                ['SELECT YOUR', 'FIGHTER'], pc)
    for k, name in NAMES.items():
        block_label(ss, k, name, block, menus.BLOCK_COLOURS)
    files['CHR_SEL.SPR'] = ss.blob()
    log.append('character select: title, %d names' % len(NAMES))
    # map
    ms = Spr(files['TRAV01S.SPR'])
    es = Spr(files['FONT_RK.SPR'])
    for i, c in enumerate(MAP_CHARS):
        if c == ' ':
            cell = [0] * 576
        elif c == '-':
            cell = [0] * 576
            for y in (11, 12, 13):
                for x in range(5, 14):
                    cell[y * 24 + x] = 2 if y != 12 or x in (5, 13) else SHADE[x]
        elif c == '.':
            cell = map_glyph(es.get(LETTER_DOT))
        else:
            cell = map_glyph(es.get(LETTER_A + ord(c) - 65))
        ms.put(MAP_GLYPH + i, cell)
    for k, t in TITLES.items():
        plaque(ms, k, t, block)
    for k, t in DIFFICULTY.items():
        block_label(ms, k, t, block, {})
    files['TRAV01S.SPR'] = ms.blob()
    map_texts(prog)
    log.append('map: names, story titles, difficulty')
    return log

"""The ranking (high score) screens: difficulty label, the 'chains' tag of
the MAX column, and the title of the endless (tokoton) ranking.

Their glyphs are 16x16 cells of FONT_RK.SPR (the arcade set 236); the
English labels are drawn with the 8x16 block letters, in the white of the
Japanese labels, into the cells of the kana (86-95, used by these labels
only), and the label texts are rewritten for them, centred where the
Japanese was. The two cells of the 'chain' kanji become a narrow CHAIN;
'tokoton' (cells 98-100) becomes ENDLESS.
"""
import struct

from gfx import Canvas
from spr import Spr

CHAIN_CELLS = (96, 97)

# (text address, English): the labels are centred at x 52 (sprites are
# placed by their centre)
LABELS = [(0x0608014c, 'EASY'), (0x06080166, 'NORMAL'), (0x0608017e, 'HARD')]
CENTRE = 52
LABEL_CELLS, LABEL_END = 86, 96
# the endless ranking title: its 4 codes, rewritten in place
TOKOTON = 0x060b0566
TOKOTON_CELLS = [98, 99, 100]
# block letter shades -> the white of the labels (outline 1, body 10, light 13/15)
WHITE = {2: 1, 3: 1, 4: 1, 5: 10, 6: 13, 7: 13, 8: 15, 9: 15, 10: 15}


def word_cells(ss, block, text, cells):
    """text in block letters, centred over len(cells) 16x16 cells"""
    n = len(cells)
    cv = Canvas(16 * n, 16)
    block.draw(cv, text, (16 * n - block.width(text)) // 2, 0, WHITE)
    for k, c in enumerate(cells):
        ss.put(c, [cv.px[y * 16 * n + 16 * k + x] for y in range(16) for x in range(16)])


def build(files, prog, block):
    ss = Spr(files['FONT_RK.SPR'])
    cell = LABEL_CELLS
    for addr, text in LABELS:
        old = prog.words(addr)
        assert old[:5] == [0xff0f, 0x0700, 0xff11, 0x10, 0x10] and old[5] == 0xff06, hex(addr)
        n = (8 * len(text) + 15) // 16
        cells = list(range(cell, cell + n))
        cell += n
        word_cells(ss, block, text, cells)
        w = [0xff0f, 0x0700, 0xff11, 0x10, 0x10, 0xff06, CENTRE - 8 * (n - 1), old[7]] + cells + [0xff00]
        prog.repoint(addr, prog.place(struct.pack('>%dH' % len(w), *w)))
    # ENDLESS: 4 cells, the three of the kana and one left of the labels
    assert cell < LABEL_END
    cells = TOKOTON_CELLS + [cell]
    word_cells(ss, block, 'ENDLESS', cells)
    a = TOKOTON - prog.base
    assert prog.b[a:a + 8] == bytes.fromhex('0062006300620064')
    prog.b[a:a + 8] = struct.pack('>4H', *cells)
    # CHAIN in the two cells, block letters 6 pixels apart
    cv = Canvas(40, 16)
    block.draw(cv, 'CHAIN', 0, 0, {})
    narrow = Canvas(32, 16)
    for y in range(16):
        for x in range(32):
            narrow.px[y * 32 + x] = cv.px[y * 40 + x * 40 // 32]
    for k, c in enumerate(CHAIN_CELLS):
        ss.put(c, [narrow.px[y * 32 + 16 * k + x] for y in range(16) for x in range(16)])
    files['FONT_RK.SPR'] = ss.blob()
    return ['ranking: difficulty labels, ENDLESS, CHAIN']

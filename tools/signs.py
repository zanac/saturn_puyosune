"""Japanese written on the story backgrounds (8bpp planes, cel.py):

- Nohoho's scene (COM_NOHO): the curry stand's sign, 'Pakisutaru' in
  katakana, becomes CURRY in the 16x16 block letters of FONT_RK.SPR.
- Kikimora's scene (COM_KIKI): the A-frame board in front of the stones,
  'souji-chuu' (cleaning in progress) written down it, becomes CLEANING,
  written down in small letters.

The old letters are painted over with the plain pixels next to them in
the same row.
"""
from cel import Plane
from spr import Spr

# --- curry stand ---------------------------------------------------------------

CURRY_BOX = (185, 57, 273, 78)
CURRY_LETTERS = {86, 124, 133, 189}
CURRY_Y = 60
LETTER_A = 46                      # FONT_RK.SPR
CURRY_INK = {1: 86, 2: 86, 3: 86, 4: 124, 5: 133, 6: 189, 7: 189, 8: 189, 9: 189, 10: 189}


def paint_over(p, x0, y0, x1, y1, ink):
    for y in range(y0, y1):
        row = [p.get(x, y) for x in range(x0 - 8, x1 + 8)]
        plain = [i for i, v in enumerate(row) if not ink(v)]
        for x in range(x0, x1):
            i = x - x0 + 8
            if ink(row[i]):
                j = min(plain, key=lambda k: (abs(k - i), k))
                p.put(x, y, row[j])


def curry(files):
    p = Plane(files['COM_NOHO.CEL'], files['COM_NOHO.MAP'])
    x0, y0, x1, y1 = CURRY_BOX
    assert not p.shared(x0, y0, x1, y1)
    paint_over(p, x0, y0, x1, y1, lambda v: v in CURRY_LETTERS)
    font = Spr(files['FONT_RK.SPR'])
    word = 'CURRY'
    x = x0 + (x1 - x0 - 16 * len(word)) // 2
    for ch in word:
        w, h, px = font.get(LETTER_A + ord(ch) - 65)
        for yy in range(h):
            for xx in range(w):
                if px[yy * w + xx]:
                    p.put(x + xx, CURRY_Y + yy, CURRY_INK[px[yy * w + xx]])
        x += 16
    files['COM_NOHO.CEL'] = p.cel()


# --- cleaning board ------------------------------------------------------------

BOARD_ROWS = (108, 150)
BOARD_X = (64, 104)
BOARD_INK = {59, 61, 73, 88, 113}     # the letters (dark on the light board)
BOARD_DARK = 59
TINY = {   # 4x4 letters
    'C': ['.###', '#...', '#...', '.###'],
    'L': ['#...', '#...', '#...', '####'],
    'E': ['####', '###.', '#...', '####'],
    'A': ['.##.', '#..#', '####', '#..#'],
    'N': ['#..#', '##.#', '#.##', '#..#'],
    'I': ['###.', '.#..', '.#..', '###.'],
    'G': ['.###', '#...', '#.##', '.###'],
}


def board(files):
    p = Plane(files['COM_KIKI.CEL'], files['COM_KIKI.MAP'])
    y0, y1 = BOARD_ROWS
    x0, x1 = BOARD_X
    assert not p.shared(x0, y0, x1, y1)

    def light(v):
        return v >= 150 and v not in (243, 244)
    spans = {}
    for y in range(y0, y1):
        xs = [x for x in range(x0, x1) if light(p.get(x, y)) or p.get(x, y) in BOARD_INK]
        spans[y] = (min(xs), max(xs))
        a, b = spans[y]
        paint_over(p, a + 1, y, b, y + 1, lambda v: v in BOARD_INK)
    word = 'CLEANING'
    y = y0 + 1
    for ch in word:
        rows = TINY[ch]
        # the middle of the board leans: x 83 at the top, 77 at the bottom
        x = 83 - 6 * (y - y0) // (y1 - y0) - 2
        for yy, line in enumerate(rows):
            for xx, c in enumerate(line):
                if c == '#':
                    p.put(x + xx, y + yy, BOARD_DARK)
        y += 5
    assert y <= y1
    files['COM_KIKI.CEL'] = p.cel()


def build(files):
    curry(files)
    board(files)
    return ['story backgrounds: curry stand sign, cleaning board']

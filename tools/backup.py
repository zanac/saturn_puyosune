"""The messages about the saved data (AAA2S.SPR): boxes of white (and
yellow) lettering on black, shown at start up when the backup memory is
full or cannot be used, and the Yes / No buttons.

The Japanese (colours 14, 15 inside the box) is cleared, the frame and
the pad icon are kept, and the English is written in the PC font, a line
where each Japanese line was.
"""
from gfx import Canvas
from spr import Spr

BG = 1
# cell: (top of the first line, x of the first line, lines)
BOXES = {   # cell: (top of the first line, x of the first line, lines, text)
    0: (0, 41, 3, 'Hold L or R and press Reset to go to the Memory Manager screen.'),
    1: (7, 12, 2, 'Erase all the saved data in the system memory. (Initialize)'),
    2: (7, 12, 2, 'Erase all the saved data in the cartridge RAM. (Initialize)'),
    3: (7, 41, 4, 'Not enough room to save the game data (it needs 6). '
                  'If you start now, the game cannot be saved. Is that OK?'),
    6: (7, 12, 4, "In the system's Memory Manager, erase other games' data "
                  'or copy it to the cartridge RAM, then restart.'),
    7: (7, 12, 1, 'Cannot use saved data.'),
    8: (7, 12, 1, 'The data could not be saved.'),
}
BUTTONS = {4: 'Yes', 5: 'No'}
BUTTON_TEXT_X = 24
INK = {1: BG, 9: 15, 15: 15}


def wrap(text, x1, right, pc):
    lines = ['']
    for word in text.split(' '):
        t = (lines[-1] + ' ' + word).strip()
        x = x1 if len(lines) == 1 else 12
        if x + pc.width(t, -1) <= right:
            lines[-1] = t
        else:
            lines.append(word)
    return lines


def box(cv, top, x1, n, text, pc):
    w = cv.w
    lines = wrap(text, x1, w - 10, pc)
    assert len(lines) <= n, lines
    for y in range(top, min(cv.h, top + 16 * len(lines))):
        for x in range(8, w - 8):
            if cv.px[y * w + x] in (14, 15):
                cv.px[y * w + x] = BG
    for n, line in enumerate(lines):
        x = x1 if n == 0 else 12
        track = 0 if x + pc.width(line) <= w - 10 else -1
        assert x + pc.width(line, track) <= w - 10, line
        pc.draw(cv, line, x, top + 16 * n, INK, track)


def button(cv, text, pc, bg=6, ink=8):
    """a button: the symbol kept, the word after it"""
    w = cv.w
    for y in range(cv.h):
        for x in range(BUTTON_TEXT_X, w - 6):
            if cv.px[y * w + x] == ink:
                cv.px[y * w + x] = bg
    pc.draw(cv, text, BUTTON_TEXT_X + (w - 6 - BUTTON_TEXT_X - pc.width(text)) // 2, 0, {1: None, 9: ink, 15: ink})


def build(files, pc):
    s = Spr(files['AAA2S.SPR'])
    for k, text in BUTTONS.items():
        w, h, px = s.get(k)
        cv = Canvas(w, h, px)
        button(cv, text, pc)
        s.put(k, cv.px)
    for k, (top, x1, n, text) in BOXES.items():
        w, h, px = s.get(k)
        cv = Canvas(w, h, px)
        if k == 3:
            # the two buttons drawn in the box, below the lines
            rows = [y for y in range(72, h) if 3 in px[y * w:(y + 1) * w]]
            y0, y1 = rows[0], rows[-1] + 1
            cols = [any(px[y * w + x] in (2, 3, 9) for y in range(y0, y1)) for x in range(w)]
            segs = []
            for x in range(w):
                if cols[x] and (not segs or segs[-1][1] != x):
                    segs.append([x, x + 1])
                elif cols[x]:
                    segs[-1][1] = x + 1
            assert len(segs) == 2, segs
            for (a, b), word in zip(segs, ('Yes', 'No')):
                sub = Canvas(b - a, y1 - y0, [px[y * w + x] for y in range(y0, y1) for x in range(a, b)])
                button(sub, word, pc, 3, 9)
                for y in range(y1 - y0):
                    cv.px[(y0 + y) * w + a:(y0 + y) * w + b] = sub.px[y * sub.w:(y + 1) * sub.w]
        box(cv, top, x1, n, text, pc)
        s.put(k, cv.px)
    files['AAA2S.SPR'] = s.blob()
    return ['saved data messages: %d boxes' % len(BOXES)]

"""'Message from AAA' (options menu): the message of the Act Against AIDS
campaign, translated here (the patch shows its own greeting instead).

AAA_MES.SPR: cell 0 the title (big letters, then '(Act Against AIDS)'),
cells 1-14 the lines, 320x16 each, in one colour without outline.
"""
from gfx import Canvas
from spr import Spr

TITLE = 'A Message from AAA'
LINES = [
    'AIDS is an illness like any other.',
    "You can't catch it by touching.",
    'Science has proven it, too.',
    "So don't be afraid of it.",
    'If someone near you is infected,',
    'be kind to them.',
    'Love and courage: the best vaccine!',
    'Love and courage can save the world.',
    'For questions about AIDS, call',
    'the AIDS Prevention Foundation',
    'PHONE:0120-177-812',
    'Monday to Friday,',
    'from 10 AM to 5 PM.',
    'Compile supports AAA.',
]
TITLE_ROWS = 34                    # the big letters; the line below is kept
TITLE_X = 17
LINE_X = 8


def big(pc, text, colours):
    """the text at twice the height, 1.5 times the width"""
    tw = pc.width(text)
    cv = Canvas(tw, 16)
    pc.draw(cv, text, 0, 0, colours)
    W = tw * 3 // 2
    out = Canvas(W, 32)
    for y in range(32):
        for x in range(W):
            out.px[y * W + x] = cv.px[(y // 2) * tw + x * 2 // 3]
    return out


def build(files, pc):
    ss = Spr(files['AAA_MES.SPR'])
    w, h, px = ss.get(0)
    cv = Canvas(w, h, px)
    cv.clear(0, 0, w, TITLE_ROWS)
    t = big(pc, TITLE, {1: 8, 9: 7, 15: 6})
    assert TITLE_X + t.w <= w, t.w
    cv.blit(t.px, t.w, t.h, TITLE_X, 1, {})
    ss.put(0, cv.px)
    for k, line in enumerate(LINES, 1):
        w, h, px = ss.get(k)
        cv = Canvas(w, h)
        track = 0 if LINE_X + pc.width(line) <= w else -1
        assert LINE_X + pc.width(line, track) <= w, line
        pc.draw(cv, line, LINE_X, 0, {1: 0, 9: 0, 15: 15}, track)
        ss.put(k, cv.px)
    files['AAA_MES.SPR'] = ss.blob()
    return ['message from AAA: %d lines' % len(LINES)]

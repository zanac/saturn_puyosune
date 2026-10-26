"""The story scenes: the English texts of the Puyo Nexus patch (comic.scr of
the Windows version) in place of the Japanese ones.

The Windows version is a port of the Saturn one: the same 24 scenes, the
same event lists ("15 41 50 00", time, block) with the same times, and a
block shows one text ("31 00 00 00", text, then the end op "00 00 00 00").
Page k of a scene gets page k of the patch. The patch's pauses and typing
speed were made for these times, so they stay; the text goes in
proportional mode (the patch spaces its letters by a fixed step), with the
balloon sized for it.

comic.scr is little endian; its pointers are file offsets - 4.
"""
import struct

EVENT = b'\x15\x41\x50\x00'
SHOW = b'\x31\x00\x00\x00'
END = b'\x00\x00\x00\x00'

# the Japanese story texts, between these addresses
TEXTS_FROM, TEXTS_TO = 0x0608d000, 0x06091400

ARGS = {0xff02: 0, 0xff03: 1, 0xff04: 1, 0xff06: 2, 0xff07: 1, 0xff0f: 1,
        0xff10: 1, 0xff11: 2, 0xff12: 4, 0xff13: 2, 0xff14: 1, 0xff15: 4}

PROP = 0x40      # text engine flag: x advance from the width table


def _scene_lists(data, rd32, base, is_block):
    """[(list address, [(time, block)])] of every event list whose events
    all show a text, in the order of their blocks"""
    out = []
    i = 0
    n = len(data)
    while i < n - 12:
        if data[i:i + 4] == EVENT:
            a = i
            ev = []
            while data[a:a + 4] == EVENT:
                ev.append((rd32(a + 4), rd32(a + 8) - base))
                a += 12
            if all(is_block(b) for t, b in ev):
                out.append((i, ev))
            i = a
        else:
            i += 4
    return sorted(out, key=lambda s: min(b for t, b in s[1]))


def pc_scenes(comic):
    """the event lists of comic.scr: [[(time, text words)]]"""
    def rd32(a):
        return struct.unpack('<I', comic[a:a + 4])[0]

    def is_block(a):
        return comic[a:a + 4] == SHOW and comic[a + 8:a + 12] == END

    def text(off):
        w = []
        a = off
        while True:
            x = struct.unpack('<H', comic[a:a + 2])[0]
            w.append(x)
            a += 2
            if x == 0xff00:
                return w
    return [[(t, text(rd32(b + 4) + 4)) for t, b in ev]
            for at, ev in _scene_lists(comic, rd32, -4, is_block)]


def saturn_scenes(prog, base):
    """[(list offset, [(time, block offset)])] in the program"""
    def rd32(a):
        return struct.unpack('>I', prog[a:a + 4])[0]

    def is_block(a):
        return (prog[a:a + 4] == SHOW and prog[a + 8:a + 12] == END
                and TEXTS_FROM <= rd32(a + 4) < TEXTS_TO)
    return _scene_lists(prog, rd32, base, is_block)


def _ops(words):
    """[(op or None, args or char)]"""
    out = []
    i = 0
    while i < len(words):
        x = words[i]
        if x >= 0xff00:
            n = ARGS.get(x, 0)
            out.append((x, list(words[i + 1:i + 1 + n])))
            i += 1 + n
        else:
            out.append((None, x))
            i += 1
    return out


PIECE = 12       # balloon pieces are drawn every 12 pixels (FF11 12 16)
SCREEN_W = 320


def fit_balloon(head, body, charmap, widths):
    """the balloon of the patch was sized for its spacing of the letters;
    size it for the proportional text, and keep it on the screen (a balloon
    that goes past the right edge is not drawn at all)"""
    pos = [k for k, (x, a) in enumerate(head) if x == 0xff06]
    bal = [k for k, (x, a) in enumerate(head) if x == 0xff15]
    tpos = [k for k, (x, a) in enumerate(body) if x == 0xff06]
    if not pos or not bal or not tpos:
        return head
    bx, by = head[pos[0]][1]
    bw, bh, bbase, tail = head[bal[0]][1]
    tx, ty = body[tpos[0]][1]
    lines = [0]
    for x, a in body:
        if x == 0xff02:
            lines.append(0)
        elif x is None:
            lines[-1] += sum(widths[c] for c in charmap[a])
    w = min(bw, -(-(max(lines) + 2 * (tx - bx)) // PIECE))
    shift = max(0, bx + w * PIECE + 4 - SCREEN_W)
    shift = min(shift, bx)
    tail = min(tail + -(-shift // PIECE), w - 2) if tail < 0x8000 else tail
    head = list(head)
    head[pos[0]] = (0xff06, [bx - shift, by])
    head[bal[0]] = (0xff15, [w, bh, bbase, tail])
    if shift:
        body[tpos[0]] = (0xff06, [tx - shift, ty])
    return head


def split(ops):
    """(head, body): the balloon part, the text part (from the 2nd FF0F)"""
    nf = 0
    head, body = [], []
    for op in ops:
        if op[0] == 0xff0f:
            nf += 1
        (body if nf >= 2 else head).append(op)
    return head, body


def convert(words, charmap, widths, orig):
    """a PC text for the Saturn: in the body (from the second FF0F)
    proportional mode and no letter spacing; the rest as it is. A page
    the patch wrote without its balloon part gets the balloon and text
    position of the Japanese page (orig)."""
    ops = _ops(words)
    if sum(1 for x, a in ops if x == 0xff0f) == 1:
        head, body = split(_ops(orig))
        pos = [a for x, a in body if x == 0xff06]
        ops = head + [(x, pos[0] if x == 0xff06 else a) for x, a in ops]
    nf = 0
    body = []
    head = []
    total = sum(1 for x, a in ops if x == 0xff0f)
    for op in ops:
        if op[0] == 0xff0f:
            nf += 1
        (body if nf >= 2 or total == 0 else head).append(op)
    if total == 0:      # a page that goes on in the balloon of the last one
        head = [(0xff0f, [PROP]), (0xff11, [0, 0x10])]
    assert total != 1, 'text with one FF0F'
    head = fit_balloon(head, body, charmap, widths)
    out = []
    for x, a in head:
        out.append(x)
        out.extend(a)
    spaced = False
    for x, a in body:
        if x is None:
            out.extend(charmap[a])
            continue
        a = list(a)
        if x == 0xff0f:
            a[0] |= PROP
        elif x == 0xff11:
            if spaced:
                continue
            spaced = True
            a[0] = 0
        out.append(x)
        out.extend(a)
    return out


def rd(b, a):
    return struct.unpack('>I', b[a:a + 4])[0]


def build(prog, comic, charmap, widths):
    """put the PC texts in the scenes of prog (text.Program). Returns a
    log."""
    pcs = pc_scenes(comic)
    sat = saturn_scenes(prog.b, prog.base)
    assert len(pcs) == len(sat) == 24, (len(pcs), len(sat))
    texts = {}
    pages = 0
    for (at, ev), pev in zip(sat, pcs):
        assert [t for t, b in ev] == [t for t, w in pev]
        for (t, b), (u, words) in zip(ev, pev):
            key = (tuple(words), rd(prog.b, b + 4))
            if key not in texts:
                w = convert(words, charmap, widths, prog.words(rd(prog.b, b + 4)))
                texts[key] = prog.place(struct.pack('>%dH' % len(w), *w))
            assert prog.b[b:b + 4] == SHOW
            prog.b[b + 4:b + 8] = struct.pack('>I', texts[key])
            pages += 1
    return ['story: %d scenes, %d pages' % (len(sat), pages)]

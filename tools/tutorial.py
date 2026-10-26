"""The rules demonstration (Arle explains the game, in the attract mode).

Its 26 texts (the same as the arcade ones) use the story sprite set,
whose kana codes now hold the English letters, so they are translated
here (the PC patch has no counterpart). Each text keeps its own commands (position, speed, waits);
the characters become the English lines, in proportional mode.
"""
import struct

import story

FIRST, LAST = 0x060834c0, 0x06083be0

LINES = [
    "Hi, I'm Arle!",
    "I'll explain the rules now.",
    "You move the puyos with the lever.",
    "Left and right, back and forth~",
    "Push the lever down to drop them faster.",
    "Press a button and they spin around.",
    "4 puyos of one color that touch will vanish.",
    "When puyos vanish, the ones above fall...",
    "and if those vanish too, that's a chain!",
    "Let me show you once more.",
    "Look, if you do it like this...!",
    "Fill the 3rd column from the left: game over!",
    "Big clears send Nuisance Puyos to your rival!",
    "Chains send even more Nuisance Puyos!",
    "Nuisance Puyos don't vanish when 4 touch.",
    "Clear puyos next to them and they go too.",
    "Oh no! Nuisance Puyos are coming!",
    "Don't panic. Clear puyos here...",
    "to cancel what you get! That's an Offset.",
    "Leftover puyos fly over to your rival's field.",
    "When you offset...",
    "Sun Puyos fall!",
    "Clearing Sun Puyos sends Nuisance too.",
    "Clear them in a chain to send even more!",
    "An All Clear also brings Sun Puyos.",
    "Sun Puyos don't vanish when 4 touch either.",
]
MAX_WIDTH = 160        # inside the balloon
MAX_LINES = 3


def wrap(text, widths):
    lines = ['']
    for word in text.split(' '):
        t = (lines[-1] + ' ' + word).strip()
        if sum(widths[ord(c)] for c in t) <= MAX_WIDTH:
            lines[-1] = t
        else:
            lines.append(word)
    assert len(lines) <= MAX_LINES and all(sum(widths[ord(c)] for c in l) <= MAX_WIDTH for l in lines), text
    return lines


def build(prog, widths):
    """prog: text.Program"""
    a = FIRST
    texts = []
    while a < LAST:
        if prog.b[a - prog.base:a - prog.base + 2] == b'\xff\x0f':
            w = prog.words(a)
            texts.append((a, w))
            a += 2 * len(w)
        else:
            a += 2
    assert len(texts) == len(LINES), len(texts)
    for (a, words), english in zip(texts, LINES):
        ops = story._ops(words)
        chars = [k for k, (x, v) in enumerate(ops) if x is None]
        head, tail = ops[:chars[0]], ops[chars[-1] + 1:]
        assert all(x in (None, 0xff02) for x, v in ops[chars[0]:chars[-1] + 1])
        out = []
        for x, v in head:
            v = list(v)
            if x == 0xff0f:
                v[0] |= story.PROP
            elif x == 0xff11:
                v[0] = 0
            out += [x] + v
        for n, line in enumerate(wrap(english, widths)):
            if n:
                out.append(0xff02)
            out += [ord(c) for c in line]
        for x, v in tail:
            out += [x] + list(v)
        prog.repoint(a, prog.place(struct.pack('>%dH' % len(out), *out)))
    return ['rules demo: %d texts' % len(texts)]

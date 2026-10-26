"""Build the English disc: the data track of the Japanese disc (Rev A) with
the files changed, from the Puyo Nexus patch of the Windows version.

    python3 build.py TRACK1.bin grp.dat comic.scr OUT_DIR
"""
import sys

import disc
import font
import ending
import gamesel
import gfx
import aaa
import aids
import atelier
import backup
import images
import ingame
import menus
import nameentry
import ranking
import results
import screens
import signs
from spr import Spr
import options
import pcgrp
import region
import story
import text
import tutorial


def build(track_path, grp_blob, comic):
    t = disc.Track(track_path)
    files = {}
    for name in t.files:
        files[name] = t.read(name)
    orig = dict(files)
    grp = pcgrp.Grp(grp_blob)
    log = []
    pc = font.pc_font(grp_blob)
    log += images.build(files, grp)
    log += options.build(files, pc)
    block = gfx.block_font(Spr(orig['FONT.SPR']))
    log += menus.build(files, pc, block)
    log += gamesel.build(files, pc)
    log += ingame.build(files, pc, block)
    log += results.build(files, pc)
    log += aids.build(files, pc)
    log += aaa.build(files, pc)
    log += atelier.build(files, pc)
    log += backup.build(files, pc)
    log += signs.build(files)
    prog, glyphs, widths, tlog = text.build(files, grp_blob)
    log += tlog
    charmap = {c: [c] for c in glyphs}
    charmap[0x1f] = [0x2c, 0x20]        # the patch writes ", " as one character
    log += story.build(prog, comic, charmap, widths)
    log += tutorial.build(prog, widths)
    log += screens.build(files, prog, pc, block)
    log += ranking.build(files, prog, block)
    log += nameentry.build(files, prog, pc)
    log += ending.build(files, prog, pc)
    log.append('program free area used to %x' % prog.free)
    files['0'] = bytes(prog.b)
    moved = 0
    for name, blob in files.items():
        if blob != orig[name]:
            before = t.files[name][1]
            t.put(name, blob)
            moved += t.files[name][1] != before
    log.append('%d files changed, %d moved to the end of the track' % (
        sum(files[n] != orig[n] for n in files), moved))
    log += region.build(t)
    return t.finish(), log


def main():
    track, grp, comic, dst = sys.argv[1:5]
    import os
    out, log = build(track, open(grp, 'rb').read(), open(comic, 'rb').read())
    for line in log:
        print(line)
    os.makedirs(dst, exist_ok=True)
    open(os.path.join(dst, 'track01.bin'), 'wb').write(out)


if __name__ == '__main__':
    main()

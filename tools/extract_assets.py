"""Make assets/saturn_puyosune_assets.zip (see assets.py) from the Puyo Nexus
English patch of the Windows version, as it comes. Only needed to remake
the zip; the build does not use the patch. Python 3 standard library only.

    python3 extract_assets.py Puyo_Puyo_Sun__English_Patched_.zip [ASSETS_ZIP]
"""
import sys
import zipfile

import assets
import images
import pcgrp
import story
import text


def read_member(z, name):
    for i in z.infolist():
        if i.filename.lower().replace('\\', '/').endswith(name):
            return z.read(i)
    raise SystemExit('%s: no %s' % (z.filename, name))


def main():
    patch = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else assets.DEFAULT
    zp = zipfile.ZipFile(patch)
    grp_blob = read_member(zp, 'puyo3/grp.dat')
    comic = read_member(zp, 'puyo3/comic.scr')
    grp = pcgrp.Grp(grp_blob)
    pictures = {}
    for name, entry, ids in images.PICTURES:
        frames = grp.frames(entry)
        for i in ids:
            j = i[1] if isinstance(i, tuple) else i
            pictures[(entry, j)] = frames[j]
    a = assets.Assets(text.glyphs(grp_blob), pictures, story.pc_scenes(comic))
    assets.save(dst, a)
    print('wrote %s: %d characters, %d pictures, %d scenes' % (dst, len(a.glyphs), len(pictures), len(a.story)))


if __name__ == '__main__':
    main()

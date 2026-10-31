"""The translated assets of the Puyo Nexus English patch that the build uses,
kept in assets/saturn_puyosune_assets.zip so the build needs only the disc.

The zip holds JSON files:
  glyphs.json   [[code, advance, 256 colour indices of the 16x16 cell]]: the
                English font of the patch (grp.dat entry 21) and the note
                taken from a win quote picture (entry 1), as text.glyphs()
  pictures.json {"entry/frame": [w, h, W, H, fx, fy, pixels]}: the pictures
                the patch translated (images.PICTURES), as pcgrp.Picture
  story.json    [[[time, text words]]]: the English pages of the story
                scenes (comic.scr), as story.pc_scenes()

extract_assets.py makes the zip from the patched Windows game; the build
reads only the zip.
"""
import json
import os
import zipfile

from pcgrp import Picture

DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets',
                       'saturn_puyosune_assets.zip')


class Assets:
    def __init__(self, glyphs, pictures, story):
        self.glyphs = glyphs        # {code: (advance, cell)}, in font order
        self.pictures = pictures    # {(entry, frame): Picture}
        self.story = story          # [[(time, words)]]


def load(path=DEFAULT):
    with zipfile.ZipFile(path) as z:
        glyphs = json.loads(z.read('glyphs.json'))
        pictures = json.loads(z.read('pictures.json'))
        story = json.loads(z.read('story.json'))
    return Assets({c: (adv, cell) for c, adv, cell in glyphs},
                  {tuple(int(x) for x in k.split('/')): Picture(*v) for k, v in pictures.items()},
                  [[(t, w) for t, w in scene] for scene in story])


def save(path, a):
    def dump(o):
        return json.dumps(o, separators=(',', ':'), sort_keys=True).encode()
    glyphs = [[c, adv, list(cell)] for c, (adv, cell) in a.glyphs.items()]
    pictures = {'%d/%d' % k: [p.w, p.h, p.W, p.H, p.fx, p.fy, list(p.px)]
                for k, p in a.pictures.items()}
    story = [[[t, list(w)] for t, w in scene] for scene in a.story]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, o in (('glyphs.json', glyphs), ('pictures.json', pictures), ('story.json', story)):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, dump(o))

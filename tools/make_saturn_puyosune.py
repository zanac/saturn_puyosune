"""Make the English Puyo Puyo Sun for the Sega Saturn from the Japanese disc
(Rev A, the Redump .cue/.bin set) and the Puyo Nexus English patch of the
Windows version, both as they come. Python 3 standard library only.

    python3 make_saturn_puyosune.py "Puyo Puyo Sun (Japan) (Rev A) (10M).cue" Puyo_Puyo_Sun__English_Patched_.zip OUT_DIR

OUT_DIR receives "Puyo Puyo Sun (English).cue" with its two tracks: the
data track rebuilt, the audio track copied.
"""
import hashlib
import os
import shutil
import sys
import zipfile
import zlib

import build

TRACKS = [('e1afff40', 464670528), ('3f0834c8', 5435472)]
NAME = 'Puyo Puyo Sun (English)'
CUE = '''FILE "{0} (Track 1).bin" BINARY
  TRACK 01 MODE1/2352
    INDEX 01 00:00:00
FILE "{0} (Track 2).bin" BINARY
  TRACK 02 AUDIO
    INDEX 00 00:00:00
    INDEX 01 00:02:01
'''


def crc_file(path):
    c = 0
    with open(path, 'rb') as f:
        while True:
            b = f.read(1 << 22)
            if not b:
                return '%08x' % (c & 0xffffffff)
            c = zlib.crc32(b, c)


def tracks(cue):
    """the bin files of the cue sheet, in order"""
    out = []
    for line in open(cue, encoding='latin-1'):
        line = line.strip()
        if line.upper().startswith('FILE'):
            name = line[line.index('"') + 1:line.rindex('"')]
            out.append(os.path.join(os.path.dirname(os.path.abspath(cue)), name))
    return out


def read_member(z, name):
    for i in z.infolist():
        if i.filename.lower().replace('\\', '/').endswith(name):
            return z.read(i)
    raise SystemExit('%s: no %s' % (z.filename, name))


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    cue, patch, dst = sys.argv[1:4]
    bins = tracks(cue)
    if len(bins) != 2:
        raise SystemExit('%s: expected 2 tracks, found %d' % (cue, len(bins)))
    for path, (want, size) in zip(bins, TRACKS):
        if os.path.getsize(path) != size or crc_file(path) != want:
            raise SystemExit('%s: not the Redump track (CRC %s expected)' % (path, want))
    zp = zipfile.ZipFile(patch)
    grp = read_member(zp, 'puyo3/grp.dat')
    comic = read_member(zp, 'puyo3/comic.scr')
    out, log = build.build(bins[0], grp, comic)
    for line in log:
        print(line)
    os.makedirs(dst, exist_ok=True)
    t1 = os.path.join(dst, NAME + ' (Track 1).bin')
    t2 = os.path.join(dst, NAME + ' (Track 2).bin')
    open(t1, 'wb').write(out)
    shutil.copyfile(bins[1], t2)
    open(os.path.join(dst, NAME + '.cue'), 'w', newline='\r\n').write(CUE.format(NAME))
    for path in (t1, t2):
        d = open(path, 'rb').read()
        print('%-40s %10d  crc %s  sha1 %s' % (os.path.basename(path), len(d),
                                              '%08x' % (zlib.crc32(d) & 0xffffffff), hashlib.sha1(d).hexdigest()))
    print('wrote', os.path.join(dst, NAME + '.cue'))


if __name__ == '__main__':
    main()

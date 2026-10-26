"""Reader for grp.dat of the Windows Puyo Puyo Sun (puyo3.exe).

grp.dat: u32 count, u32 0, then count+1 (offset, size) pairs (u32 LE).
Each entry is a sprite set, u32 nframes, u32 type:
  type 0/1: one picture; u16 w, u16 h, u32 0, u32 nparts, then the parts
  type 2:   nframes x (u16 w, u16 h, u32 index), u32 nparts, then the parts
A part (16 bytes) is a rectangle of 8bpp pixels:
  u16 w, u16 h, u16 x, u16 y, u16 ?, u16 flags, u32 data offset
(data offsets count from the end of the part table).
"""
import struct


def entries(g):
    n = struct.unpack('<I', g[:4])[0]
    return [struct.unpack('<II', g[8 + i * 8:16 + i * 8]) for i in range(n)]


def parse(d):
    """(type, frames [(w, h)], parts [(w, h, x, y, a, flags, off)], data offset)"""
    nf, t = struct.unpack('<II', d[:8])
    if t in (0, 1):
        w, h, z, np_ = struct.unpack('<HHII', d[8:20])
        frames = [(w, h)]
        p = 20
    else:
        frames = [struct.unpack('<HH', d[8 + i * 8:12 + i * 8]) for i in range(nf)]
        p = 8 + nf * 8
        np_ = struct.unpack('<I', d[p:p + 4])[0]
        p += 4
    parts = [struct.unpack('<HHHHHHI', d[p + i * 16:p + i * 16 + 16]) for i in range(np_)]
    return t, frames, parts, p + 16 * np_


def picture(d):
    """type 0/1 picture as (w, h, bytes 8bpp)"""
    t, frames, parts, base = parse(d)
    w, h = frames[0]
    img = bytearray(w * h)
    for pw, ph, x, y, a, fl, off in parts:
        src = d[base + off:base + off + pw * ph]
        for r in range(ph):
            if y + r >= h:
                break
            row = src[r * pw:(r + 1) * pw]
            n = min(pw, w - x)
            img[(y + r) * w + x:(y + r) * w + x + n] = row[:n]
    return w, h, bytes(img)


def sprites(d):
    """type 2: [(w, h, bytes 8bpp)] one per part"""
    t, frames, parts, base = parse(d)
    out = []
    for pw, ph, x, y, a, fl, off in parts:
        out.append((pw, ph, d[base + off:base + off + pw * ph]))
    return out

"""The decompressor of the Puyo Puyo Sun (ST-V) program (code at 0x060b003c).

Byte stream of commands, a command byte c:
  0x00        end
  0x0n        copy (n & 15) + 2 bytes from out - d8       (1 distance byte)
  0x1n        copy (n & 15) + 2 bytes from out - d16      (distance LE)
  0x2n        copy ((n & 15) << 8 | l8) bytes, distance d8
  0x3n        copy ((n & 15) << 8 | l8) bytes, distance d16 (LE)
  0x40-0x5f   (c & 31) literal bytes
  0x60-0x7f   ((c & 31) << 8 | l8) literal bytes
  0x80-0xff   ((c >> 4) & 7) literal bytes, then copy (c & 15) + 2 bytes
              from out - d8
"""


def decompress(src, pos=0, limit=1 << 22):
    out = bytearray()
    while True:
        c = src[pos]
        pos += 1
        if c == 0:
            return bytes(out), pos
        hi = c & 0xf0
        if hi in (0x40, 0x50, 0x60, 0x70):
            n = c & 0x1f
            if hi >= 0x60:
                n = (n << 8) | src[pos]
                pos += 1
            out += src[pos:pos + n]
            pos += n
            continue
        if hi == 0x00:
            n = (c & 15) + 2
            d = src[pos]
            pos += 1
        elif hi == 0x10:
            n = (c & 15) + 2
            d = src[pos] | (src[pos + 1] << 8)
            pos += 2
        elif hi == 0x20:
            n = ((c & 15) << 8) | src[pos]
            d = src[pos + 1]
            pos += 2
        elif hi == 0x30:
            n = ((c & 15) << 8) | src[pos]
            d = src[pos + 1] | (src[pos + 2] << 8)
            pos += 3
        else:
            lit = (c >> 4) & 7
            out += src[pos:pos + lit]
            pos += lit
            d = src[pos]
            pos += 1
            n = (c & 15) + 2
        if d == 0 or d > len(out):
            raise ValueError('bad distance at %x' % pos)
        for i in range(n):
            out.append(out[-d])
        if len(out) > limit:
            raise ValueError('too long')

"""The pictures of the Puyo Nexus patch (grp.dat of the Windows version).

The Windows version is a port of the Saturn one: most .SPR files of the
disc are a grp.dat entry with the same frames and colour numbers. The
translated pictures of the patch sometimes reach past the frame box of
the original (the Windows game draws the whole part); frames() gives the
whole picture, from the frame's top left corner.
"""
import grpdat


class Grp:
    def __init__(self, blob):
        self.g = blob
        self.e = grpdat.entries(blob)

    def frames(self, k):
        """[(w, h, pixels)], w and h at least those of the frame"""
        o, s = self.e[k]
        d = self.g[o:o + s]
        t, frames, parts, base = grpdat.parse(d)
        out = []
        for (w, h), (pw, ph, px, py, a, fl, off) in zip(frames, parts):
            px = px - 0x10000 if px & 0x8000 else px
            py = py - 0x10000 if py & 0x8000 else py
            W, H = max(w, px + pw), max(h, py + ph)
            img = [0] * (W * H)
            src = d[base + off:base + off + pw * ph]
            for y in range(ph):
                for x in range(pw):
                    X, Y = x + px, y + py
                    if 0 <= X < W and 0 <= Y < H:
                        img[Y * W + X] = src[y * pw + x]
            out.append((w, h, W, H, img))
        return out

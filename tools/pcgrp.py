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
        """[Picture] of the frames of entry k"""
        o, s = self.e[k]
        d = self.g[o:o + s]
        t, frames, parts, base = grpdat.parse(d)
        out = []
        for (w, h), (pw, ph, px, py, a, fl, off) in zip(frames, parts):
            px = px - 0x10000 if px & 0x8000 else px
            py = py - 0x10000 if py & 0x8000 else py
            x0, y0 = min(0, px), min(0, py)
            W, H = max(w, px + pw) - x0, max(h, py + ph) - y0
            img = [0] * (W * H)
            src = d[base + off:base + off + pw * ph]
            for y in range(ph):
                for x in range(pw):
                    img[(y + py - y0) * W + x + px - x0] = src[y * pw + x]
            out.append(Picture(w, h, W, H, -x0, -y0, img))
        return out


class Picture:
    """a picture of the patch: the frame is w x h; the whole picture is
    W x H, the frame's top left corner at (fx, fy) in it"""
    def __init__(self, w, h, W, H, fx, fy, px):
        self.w, self.h, self.W, self.H, self.fx, self.fy, self.px = w, h, W, H, fx, fy, px

    def inside(self):
        return self.W == self.w and self.H == self.h

    def frame(self):
        """the pixels inside the frame box"""
        return [self.px[(y + self.fy) * self.W + x + self.fx] for y in range(self.h) for x in range(self.w)]

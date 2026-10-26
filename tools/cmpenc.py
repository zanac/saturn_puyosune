"""Compressor for the format of cmpdec.py (Python 3 standard library only).

Greedy parse with one step of lazy matching; matches come from hash chains
of 3-byte prefixes. The output decodes with cmpdec.decompress and with the
SH-2 decompressor of the game.
"""

MAXD = 0xffff
MAXLEN = 0xfff
DEPTH = 24


def _match_len(data, a, b, limit):
    """length of the common run of data[a:] and data[b:] (b > a), at most limit"""
    if data[a:a + limit] == data[b:b + limit]:
        return limit
    lo, hi = 0, limit
    while hi - lo > 8:
        mid = (lo + hi) // 2
        if data[a:a + mid] == data[b:b + mid]:
            lo = mid
        else:
            hi = mid
    while lo < hi and data[a + lo] == data[b + lo]:
        lo += 1
    return lo


def _cost(n, d):
    """bytes of a copy command (without literals)"""
    if n <= 17:
        return 2 if d <= 255 else 3
    return 3 if d <= 255 else 4


class _Finder:
    def __init__(self, data):
        self.data = data
        self.head = {}
        self.prev = [-1] * len(data)
        self.pos = 0

    def insert_upto(self, i):
        d = self.data
        while self.pos < i:
            p = self.pos
            if p + 3 <= len(d):
                k = d[p:p + 3]
                self.prev[p] = self.head.get(k, -1)
                self.head[k] = p
            self.pos += 1

    def best(self, i):
        d = self.data
        n = len(d)
        if i + 3 > n:
            return 0, 0
        self.insert_upto(i)
        limit = min(MAXLEN, n - i)
        bl, bd, bc = 0, 0, 0
        c = self.head.get(d[i:i + 3], -1)
        depth = 0
        while c >= 0 and i - c <= MAXD and depth < DEPTH:
            if d[c + bl] == d[i + bl] if bl < limit else True:
                ln = _match_len(d, c, i, limit)
                if ln >= 2:
                    gain = ln - _cost(ln, i - c)
                    if gain > bc:
                        bl, bd, bc = ln, i - c, gain
                        if ln == limit:
                            break
            c = self.prev[c]
            depth += 1
        # distance 1 and 2 runs (often missed by the 3-byte chain head)
        for dd in (1, 2):
            if i >= dd and bd != dd:
                ln = _match_len(d, i - dd, i, limit)
                if ln >= 2 and ln - _cost(ln, dd) > bc:
                    bl, bd, bc = ln, dd, ln - _cost(ln, dd)
        if bc <= 0:
            return 0, 0
        return bl, bd


def compress(data):
    data = bytes(data)
    n = len(data)
    f = _Finder(data)
    out = bytearray()
    lit = bytearray()

    def flush_lit():
        """write the pending literals"""
        k = len(lit)
        p = 0
        while k - p > 0:
            m = min(k - p, 0x1fff)
            if m <= 31:
                out.append(0x40 | m)
            else:
                out.append(0x60 | (m >> 8))
                out.append(m & 0xff)
            out.extend(lit[p:p + m])
            p += m
        del lit[:k]

    def put_copy(ln, d):
        while ln:
            m = min(ln, MAXLEN)
            if ln - m == 1:          # never leave a copy of 1 byte
                m -= 1
            if m <= 17 and d <= 255 and len(lit) <= 7:
                out.append(0x80 | (len(lit) << 4) | (m - 2))
                out.extend(lit)
                del lit[:]
                out.append(d)
            else:
                flush_lit()
                if m <= 17:
                    if d <= 255:
                        out.extend(bytes((0x00 | (m - 2), d)))
                    else:
                        out.extend(bytes((0x10 | (m - 2), d & 0xff, d >> 8)))
                else:
                    if d <= 255:
                        out.extend(bytes((0x20 | (m >> 8), m & 0xff, d)))
                    else:
                        out.extend(bytes((0x30 | (m >> 8), m & 0xff, d & 0xff, d >> 8)))
            ln -= m

    i = 0
    while i < n:
        ln, d = f.best(i)
        if ln and i + 1 < n:
            ln2, d2 = f.best(i + 1)
            if ln2 > ln + 1:
                lit.append(data[i])
                i += 1
                ln, d = ln2, d2
        if ln:
            if len(lit) > 7:
                flush_lit()
            put_copy(ln, d)
            i += ln
        else:
            lit.append(data[i])
            i += 1
    flush_lit()
    out.append(0)
    return bytes(out)


def compress_optimal(data):
    """the same format, with a cheapest parse (dynamic programming over the
    positions, from the end): smaller than compress() on pictures"""
    data = bytes(data)
    n = len(data)
    f = _Finder(data)
    # candidates per position: (length, distance), the longest per distance
    cands = []
    for i in range(n):
        cs = []
        if i + 3 <= n:
            f.insert_upto(i)
            limit = min(MAXLEN, n - i)
            c = f.head.get(data[i:i + 3], -1)
            depth = 0
            seen = set()
            while c >= 0 and i - c <= MAXD and depth < DEPTH * 2:
                ln = _match_len(data, c, i, limit)
                if ln >= 3 and (i - c) not in seen:
                    cs.append((ln, i - c))
                    seen.add(i - c)
                c = f.prev[c]
                depth += 1
        for dd in (1, 2):
            if i >= dd and i + 2 <= n:
                ln = _match_len(data, i - dd, i, min(MAXLEN, n - i))
                if ln >= 2:
                    cs.append((ln, dd))
        cands.append(cs)
    INF = 1 << 60
    cost = [INF] * (n + 1)
    step = [None] * (n + 1)
    cost[n] = 1                       # the end byte
    for i in range(n - 1, -1, -1):
        # a literal: one byte (the run headers are left out of the model)
        best = cost[i + 1] + 1
        bstep = ('L', 1)
        for ln, d in cands[i]:
            near = d <= 255
            lens = set(range(2, min(ln, 17) + 1))
            lens.add(ln)
            if ln > 17:
                lens.add(18)
            for l in lens:
                c = (2 if l <= 17 else 3) + (0 if near else 1)
                if cost[i + l] + c < best:
                    best = cost[i + l] + c
                    bstep = ('C', l, d)
        cost[i] = best
        step[i] = bstep
    # emit as compress() does
    out = bytearray()
    lit = bytearray()

    def flush_lit():
        k = len(lit)
        p = 0
        while k - p > 0:
            m = min(k - p, 0x1fff)
            if m <= 31:
                out.append(0x40 | m)
            else:
                out.append(0x60 | (m >> 8))
                out.append(m & 0xff)
            out.extend(lit[p:p + m])
            p += m
        del lit[:k]

    def put_copy(m, d):
        if m <= 17 and d <= 255 and len(lit) <= 7:
            out.append(0x80 | (len(lit) << 4) | (m - 2))
            out.extend(lit)
            del lit[:]
            out.append(d)
            return
        flush_lit()
        if m <= 17:
            if d <= 255:
                out.extend(bytes((0x00 | (m - 2), d)))
            else:
                out.extend(bytes((0x10 | (m - 2), d & 0xff, d >> 8)))
        else:
            if d <= 255:
                out.extend(bytes((0x20 | (m >> 8), m & 0xff, d)))
            else:
                out.extend(bytes((0x30 | (m >> 8), m & 0xff, d & 0xff, d >> 8)))

    i = 0
    while i < n:
        s = step[i]
        if s[0] == 'L':
            lit.append(data[i])
            i += 1
        else:
            put_copy(s[1], s[2])
            i += s[1]
    flush_lit()
    out.append(0)
    return bytes(out)

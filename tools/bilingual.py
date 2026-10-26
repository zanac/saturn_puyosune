"""One disc, two languages: Japanese on a Japanese console, English on any
other (experimental).

The program on the disc is the English one. A stub runs first (the start
up code jumps to it instead of the game's main): it asks the SMPC for the
area code (INTBACK, status only); on a Japanese console (area 1) it puts
the original bytes of the program back from a table (texts, pointers,
the text engine), else it sets the English flag. Then it goes on to the
game's main.

The files the translation changes are on the disc twice: the original
under its own name, the English one with the last letter of the
extension made E (FONT.SPR -> FONT.SPE). The game opens its files by
name through one routine (0x06098b68: the name in capitals, then the
lookup); a hook between the two looks the name up in the list of
translated files and, with the English flag, asks for the E name.

Everything new goes in the free end of the program file, after the
English texts.
"""
import struct

BASE = 0x06004000
ENTRY_LITERAL = 0x06004024      # the start up code jumps to this address
MAIN = 0x0601440c
LOOKUP_LITERAL = 0x06098b8c     # the name routine calls this address
LOOKUP = 0x0609a554
FREE_FROM, FREE_TO = 0x060d1000, 0x060dc000

SF, IREG0, COMREG, OREG9 = 0x20100063, 0x20100001, 0x2010001f, 0x20100033
CCR = 0xfffffe92
AREA_JAPAN = 1


class Asm:
    """a few SH-2 instructions, with labels and a literal pool"""

    def __init__(self, at):
        self.at, self.code, self.fix, self.labels, self.lits = at, [], [], {}, []

    def here(self):
        return self.at + 2 * len(self.code)

    def label(self, name):
        self.labels[name] = self.here()

    def w(self, op):
        self.code.append(op)

    def lit(self, value, n):
        """mov.l @(literal),Rn"""
        self.fix.append(('lit', len(self.code), value))
        self.w(0xd000 | n << 8)

    def br(self, kind, target):
        op = {'bt': 0x8900, 'bf': 0x8b00, 'bra': 0xa000}[kind]
        self.fix.append((kind, len(self.code), target))
        self.w(op)

    def blob(self):
        # literal pool after the code, aligned
        if self.here() % 4:
            self.w(0x0009)
        pool = {}
        for kind, i, v in self.fix:
            if kind == 'lit' and v not in pool:
                pool[v] = len(pool)
        pool_at = self.here()
        for kind, i, v in self.fix:
            pc = self.at + 2 * i
            if kind == 'lit':
                a = pool_at + 4 * pool[v]
                d = (a - ((pc & ~3) + 4)) // 4
                assert 0 <= d < 256
                self.code[i] |= d
            else:
                d = (self.labels[v] - (pc + 4)) // 2
                if kind == 'bra':
                    assert -2048 <= d < 2048
                    self.code[i] |= d & 0xfff
                else:
                    assert -128 <= d < 128
                    self.code[i] |= d & 0xff
        out = struct.pack('>%dH' % len(self.code), *self.code)
        for v in sorted(pool, key=pool.get):
            out += struct.pack('>I', v)
        return out


def revert_table(english, japanese, skip):
    """(address, length, original bytes) for each run of changed bytes
    (runs closer than 8 bytes are one)"""
    diff = [i for i in range(len(japanese)) if english[i] != japanese[i]
            and not FREE_FROM <= BASE + i < FREE_TO and not any(s <= BASE + i < s + 4 for s in skip)]
    runs = []
    for i in diff:
        if runs and i - runs[-1][1] < 8:
            runs[-1][1] = i + 1
        else:
            runs.append([i, i + 1])
    out = b''
    for i, j in runs:
        b = japanese[i:j]
        out += struct.pack('>II', BASE + i, j - i) + b + bytes(-len(b) % 4)
    return out + bytes(8), len(runs)


def hook(at, flag, names):
    """r4: the name in capitals. A translated file with the English flag:
    the last letter made E. Then the lookup."""
    a = Asm(at)
    a.lit(flag, 1)
    a.w(0x6010)             # mov.b @r1,r0
    a.w(0x2008)             # tst r0,r0
    a.br('bt', 'tail')
    a.lit(names, 5)
    a.label('next')
    a.w(0x6050)             # mov.b @r5,r0
    a.w(0x2008)             # tst r0,r0
    a.br('bt', 'tail')
    a.w(0x6643)             # mov r4,r6
    a.w(0x6753)             # mov r5,r7
    a.label('cmp')
    a.w(0x6064)             # mov.b @r6+,r0
    a.w(0x6174)             # mov.b @r7+,r1
    a.w(0x3010)             # cmp/eq r1,r0
    a.br('bf', 'miss')
    a.w(0x2008)             # tst r0,r0
    a.br('bf', 'cmp')
    a.w(0x76fe)             # add #-2,r6     ; the last letter
    a.w(0xe045)             # mov #'E',r0
    a.w(0x2600)             # mov.b r0,@r6
    a.br('bra', 'tail')
    a.w(0x0009)
    a.label('miss')
    a.w(0x7510)             # add #16,r5
    a.br('bra', 'next')
    a.w(0x0009)
    a.label('tail')
    a.lit(LOOKUP, 0)
    a.w(0x402b)             # jmp @r0
    a.w(0x0009)
    return a.blob()


def stub(at, flag, table):
    a = Asm(at)
    a.lit(SF, 1)
    a.label('w1')
    a.w(0x6010)             # mov.b @r1,r0
    a.w(0xc801)             # tst #1,r0
    a.br('bf', 'w1')
    a.w(0xe001)             # mov #1,r0
    a.w(0x2100)             # mov.b r0,@r1     ; SF = 1
    a.lit(IREG0, 2)
    a.w(0x2200)             # mov.b r0,@r2     ; IREG0 = 1: status
    a.w(0xe000)             # mov #0,r0
    a.w(0x8022)             # mov.b r0,@(2,r2) ; IREG1 = 0: no pads
    a.w(0xe0f0)             # mov #-16,r0
    a.w(0x8024)             # mov.b r0,@(4,r2) ; IREG2 = f0
    a.lit(COMREG, 3)
    a.w(0xe010)             # mov #0x10,r0
    a.w(0x2300)             # mov.b r0,@r3     ; INTBACK
    a.label('w2')
    a.w(0x6010)             # mov.b @r1,r0
    a.w(0xc801)             # tst #1,r0
    a.br('bf', 'w2')
    a.lit(OREG9, 3)
    a.w(0x6030)             # mov.b @r3,r0
    a.w(0xc90f)             # and #15,r0
    a.w(0x8800 | AREA_JAPAN)  # cmp/eq #1,r0
    a.br('bt', 'japan')
    a.lit(flag, 1)
    a.w(0xe001)             # mov #1,r0
    a.w(0x2100)             # mov.b r0,@r1
    a.br('bra', 'go')
    a.w(0x0009)
    a.label('japan')
    a.lit(table, 5)
    a.label('run')
    a.w(0x6656)             # mov.l @r5+,r6   ; address
    a.w(0x2668)             # tst r6,r6
    a.br('bt', 'purge')
    a.w(0x6756)             # mov.l @r5+,r7   ; length
    a.label('copy')
    a.w(0x6054)             # mov.b @r5+,r0
    a.w(0x2600)             # mov.b r0,@r6
    a.w(0x7601)             # add #1,r6
    a.w(0x4710)             # dt r7
    a.br('bf', 'copy')
    a.w(0x7503)             # add #3,r5
    a.w(0xe0fc)             # mov #-4,r0
    a.w(0x2509)             # and r0,r5
    a.br('bra', 'run')
    a.w(0x0009)
    a.label('purge')
    a.lit(CCR, 1)
    a.w(0x6010)             # mov.b @r1,r0
    a.w(0xcb10)             # or #0x10,r0     ; cache purge
    a.w(0x2100)             # mov.b r0,@r1
    a.label('go')
    a.lit(MAIN, 4)
    a.w(0x442b)             # jmp @r4
    a.w(0x0009)
    return a.blob()


def build(prog, japanese, names):
    """prog: text.Program, the English program; japanese: the original
    program file; names: the translated files (their original names)"""
    assert prog.b[ENTRY_LITERAL - BASE:ENTRY_LITERAL - BASE + 4] == struct.pack('>I', MAIN)
    assert prog.b[LOOKUP_LITERAL - BASE:LOOKUP_LITERAL - BASE + 4] == struct.pack('>I', LOOKUP)
    table, runs = revert_table(prog.b, japanese, (ENTRY_LITERAL, LOOKUP_LITERAL))
    flag = prog.place(bytes(4), 4)
    table_at = prog.place(table, 4)
    listing = b''.join(n.upper().encode().ljust(16, b'\0') for n in sorted(names)) + bytes(16)
    assert all(len(n) < 16 for n in names)
    names_at = prog.place(listing, 4)
    h = prog.place(bytes(len(hook(0, 1, 2))), 4)
    prog.b[h - BASE:h - BASE + len(hook(h, flag, names_at))] = hook(h, flag, names_at)
    s = prog.place(bytes(len(stub(0, 1, 2))), 4)
    prog.b[s - BASE:s - BASE + len(stub(s, flag, table_at))] = stub(s, flag, table_at)
    prog.b[LOOKUP_LITERAL - BASE:LOOKUP_LITERAL - BASE + 4] = struct.pack('>I', h)
    prog.b[ENTRY_LITERAL - BASE:ENTRY_LITERAL - BASE + 4] = struct.pack('>I', s)
    return ['bilingual: %d runs to revert (%d bytes), %d files twice, free area to %x'
            % (runs, len(table), len(names), prog.free)]


def english_name(name):
    return name[:-1] + 'E'

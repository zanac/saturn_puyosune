"""All regions in the boot header (IP.BIN, the first 16 sectors), so that a
console or BIOS of any region boots the disc.

The BIOS checks the area symbols of the header (offset 0x40) and the
area code groups after the security code (0xe00, 32 bytes each: a0 0e 00
09, 'For JAPAN.'...). The disc has only Japan; the groups of the other
areas go after it, and the initial program that followed is moved down
by their size. Its few absolute references to itself are moved with it
(the code is otherwise PC relative); the IP size (0xe0) has room.
"""
import struct

# USA first: an emulator that takes the region from the disc (the first
# symbol) starts as a US console, so the two-language disc starts in English
AREAS = [('U', 'For USA and CANADA.'), ('E', 'For EUROPE.'), ('J', 'For JAPAN.'),
         ('T', 'For TAIWAN and PHILIPINES.'), ('B', 'For BRAZIL.'), ('K', 'For KOREA.'),
         ('A', 'For ASIA PAL area.'), ('L', 'For LATIN AMERICA.')]
GROUPS = 0xe00
IP_BASE = 0x06002000
SECTORS = 16


def group(text):
    return b'\xa0\x0e\x00\x09' + text.encode().ljust(28)


def patch(ip):
    """ip: the 32 KB of IP.BIN; returns the patched copy"""
    ip = bytearray(ip)
    assert ip[:16] == b'SEGA SEGASATURN '
    assert ip[0x40:0x50] == b'J'.ljust(16) and ip[GROUPS:GROUPS + 32] == group('For JAPAN.')
    size = struct.unpack('>I', ip[0xe0:0xe4])[0]
    start = GROUPS + 32                  # the initial program
    end = len(ip.rstrip(b'\0'))
    end += -end % 4
    shift = 32 * (len(AREAS) - 1)
    assert end + shift <= size
    code = bytearray(ip[start:end])
    lo, hi = IP_BASE + start, IP_BASE + end + 16
    n = 0
    for i in range(0, len(code) - 3, 2):
        v = struct.unpack('>I', code[i:i + 4])[0]
        if lo <= v < hi and (start + i) % 4 == 0:
            code[i:i + 4] = struct.pack('>I', v + shift)
            n += 1
    ip[0x40:0x50] = ''.join(a for a, t in AREAS).encode().ljust(16)
    ip[GROUPS:GROUPS + 32 * len(AREAS)] = b''.join(group(t) for a, t in AREAS)
    ip[start + shift:start + shift + len(code)] = code
    return bytes(ip), n


def build(track):
    ip = b''.join(track.data(i) for i in range(SECTORS))
    new, n = patch(ip)
    for i in range(SECTORS):
        track.write_data(i, new[i * 2048:(i + 1) * 2048])
    return ['boot header: all regions (%d references moved)' % n]

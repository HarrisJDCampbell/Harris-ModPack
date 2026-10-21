"""Draw a 16x16 pixel-art dog head and write it as a scaled PNG (no PIL needed)."""
import struct, sys, zlib

ART = [
    "................",
    "..EE........EE..",
    ".EeeE......EeeE.",
    ".EeeEBBBBBBEeeE.",
    ".EeEBBBBBBBBEeE.",
    "..EBBBBBBBBBBE..",
    "..BBWWBBBBWWBB..",
    "..BBWKBBBBWKBB..",
    "..BBBBLLLLBBBB..",
    "..BBBLLLLLLBBB..",
    "...BBLLNNLLBB...",
    "...BBLLLLLLBB...",
    "....BLLMMLLB....",
    "....BBLPPLBB....",
    ".....BBBBBB.....",
    "................",
]
PAL = {
    ".": None,
    "E": (92, 56, 32), "e": (140, 88, 52),    # ears
    "B": (196, 134, 72),                       # fur
    "L": (238, 206, 160),                      # muzzle
    "W": (255, 255, 255), "K": (24, 20, 20),   # eyes
    "N": (30, 24, 24),                         # nose
    "M": (90, 40, 40), "P": (232, 104, 120),   # mouth, tongue
}
BG = (40, 44, 52)

def png(path, scale, bg):
    n = len(ART)
    rows = []
    for y in range(n * scale):
        row = bytearray([0])
        for x in range(n * scale):
            c = PAL[ART[y // scale][x // scale]]
            if c is None:
                row += bytes(bg + (255,)) if bg else b"\0\0\0\0"
            else:
                row += bytes(c + (255,))
        rows.append(bytes(row))
    raw = b"".join(rows)
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    size = n * scale
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    open(path, "wb").write(data)

png(sys.argv[1], 8, None)     # transparent icon for Prism
png(sys.argv[2], 8, BG)       # logo for the mod list

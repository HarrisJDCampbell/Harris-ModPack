#!/usr/bin/env python3
"""Render text pixel-art files (art/*.txt) into PNG textures. No dependencies.

Format of an art file:

    # comments start with #
    out: mod/src/main/resources/assets/harris/textures/item/thing.png
    palette:
      O = 58 30 20        # r g b  (or r g b a)
      m = 240 214 150
    grid:
      ....OOOO....        # '.' is transparent; every row the same width

    python3 scripts/pixelart.py            # render every art/*.txt
    python3 scripts/pixelart.py --preview  # also write 16x-scaled previews to .test/art/
"""
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def write_png(path: Path, pixels: list[list[tuple[int, int, int, int]]], scale: int = 1) -> None:
    h, w = len(pixels) * scale, len(pixels[0]) * scale
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw += bytes(pixels[y // scale][x // scale])

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def parse(src: Path) -> tuple[Path, list[list[tuple[int, int, int, int]]]]:
    out, palette, grid, section = None, {".": (0, 0, 0, 0)}, [], None
    for line in src.read_text().splitlines():
        line = line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        s = line.strip()
        if s.startswith("out:"):
            out = ROOT / s[4:].strip()
        elif s in ("palette:", "grid:"):
            section = s[:-1]
        elif section == "palette":
            key, value = s.split("=", 1)
            nums = [int(n) for n in value.split()]
            palette[key.strip()] = tuple(nums + [255] * (4 - len(nums)))
        elif section == "grid":
            grid.append(s)
    if out is None or not grid:
        raise SystemExit(f"{src}: needs an 'out:' line and a grid")
    if len({len(r) for r in grid}) != 1:
        raise SystemExit(f"{src}: grid rows have different widths")
    missing = {c for row in grid for c in row} - palette.keys()
    if missing:
        raise SystemExit(f"{src}: colours not in palette: {''.join(sorted(missing))}")
    return out, [[palette[c] for c in row] for row in grid]


def main() -> None:
    preview = "--preview" in sys.argv
    for src in sorted((ROOT / "art").glob("*.txt")):
        out, pixels = parse(src)
        write_png(out, pixels)
        print(f"{src.relative_to(ROOT)} -> {out.relative_to(ROOT)}")
        if preview:
            write_png(ROOT / ".test" / "art" / f"{src.stem}.png", pixels, scale=16)


if __name__ == "__main__":
    main()

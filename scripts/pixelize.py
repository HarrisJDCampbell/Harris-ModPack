#!/usr/bin/env python3
"""Turn any image (a drawing, a photo, a screenshot) into a clean Minecraft texture.

    make pixelize IN=~/Downloads/pie.png NAME=mums_shepherds_pie
    python3 scripts/pixelize.py IN.png OUT.png [--size 16] [--colors 12] [--keep-bg] [--outline]

Why not just resize? Most "pixel art" images are ~1024px with a wobbly grid,
soft edges and hundreds of colours. A normal downscale averages all that into
mush. Instead this:
  1. removes a flat background (flood fill from the corners), unless --keep-bg;
  2. crops to the subject and centres it on a square canvas;
  3. reduces the whole image to a small palette FIRST, so every pixel is one
     of N clean colours;
  4. picks each output pixel by majority vote of the source block it covers
     (the mode, not the mean), so edges stay crisp and no new in-between
     colours appear;
  5. optionally adds a 1px dark outline, the way vanilla item icons look.
It also writes a 16x preview to .test/art/ so you can eyeball it.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from PIL import Image


def remove_background(img: Image.Image, tolerance: int = 40) -> Image.Image:
    """Flood-fill from each corner, making anything close to the corner colour transparent."""
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    seen = bytearray(w * h)
    for sx, sy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        base = px[sx, sy]
        if base[3] == 0:
            continue
        stack = [(sx, sy)]
        while stack:
            x, y = stack.pop()
            i = y * w + x
            if seen[i]:
                continue
            seen[i] = 1
            r, g, b, a = px[x, y]
            if a and abs(r - base[0]) + abs(g - base[1]) + abs(b - base[2]) <= tolerance:
                px[x, y] = (0, 0, 0, 0)
                if x > 0: stack.append((x - 1, y))
                if x < w - 1: stack.append((x + 1, y))
                if y > 0: stack.append((x, y - 1))
                if y < h - 1: stack.append((x, y + 1))
    return img


def crop_square(img: Image.Image, margin: float = 0.04) -> Image.Image:
    box = img.getchannel("A").point(lambda a: 255 if a > 32 else 0).getbbox()
    if box:
        img = img.crop(box)
    side = int(max(img.size) * (1 + 2 * margin))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    return canvas


def pixelize(img: Image.Image, size: int, colors: int) -> Image.Image:
    alpha = img.getchannel("A")
    rgb = Image.new("RGB", img.size, (0, 0, 0))
    rgb.paste(img, mask=alpha)
    pal = rgb.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    palette = pal.getpalette()
    idx, a = pal.load(), alpha.load()
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    o = out.load()
    cell = img.width / size
    for oy in range(size):
        for ox in range(size):
            x0, x1 = int(ox * cell), max(int((ox + 1) * cell), int(ox * cell) + 1)
            y0, y1 = int(oy * cell), max(int((oy + 1) * cell), int(oy * cell) + 1)
            votes, opaque, total = Counter(), 0, 0
            for y in range(y0, y1):
                for x in range(x0, x1):
                    total += 1
                    if a[x, y] > 127:
                        opaque += 1
                        votes[idx[x, y]] += 1
            if opaque * 2 >= total and votes:
                c = votes.most_common(1)[0][0]
                o[ox, oy] = (palette[3 * c], palette[3 * c + 1], palette[3 * c + 2], 255)
    return out


def add_outline(img: Image.Image) -> Image.Image:
    """Darken opaque pixels that touch transparency, like vanilla item outlines."""
    out = img.copy()
    src, dst = img.load(), out.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if not a:
                continue
            edge = any(not (0 <= x + dx < w and 0 <= y + dy < h) or src[x + dx, y + dy][3] == 0
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge:
                dst[x, y] = (int(r * 0.45), int(g * 0.45), int(b * 0.45), 255)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--size", type=int, default=16)
    ap.add_argument("--colors", type=int, default=12)
    ap.add_argument("--keep-bg", action="store_true", help="don't remove the background")
    ap.add_argument("--outline", action="store_true", help="darken the outer edge")
    args = ap.parse_args()

    img = Image.open(Path(args.input).expanduser()).convert("RGBA")
    if not args.keep_bg:
        img = remove_background(img)
    img = crop_square(img)
    out = pixelize(img, args.size, args.colors)
    if args.outline:
        out = add_outline(out)

    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.save(dest)
    # Preview goes in .test/ so it never ends up inside the mod jar.
    preview = Path(__file__).resolve().parent.parent / ".test" / "art" / f"{dest.stem}.preview.png"
    preview.parent.mkdir(parents=True, exist_ok=True)
    out.resize((args.size * 16, args.size * 16), Image.Resampling.NEAREST).save(preview)
    print(f"{dest}  (preview: {preview})")


if __name__ == "__main__":
    main()

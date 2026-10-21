#!/usr/bin/env python3
"""Draw the animated README dog: a small black-and-white pixel dog trotting along.

    .venv/bin/python scripts/readme_dog.py     (make .venv/bin/python first)

Writes assets/olly-trot.gif. Each frame is built from simple parts (body, head,
legs, tail) on a small grid, then scaled up with hard pixel edges. The legs move
in a trot (diagonal pairs together), the tail wags, the body bobs, and the ground
scrolls underneath so he looks like he's going somewhere. A grey outline keeps
the black fur visible on GitHub's dark theme as well as the light one.
"""
from pathlib import Path

from PIL import Image

W, H, SCALE, FRAMES = 44, 26, 5, 8
CLEAR, BLACK, WHITE, PINK, OUTLINE, GROUND = 0, 1, 2, 3, 4, 5
PALETTE = [
    (255, 0, 255),    # transparent key
    (22, 22, 24),     # fur
    (244, 244, 240),  # white patches
    (232, 112, 128),  # tongue
    (139, 148, 158),  # outline (reads on light and dark backgrounds)
    (139, 148, 158),  # ground dashes
]


def frame(i: int) -> list[list[int]]:
    g = [[CLEAR] * W for _ in range(H)]

    def px(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = c

    def rect(x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                px(x, y, c)

    bob = 1 if i % 4 in (1, 2) else 0          # body rises mid-stride
    ox, oy = 8, 3 - bob                       # dog origin

    # tail: wags between three angles
    tail = [[(0, 0), (-1, -1), (-2, -2), (-3, -3)],
            [(0, 0), (-1, -1), (-2, -1), (-3, -2)],
            [(0, 0), (-1, 0), (-2, -1), (-3, -1)]][[0, 1, 2, 1][i % 4]]
    for dx, dy in tail:
        px(ox + 5 + dx, oy + 9 + dy, BLACK)
    px(ox + 5 + tail[-1][0], oy + 9 + tail[-1][1], WHITE)   # white tail tip

    # body
    rect(ox + 6, oy + 8, ox + 18, oy + 14, BLACK)
    for x, y in ((ox + 6, oy + 8), (ox + 6, oy + 14), (ox + 18, oy + 14)):
        px(x, y, CLEAR)
    rect(ox + 15, oy + 11, ox + 19, oy + 15, WHITE)           # white chest
    rect(ox + 10, oy + 14, ox + 13, oy + 14, WHITE)           # white belly

    # head + neck
    rect(ox + 17, oy + 5, ox + 22, oy + 11, BLACK)
    px(ox + 22, oy + 5, CLEAR)                                # rounded head
    rect(ox + 22, oy + 7, ox + 25, oy + 10, WHITE)            # white muzzle
    px(ox + 26, oy + 7, BLACK)                                # nose
    px(ox + 25, oy + 7, BLACK)
    rect(ox + 20, oy + 4, ox + 20, oy + 9, WHITE)             # white blaze
    px(ox + 22, oy + 6, WHITE)                                # eye shine
    px(ox + 22, oy + 7, BLACK)
    rect(ox + 17, oy + 2, ox + 18, oy + 5, BLACK)             # ear
    px(ox + 19, oy + 3, BLACK)
    if i % 4 in (1, 2):                                       # tongue out mid-stride
        px(ox + 24, oy + 11, PINK)
        px(ox + 24, oy + 12, PINK)

    # legs: trot = diagonal pairs move together
    swing = [2, 1, -1, 0][i % 4]
    legs = [(ox + 7, swing), (ox + 10, -swing), (ox + 14, -swing), (ox + 17, swing)]
    for x, s in legs:
        lift = 1 if s > 0 else 0
        top, bottom = oy + 15, oy + 18 - lift + bob
        for y in range(top, bottom + 1):
            px(x + (s if y > top + 1 else 0), y, BLACK)
            px(x + 1 + (s if y > top + 1 else 0), y, BLACK)
        px(x + s, bottom, WHITE)                              # white socks
        px(x + 1 + s, bottom, WHITE)

    # outline: any clear pixel touching the dog becomes grey
    snap = [row[:] for row in g]
    for y in range(H):
        for x in range(W):
            if snap[y][x] == CLEAR and any(
                0 <= x + dx < W and 0 <= y + dy < H and snap[y + dy][x + dx] in (BLACK, WHITE, PINK)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                g[y][x] = OUTLINE

    # scrolling ground dashes
    for x in range(W):
        if (x + i * 2) % 8 < 3:
            px(x, H - 2, GROUND)
    return g


def main() -> None:
    images = []
    flat = [c for rgb in PALETTE for c in rgb]
    for i in range(FRAMES):
        grid = frame(i)
        im = Image.new("P", (W, H))
        im.putpalette(flat)
        im.putdata([c for row in grid for c in row])
        images.append(im.resize((W * SCALE, H * SCALE), Image.Resampling.NEAREST))
    out = Path(__file__).resolve().parent.parent / "assets" / "olly-trot.gif"
    images[0].save(out, save_all=True, append_images=images[1:], duration=110, loop=0,
                   transparency=CLEAR, disposal=2, optimize=False)
    # contact sheet for eyeballing all frames at once (not committed)
    sheet = Image.new("RGB", (W * SCALE * 4, H * SCALE * 4), (255, 255, 255))
    for i, im in enumerate(images):
        rgba = im.convert("RGBA")
        pix = rgba.load()
        for y in range(rgba.height):
            for x in range(rgba.width):
                if pix[x, y][:3] == PALETTE[CLEAR]:
                    pix[x, y] = (0, 0, 0, 0)
        for row, bg in ((0, (255, 255, 255)), (2, (13, 17, 23))):  # GitHub light and dark backgrounds
            tile = Image.new("RGBA", rgba.size, bg + (255,))
            tile.alpha_composite(rgba)
            sheet.paste(tile, ((i % 4) * W * SCALE, (row + i // 4) * H * SCALE))
    sheet_path = out.parent.parent / ".test" / "art" / "olly-trot-sheet.png"
    sheet_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(sheet_path)
    print(out, sheet_path)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Pack per-frame PNGs of one Glitch item into a sprite sheet (grid, row-major).

Input:  a directory containing 0.png, 1.png, 2.png, ... (sorted by name)
Output (in the out dir):
  - sheet.png    : frames laid out row-major, each frame trimmed to its
                   content bounding box and centered in a uniform cell,
                   transparent background.
  - sheet.json   : per-frame offset/size + cell dimensions for engine use.

Wrapping: if a single row would exceed 10000 px (Pillow dimension limit
headroom), the sheet wraps into multiple rows.

Usage:  python3 sheetpack.py <frames_dir> <out_dir>
"""
import json
import re
import sys
from math import ceil

from PIL import Image

MAX_DIM = 10000  # stay well under Pillow's 10k / 178MP limits
MAX_MP = 150e6   # per-sheet pixel cap (Pillow's load limit is 179 MP);
                 # bigger segments are split into sheet_0, sheet_1, ...
PAD = 4          # transparent padding around each frame in its cell


def content_bbox(img):
    """Bounding box of non-transparent pixels, or None if empty."""
    if img.mode not in ("RGBA", "LA", "PA"):
        return (0, 0, img.width, img.height)
    return img.getchannel("A").getbbox()


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    frames_dir, out_dir = sys.argv[1], sys.argv[2]

    import os
    os.makedirs(out_dir, exist_ok=True)

    files = sorted(
        (f for f in os.listdir(frames_dir)
         if re.search(r"\.(png|webp)$", f, re.I)),
        key=lambda n: (int(re.match(r"\D*(\d+)", n).group(1)), n),
    )
    if not files:
        print(f"no frames found in {frames_dir}", file=sys.stderr)
        sys.exit(1)

    imgs = []
    for f in files:
        im = Image.open(os.path.join(frames_dir, f)).convert("RGBA")
        bb = content_bbox(im)
        if bb is None:
            # fully transparent frame -> 1x1 placeholder
            im2 = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
            src_crop = (0, 0, 0, 0)
        else:
            im2 = im.crop(bb)
            src_crop = bb
        imgs.append((f, im2, src_crop))

    cell_w = max(im.width for _, im, _ in imgs) + PAD
    cell_h = max(im.height for _, im, _ in imgs) + PAD
    n = len(imgs)

    cols = n if cell_w * n <= MAX_DIM else max(1, MAX_DIM // cell_w)
    # split into parts so each sheet stays under MAX_MP
    rows_per_part = max(1, int(MAX_MP // (cell_w * cols) // cell_h))
    per_part = rows_per_part * cols
    parts = ceil(n / per_part)

    sheets = []
    for p in range(parts):
        lo = p * per_part
        hi = min(lo + per_part, n)
        part = imgs[lo:hi]
        rows = ceil(len(part) / cols)
        sheet = Image.new("RGBA", (cell_w * cols, cell_h * rows),
                          (0, 0, 0, 0))
        frames = []
        for idx, (fname, im, src_crop) in enumerate(part):
            c, r = idx % cols, idx // cols
            ox = c * cell_w + (cell_w - im.width) // 2
            oy = r * cell_h + (cell_h - im.height) // 2
            sheet.paste(im, (ox, oy), im)
            frames.append({
                "frame": lo + idx,
                "src": fname,
                "offset": [ox, oy],
                "size": [im.width, im.height],
                "src_crop": list(src_crop),
            })
        sfile = "sheet.png" if parts == 1 else f"sheet_{p}.png"
        sheet.save(os.path.join(out_dir, sfile))
        sheets.append({
            "file": sfile,
            "cols": cols,
            "rows": rows,
            "frame_range": [lo, hi - 1],
            "frames": frames,
        })

    meta = {
        "cell_width": cell_w,
        "cell_height": cell_h,
        "padding": PAD,
        "count": n,
        "cols": cols,
        "sheets": sheets,
    }
    with open(os.path.join(out_dir, "sheet.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    if parts == 1:
        s = sheets[0]
        print(f"{n} frames -> {os.path.join(out_dir, 'sheet.png')} "
              f"({s['cols']}x{s['rows']} grid)")
    else:
        print(f"{n} frames -> {parts} sheets "
              f"(cell {cell_w}x{cell_h}, {cols} cols) in {out_dir}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
qa_sheets.py - QA contact sheet over an export root.

For every item (dirs containing item.json): shows the icon segment plus
samples from the biggest animated segment, on a checkerboard, with
segment labels. Writes <out>.png.

Usage: qa_sheets.py <export_root> <out.png>
"""
import json
import os
import sys
import warnings

from PIL import Image, ImageDraw

warnings.filterwarnings("ignore")
H = 100          # frame display height
TH = 18          # label band
CELL_PAD = 10
COLS = 2         # item cells per row


def checker(w, h, sq=8):
    c = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(c)
    for y in range(0, h, sq):
        for x in range(0, w, sq):
            if (x // sq + y // sq) % 2:
                d.rectangle([x, y, x + sq - 1, y + sq - 1],
                            fill=(228, 228, 228))
    return c


def cell(info):
    base = info["_dir"]
    segs = info["segments"]
    icon_name = info.get("icon_segment")
    icon_seg = next((s for s in segs if s["name"] == icon_name), segs[0])
    biggest = max(segs, key=lambda s: s["frames"])

    picks = []
    for seg in [icon_seg] + ([biggest] if biggest is not icon_seg else []):
        d = os.path.join(base, seg["frames_dir"])
        fs = sorted(f for f in os.listdir(d) if f.endswith(".png"))
        k = min(4 if seg is biggest else 1, len(fs))
        step = max(1, len(fs) // k) if len(fs) > 1 else 1
        idxs = sorted({i * step for i in range(k)})
        for i in idxs:
            im = Image.open(os.path.join(d, fs[i])).convert("RGBA")
            sc = H / im.height
            im = im.resize((max(1, round(im.width * sc)), H),
                           Image.LANCZOS)
            picks.append((seg["name"], im))

    w = sum(im.width for _, im in picks) + CELL_PAD * (len(picks) + 1)
    title = info.get("server", {}).get("label", info["item"])
    title += f"  ({info['segment_count']} segs, " \
             f"{info['total_frames']} frames, bg {info['bg_color']})"
    ch = H + TH + 20 + CELL_PAD
    canvas = checker(w, ch)
    d = ImageDraw.Draw(canvas)
    d.text((CELL_PAD, 3), title, fill=(20, 20, 20))
    x = CELL_PAD
    y0 = 20
    for name, im in picks:
        canvas.paste(im, (x, y0), im)
        d.text((x + 2, y0 + H + 2), name, fill=(90, 30, 30))
        x += im.width + CELL_PAD
    return canvas


def main():
    export_root, out = sys.argv[1], sys.argv[2]
    infos = []
    for dirpath, _, files in os.walk(export_root):
        if "item.json" in files:
            p = os.path.join(dirpath, "item.json")
            info = json.load(open(p))
            info["_dir"] = dirpath
            infos.append(info)
    infos.sort(key=lambda i: i["_dir"])

    cells = [cell(i) for i in infos]
    cw = max(c.width for c in cells)
    ch = max(c.height for c in cells)
    rows = (len(cells) + COLS - 1) // COLS
    sheet = Image.new("RGB", (cw * COLS + 8, ch * rows + 8), (250, 250, 250))
    for n, c in enumerate(cells):
        sheet.paste(c, (4 + (n % COLS) * cw, 4 + (n // COLS) * ch))
    sheet.save(out)
    print(f"{len(cells)} items -> {out} ({sheet.width}x{sheet.height})")


if __name__ == "__main__":
    main()

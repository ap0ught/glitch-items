#!/usr/bin/env python3
"""
package.py - bundle a finished export tree into a deliverable.

Builds <dest>/glitch-items-export/ (item tree + meta tables + manifest +
README) and a single <dest>/glitch-items-export.zip alongside it.
Intended to run from /tmp (tmpfs) onto /home (real disk, 88 GB free).

Usage: package.py <export_root> <dest_dir>
"""
import datetime
import json
import os
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "glitch-items-export"


def scan(export_root):
    items = 0
    segs = 0
    frames = 0
    scale = None
    for dirpath, _, files in os.walk(export_root):
        if "item.json" in files:
            info = json.load(open(os.path.join(dirpath, "item.json")))
            items += 1
            segs += info["segment_count"]
            frames += info["total_frames"]
            scale = info.get("scale", scale)
    return items, segs, frames, scale


def main():
    export_root, dest = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    os.makedirs(dest, exist_ok=True)
    out = os.path.join(dest, NAME)
    if os.path.exists(out):
        print(f"refusing to overwrite existing {out}", file=sys.stderr)
        sys.exit(1)

    items, segs, frames, scale = scan(export_root)
    print(f"scanned {items} items / {segs} segments / {frames} frames "
          f"(scale {scale})")

    os.makedirs(os.path.join(out, "meta"))
    print(f"copying tree -> {out}/items/")
    shutil.copytree(export_root, os.path.join(out, "items"))

    for f in ("scenes.tsv", "server-items.tsv", "swf-manifest.tsv"):
        p = os.path.join(HERE, "data", f)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(out, "meta", f))

    manifest = {
        "name": NAME,
        "source_repo": "ap0ught/glitch-items (CC0, Tiny Speck 'Glitch')",
        "generated": datetime.date.today().isoformat(),
        "items": items,
        "segments": segs,
        "frames": frames,
        "scale": scale,
        "layout": {
            "items/<category>/<item>/item.json": "per-item manifest",
            "items/<category>/<item>/<segment>/frames/": "keyed RGBA frames",
            "items/<category>/<item>/<segment>/sheet*.png": "packed grid sheet(s)",
            "items/<category>/<item>/<segment>/sheet.json": "per-frame offsets",
            "items/<category>/<item>/icon_official.png": "official 40x40 (if item had a server config)",
            "meta/": "source tables (scenes/labels/bg, server configs, swf dims)",
        },
        "segment_naming": "game scene/label state names; labels win ties",
        "backgrounds": "removed per-SWF via SetBackgroundColor tag "
                       "(border-flood + halo decontamination)",
    }
    with open(os.path.join(out, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)

    readme = f"""# Glitch items - engine-ready sprite export

{items} items / {segs} animation segments / {frames} frames, rendered at
{scale}x with Ruffle, background-keyed per item, packed into grid sprite
sheets. Source: CC0 Flash assets from ap0ught/glitch-items.

## Layout
items/<category>/<item>/
    item.json        manifest: stage, fps, scale, bg_color, segments
    <segment>/       named by the game's own scene/label state
        frames/      keyed (transparent) RGBA frames
        sheet*.png   packed grid (sheet_0, sheet_1, ... if >150 MP)
        sheet.json   per-frame offset/size + sheet list
    icon_official.png  official 40x40 from the server config (when present)
meta/            source tables: scenes/labels/bg, server item configs,
                 SWF dimensions/rates
manifest.json    this summary

## Using a segment
read <segment>/sheet.json: for sheet `sheets[i]`, frame k is at
`offset` with `size` in that sheet's PNG (uniform cell = cell_width x
cell_height, row-major, `cols` per row). Animation = play the frames of
that segment in order at the item's `fps`. `icon_segment` is the
preferred still (the game's iconic/`1` state when present).
"""
    with open(os.path.join(out, "README.md"), "w") as fh:
        fh.write(readme)

    zip_path = os.path.join(dest, NAME + ".zip")
    print(f"zipping -> {zip_path}")
    n = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(out):
            for f in sorted(files):
                full = os.path.join(root, f)
                z.write(full, os.path.relpath(full, dest))
                n += 1
    print(f"done: {out} + {zip_path} "
          f"({os.path.getsize(zip_path) / 1e9:.2f} GB, {n} files)")


if __name__ == "__main__":
    main()

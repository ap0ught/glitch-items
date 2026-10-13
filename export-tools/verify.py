#!/usr/bin/env python3
"""
verify.py - audit an export tree against the source tables.

For every item dir containing item.json, checks:
  - source is a known repo SWF (scenes.tsv)
  - total_frames / stage / fps match the tables
  - segments tile the timeline: start_frame contiguous from 0, no gaps,
    and sum of segment frames == total_frames
  - each segment's frames/ holds exactly as many PNGs as declared
  - each segment has a sheet.json whose sheets tile [0, frames-1]
    with no gaps/overlaps, and every sheet PNG exists with
    dimensions >= its used cell area
  - icon_segment is one of the segments
Plus a whole-tree summary (items / segments / frames / disk).

Usage:
  verify.py <export_root> [scenes.tsv] [manifest.tsv]
            [--expected-items N] [--expected-segments N]

Exit 0 = no hard errors (warns may be present), 1 = hard errors.
"""
import argparse
import json
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def load_tables(scenes_tsv, manifest_tsv):
    seg = {}
    for line in open(scenes_tsv).read().splitlines()[1:]:
        rel, frames, bg, scenes, labels = line.split("\t")
        rel = rel[2:] if rel.startswith("./") else rel
        seg[rel] = (int(frames) if frames else 0, bg or "ff/ff/ff",
                    scenes, labels)
    meta = {}
    for line in open(manifest_tsv).read().splitlines():
        p = line.split("\t")
        if len(p) == 5:
            rel = p[0][2:] if p[0].startswith("./") else p[0]
            meta[rel] = (int(float(p[1])), int(float(p[2])),
                         float(p[3]), int(float(p[4])))
    return seg, meta


def item_dir_size(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    return total


def check_item(dirpath, tables):
    """Return (errors, warns, stats_dict)."""
    seg_table, manifest = tables
    p = os.path.join(dirpath, "item.json")
    info = json.load(open(p))
    errors, warns = [], []
    stats = {"segments": 0, "frames": 0}

    src = info["source"]
    if src not in seg_table:
        errors.append(f"source {src!r} not in scenes.tsv")
        return errors, warns, stats
    frames_t, bg, scenes, labels = seg_table[src]
    if info["total_frames"] != frames_t:
        errors.append(f"total_frames {info['total_frames']} != "
                      f"table {frames_t}")
    if info["bg_color"] != bg:
        errors.append(f"bg_color {info['bg_color']} != table {bg}")
    if src in manifest:
        w, h, fps, _ = manifest[src]
        if info["stage"] != [w, h]:
            errors.append(f"stage {info['stage']} != manifest [{w},{h}]")
        if info["fps"] != fps:
            errors.append(f"fps {info['fps']} != manifest {fps}")

    # segment tiling
    pos = 0
    for s in info["segments"]:
        stats["segments"] += 1
        stats["frames"] += s["frames"]
        if s["start_frame"] != pos:
            errors.append(f"segment {s['name']!r} starts at "
                          f"{s['start_frame']}, expected {pos}")
        pos += s["frames"]
        fdir = os.path.join(dirpath, s["frames_dir"])
        if not os.path.isdir(fdir):
            errors.append(f"missing frames dir {s['frames_dir']}")
            continue
        npng = len([f for f in os.listdir(fdir) if f.endswith(".png")])
        if npng != s["frames"]:
            warns.append(f"{s['name']}: {npng} pngs != declared {s['frames']}")
        sjp = os.path.join(dirpath, s["name"], "sheet.json")
        if not os.path.exists(sjp):
            errors.append(f"missing sheet.json for {s['name']}")
            continue
        sj = json.load(open(sjp))
        lo = 0
        for sh in sj["sheets"]:
            a, b = sh["frame_range"]
            if a != lo:
                errors.append(f"{s['name']}/{sh['file']}: range "
                              f"[{a},{b}] continues from {lo}")
            lo = b + 1
            fp = os.path.join(dirpath, s["name"], sh["file"])
            if not os.path.exists(fp):
                errors.append(f"missing sheet file {sh['file']}")
                continue
            im = Image.open(fp)
            need_w = max((f["offset"][0] + f["size"][0]
                          for f in sh["frames"]), default=0)
            need_h = max((f["offset"][1] + f["size"][1]
                          for f in sh["frames"]), default=0)
            if im.width < need_w or im.height < need_h:
                errors.append(f"{sh['file']}: {im.size} < needed "
                              f"{(need_w, need_h)}")
        if lo - 1 != s["frames"] - 1:
            errors.append(f"{s['name']}: sheets cover 0..{lo - 1}, "
                          f"expected 0..{s['frames'] - 1}")
        if s["sheets"] and [os.path.basename(x) for x in s["sheets"]] \
                != [sh["file"] for sh in sj["sheets"]]:
            errors.append(f"{s['name']}: item.json sheets != sheet.json")
    if pos != info["total_frames"]:
        errors.append(f"segments cover {pos} frames, "
                      f"total_frames {info['total_frames']}")
    if info["icon_segment"] not in [s["name"] for s in info["segments"]]:
        errors.append(f"icon_segment {info['icon_segment']!r} not a segment")
    return errors, warns, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export_root")
    ap.add_argument("scenes_tsv", nargs="?",
                    default=os.path.join(HERE, "data", "scenes.tsv"))
    ap.add_argument("manifest_tsv", nargs="?",
                    default=os.path.join(HERE, "data", "swf-manifest.tsv"))
    ap.add_argument("--expected-items", type=int, default=0)
    ap.add_argument("--expected-segments", type=int, default=0)
    args = ap.parse_args()

    tables = load_tables(args.scenes_tsv, args.manifest_tsv)
    items = []
    for dirpath, _, files in os.walk(args.export_root):
        if "item.json" in files:
            items.append(dirpath)
    items.sort()

    n_err = n_warn = 0
    segs = frames = 0
    disk = 0
    for d in items:
        errors, warns, st = check_item(d, tables)
        segs += st["segments"]
        frames += st["frames"]
        disk += item_dir_size(d)
        if errors:
            n_err += 1
            print(f"ERROR {os.path.relpath(d, args.export_root)}")
            for e in errors:
                print(f"   - {e}")
        for w in warns:
            n_warn += 1
            print(f"WARN {os.path.relpath(d, args.export_root)}: {w}")

    print(f"\nitems={len(items)} segments={segs} frames={frames} "
          f"disk={disk / 1e9:.2f} GB")
    print(f"errors_items={n_err} warns={n_warn}")
    if args.expected_items and len(items) != args.expected_items:
        print(f"MISMATCH: items {len(items)} != expected "
              f"{args.expected_items}")
        n_err += 1
    if args.expected_segments and segs != args.expected_segments:
        print(f"MISMATCH: segments {segs} != expected "
              f"{args.expected_segments}")
        n_err += 1
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()

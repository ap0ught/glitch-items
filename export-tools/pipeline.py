#!/usr/bin/env python3
"""
pipeline.py - Glitch item export pipeline (segment-aware).

For each item SWF:
  1. read its scene/label table + bg color (from scenes.tsv, pre-built)
  2. compute named segments: merge all scene starts and label starts into
     timeline windows (labels win ties - they are the finer, descriptive
     names; the game's engine plays exactly these windows)
  3. one Ruffle exporter run per item: --frames all --scale S
  4. split frames into per-segment dirs
  5. bgkey (transparent background) every frame with the item's bg color
  6. sheetpack each segment -> sheet.png + sheet.json
  7. write item.json (engine-ready manifest for the item)

Usage:
  pipeline.py <export_root> <scale> [--keep-raw] <swf_rel_path>...
  (swf paths relative to the glitch-items repo root, see GLITCH_ITEMS_ROOT)
"""
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
# repo root = the directory containing export-tools/
ROOT = os.environ.get("GLITCH_ITEMS_ROOT") or os.path.dirname(HERE)
EXPORTER = os.environ.get("RUFFLE_EXPORTER") \
    or "/tmp/opencode/ruffle/target/release/exporter"
PY = os.environ.get("PIPELINE_PYTHON") or sys.executable
BGKEY = [PY, os.path.join(HERE, "bgkey.py")]
SHEETPACK = [PY, os.path.join(HERE, "sheetpack.py")]
SCENES_TSV = os.environ.get("SCENES_TSV") or os.path.join(HERE, "data", "scenes.tsv")
MANIFEST_TSV = os.environ.get("MANIFEST_TSV") \
    or os.path.join(HERE, "data", "swf-manifest.tsv")

KEEP_RAW = "--keep-raw" in sys.argv


def norm(p):
    return p[2:] if p.startswith("./") else p


def load_tables():
    seg = {}
    for line in open(SCENES_TSV).read().splitlines()[1:]:
        rel, frames, bg, scenes, labels = line.split("\t")
        seg[norm(rel)] = (int(frames) if frames else 0,
                          bg or "ff/ff/ff", scenes, labels)
    meta = {}
    for line in open(MANIFEST_TSV).read().splitlines():
        p = line.split("\t")
        if len(p) == 5:
            meta[norm(p[0])] = (int(float(p[1])), int(float(p[2])),
                                float(p[3]), int(float(p[4])))
    return seg, meta


def compute_segments(scenes, labels, total):
    """Merge scene + label boundaries into named timeline windows."""
    scene_at = {}
    for e in filter(None, scenes.split("|")):
        fr, name = e.split(":", 1)
        scene_at.setdefault(int(fr), name)
    label_at = {}
    for e in filter(None, labels.split("|")):
        fr, name = e.split(":", 1)
        label_at.setdefault(int(fr), name)
    bounds = sorted({0, total} | set(scene_at) | set(label_at))
    segs = []
    for i in range(len(bounds) - 1):
        b0, b1 = bounds[i], bounds[i + 1]
        if b1 <= b0:
            continue
        name = label_at.get(b0) or scene_at.get(b0)
        if not name:
            name = "start" if b0 == 0 else f"part{i}"
        segs.append((re.sub(r"[^A-Za-z0-9_]", "_", name), b0, b1 - b0))
    return segs


def key_frame(args):
    raw, keyed, bg = args
    subprocess.run(BGKEY + [raw, keyed, "--bg", bg],
                   check=False, capture_output=True)


def process_item(rel, segmeta, meta, export_root, scale):
    frames, bg_hex, scenes, labels = segmeta
    w, h, fps, nman = meta[rel]
    if not frames:
        frames = nman
    bg = ",".join(str(int(x, 16)) for x in bg_hex.split("/"))
    segments = compute_segments(scenes, labels, frames)

    swf = os.path.join(ROOT, rel)
    # mirror the repo path (minus .swf): handles nested sub-categories
    item_dir = os.path.join(export_root, os.path.splitext(rel)[0])
    work = os.path.join(item_dir, ".work")
    raw_dir = os.path.join(work, "raw")
    shutil.rmtree(item_dir, ignore_errors=True)
    os.makedirs(raw_dir, exist_ok=True)

    r = subprocess.run(
        [EXPORTER, "-s", "-f", "all", "--scale", str(scale), swf, raw_dir],
        capture_output=True, text=True)
    if r.returncode != 0 or not os.listdir(raw_dir):
        print(f"FAIL_EXPORT {rel}: {r.stderr.strip()[:200]}")
        shutil.rmtree(work, ignore_errors=True)
        return False

    raw_files = sorted(
        (f for f in os.listdir(raw_dir) if f.endswith(".png")),
        key=lambda n: int(re.match(r"\D*(\d+)", n).group(1)))
    nraw = len(raw_files)
    if nraw != frames:
        print(f"WARN_FRAMES {rel}: manifest={frames} captured={nraw}")

    # split into per-segment dirs (renumbered)
    seg_dirs = []
    for sname, start, n in segments:
        d = os.path.join(work, "segs", sname)
        os.makedirs(d, exist_ok=True)
        seg_dirs.append((sname, start, d))
        for k in range(start, min(start + n, nraw)):
            shutil.copy(os.path.join(raw_dir, raw_files[k]),
                        os.path.join(d, f"{k - start:03d}.png"))

    # key all frames in parallel
    jobs = []
    for sname, start, d in seg_dirs:
        for f in os.listdir(d):
            if f.endswith(".png"):
                jobs.append((os.path.join(d, f), os.path.join(d, f + ".t"),
                             bg))
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(key_frame, jobs))
    fails = 0
    for src, dst, bg in jobs:
        if not os.path.exists(dst):
            r2 = subprocess.run(BGKEY + [src, dst, "--bg", bg],
                                capture_output=True, text=True)
            fails += 1
            # skip the frame (kept under .work) instead of shipping it raw
            os.rename(src, src + ".noby")
            if fails == 1:
                print(f"KEYFAIL {src}: {r2.stderr.strip()[-300:]}")
        else:
            os.replace(dst, src)

    # sheets + item.json
    out_segs = []
    for sname, start, d in seg_dirs:
        os.makedirs(os.path.join(item_dir, sname, "frames"), exist_ok=True)
        for f in os.listdir(d):
            if f.endswith(".png"):
                shutil.move(os.path.join(d, f),
                            os.path.join(item_dir, sname, "frames", f))
        subprocess.run(SHEETPACK + [os.path.join(item_dir, sname, "frames"),
                                    os.path.join(item_dir, sname)],
                       capture_output=True, text=True)
        sj = json.load(open(os.path.join(item_dir, sname, "sheet.json")))
        out_segs.append({
            "name": sname,
            "start_frame": start,
            "frames": len(os.listdir(os.path.join(item_dir, sname, "frames"))),
            "sheets": [f"{sname}/{s['file']}" for s in sj["sheets"]],
            "frames_dir": f"{sname}/frames/",
        })

    icon = next((s["name"] for s in out_segs
                 if s["name"].startswith("iconic") or s["name"] == "1"),
                out_segs[0]["name"])
    info = {
        "item": os.path.basename(item_dir),
        "category": rel.split("/")[0],
        "source": rel,
        "stage": [w, h],
        "fps": fps,
        "scale": scale,
        "bg_color": bg_hex,
        "total_frames": frames,
        "segment_count": len(out_segs),
        "icon_segment": icon,
        "segments": out_segs,
    }
    with open(os.path.join(item_dir, "item.json"), "w") as fh:
        json.dump(info, fh, indent=1)

    if KEEP_RAW:
        os.rename(raw_dir, os.path.join(item_dir, "raw"))
    else:
        shutil.rmtree(raw_dir, ignore_errors=True)
    shutil.rmtree(os.path.join(work, "segs"), ignore_errors=True)
    shutil.rmtree(work, ignore_errors=True)
    print(f"OK {rel} segs={len(out_segs)} frames={nraw} scale={scale}")
    return True


def main():
    args = [a for a in sys.argv[1:] if a != "--keep-raw"]
    export_root, scale = args[0], float(args[1])
    items = args[2:]
    segmeta, meta = load_tables()
    ok = fail = 0
    for rel in (norm(i) for i in items):
        if rel not in segmeta:
            print(f"MISS_TABLE {rel}")
            fail += 1
            continue
        if process_item(rel, segmeta[rel], meta, export_root, scale):
            ok += 1
        else:
            fail += 1
    print(f"PIPELINE DONE ok={ok} fail={fail}")


if __name__ == "__main__":
    main()

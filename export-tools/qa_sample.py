#!/usr/bin/env python3
"""
qa_sample.py - pick a targeted visual-QA sample from a finished export.

Picks ~30 items balancing:
  - the longest remaining animations (sheet/size risk)
  - items with the rarer non-white stage backgrounds (keying risk)
  - a seeded random spread across the rest (general coverage)
copies their item dirs into a staging tree and prints the paths so
qa_sheets.py can render a contact sheet over the copy.

Usage: qa_sample.py <export_root> <staging_dir> [--count N] [--tsv PATH]
"""
import argparse
import os
import random
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export_root")
    ap.add_argument("staging_dir")
    ap.add_argument("--count", type=int, default=30)
    ap.add_argument("--tsv", default=os.path.join(HERE, "data", "scenes.tsv"))
    args = ap.parse_args()
    export_root, staging = args.export_root, args.staging_dir
    scenes_tsv, n = args.tsv, args.count

    rows = []
    for line in open(scenes_tsv).read().splitlines()[1:]:
        rel, frames, bg, _, _ = line.split("\t")
        rel = rel[2:] if rel.startswith("./") else rel
        rows.append((rel, int(frames or 0), bg))

    rows.sort(key=lambda r: -r[1])
    longest = [r[0] for r in rows[:12]]

    by_bg = {}
    for rel, _, bg in rows:
        by_bg.setdefault(bg, []).append(rel)
    nonwhite = [bg for bg in sorted(by_bg, key=lambda b: -len(by_bg[b]))
                if bg != "ff/ff/ff"][:3]
    rng = random.Random(42)
    picked = list(dict.fromkeys(longest))
    for bg in nonwhite:
        for rel in rng.sample(by_bg[bg], min(3, len(by_bg[bg]))):
            if rel not in picked:
                picked.append(rel)
    while len(picked) < n:
        rel = rng.choice(rows)[0]
        if rel not in picked:
            picked.append(rel)
    picked = picked[:n]

    os.makedirs(staging, exist_ok=True)
    missing = []
    for rel in picked:
        src = os.path.join(export_root, os.path.splitext(rel)[0])
        dst = os.path.join(staging, os.path.splitext(rel)[0])
        if not os.path.isdir(src):
            missing.append(rel)
            continue
        shutil.copytree(src, dst,
                        ignore=shutil.ignore_patterns("raw"))
    print(f"staged {len(picked) - len(missing)}/{len(picked)} -> {staging}")
    if missing:
        print("missing from export:", *missing, sep="\n  ")
    for rel in picked:
        print(rel, end=" ")
    print()


if __name__ == "__main__":
    main()

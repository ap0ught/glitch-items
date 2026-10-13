#!/usr/bin/env python3
"""
fullrun.py - drive the complete 2,651-item export in parallel chunks.

Splits the item list into --workers chunks balanced by total frame count
(the dominant cost), then runs one pipeline.py process per chunk into the
same export root (chunks are item-disjoint, so no collisions).

Usage: fullrun.py <export_root> <scale> [--workers N] [--keep-raw]
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCENES = os.environ.get("SCENES_TSV") or os.path.join(HERE, "data", "scenes.tsv")
PIPELINE = os.path.join(HERE, "pipeline.py")
CHUNKS_DIR = os.environ.get("CHUNKS_DIR") \
    or os.path.join(tempfile.gettempdir(), "glitch-export-chunks")
PY = os.environ.get("PIPELINE_PYTHON") or sys.executable


def main():
    argv = sys.argv[1:]
    keep_raw = "--keep-raw" in argv
    if keep_raw:
        argv.remove("--keep-raw")
    workers = 4
    if "--workers" in argv:
        workers = int(argv[argv.index("--workers") + 1])
        del argv[argv.index("--workers"):argv.index("--workers") + 2]
    export_root, scale = argv[0], argv[1]

    items = []  # (rel, frames)
    for line in open(SCENES).read().splitlines()[1:]:
        rel, frames, bg, scenes, labels = line.split("\t")
        items.append((rel, int(frames or 0)))
    items.sort()

    # greedy balance by total frames
    chunks = [[] for _ in range(workers)]
    load = [0] * workers
    for rel, fr in sorted(items, key=lambda x: -x[1]):
        i = min(range(workers), key=lambda k: load[k])
        chunks[i].append(rel)
        load[i] += fr

    os.makedirs(CHUNKS_DIR, exist_ok=True)
    for i, ch in enumerate(chunks):
        with open(os.path.join(CHUNKS_DIR, f"chunk_{i}.txt"), "w") as fh:
            fh.write("\n".join(ch) + "\n")
        print(f"chunk_{i}: {len(ch)} items, {load[i]} frames")

    extra = ["--keep-raw"] if keep_raw else []
    procs = []
    for i, ch in enumerate(chunks):
        log = open(os.path.join(CHUNKS_DIR, f"chunk_{i}.log"), "w")
        p = subprocess.Popen(
            [PY, PIPELINE, export_root, scale] + extra + ch,
            stdout=log, stderr=subprocess.STDOUT)
        procs.append((i, p, len(ch), load[i]))

    print("running", len(procs), "pipelines...")
    ok_items = 0
    for i, p, n, fr in procs:
        rc = p.wait()
        print(f"chunk_{i} done rc={rc} items={n} frames={fr}")
        ok_items += sum(1 for ln in open(
            os.path.join(CHUNKS_DIR, f"chunk_{i}.log"))
            if ln.startswith("OK "))
    print(f"FULLRUN COMPLETE ok_items={ok_items}/{len(items)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
scenes.py - extract scene + frame-label table and stage background color
from Glitch item SWFs (batch, parallel).

Tag 86 (0x56, "SceneDescription") layout (verified byte-exact on this set):

    [SceneCount : U8]
    [ (VL frame, null-terminated name) x SceneCount ]
    [LabelCount : U8]
    [ (VL frame, null-terminated name) x LabelCount ]

VL frame = 7 bits/byte, little-endian groups, MSB = continuation.

Also grabs Tag 9 (SetBackgroundColor) "RR/GG/BB" for the keyer.

Usage: scenes.py <out.tsv>   (walks CWD for *.swf, CWD = repo root)
TSV: swf \t frames \t bg \t scenes \t labels
"""
import concurrent.futures as cf
import os
import re
import shutil
import subprocess
import sys

SWFDUMP = os.environ.get("SWFDUMP") or shutil.which("swfdump") \
    or "/tmp/opencode/prefix/bin/swfdump"
TAG_RE = re.compile(rb"^\[056\]\s+\d+\s+SCENEDESCRIPTION")
HEX_RE = re.compile(rb"[0-9a-f]{2}")
BG_RE = re.compile(rb"SETBACKGROUNDCOLOR \(([0-9a-f]{2})/([0-9a-f]{2})/([0-9a-f]{2})\)")


def read_vl(b, pos):
    v = 0
    shift = 0
    while True:
        byte = b[pos]
        pos += 1
        v |= (byte & 0x7F) << shift
        if not byte & 0x80:
            break
        shift += 7
    return v, pos


def parse(b):
    if not b:
        return [], []
    pos = 0
    sc = b[pos]
    pos += 1
    scenes = []
    for _ in range(sc):
        fr, pos = read_vl(b, pos)
        e = b.index(0, pos)
        scenes.append((fr, b[pos:e].decode("latin1")))
        pos = e + 1
    lc = b[pos]
    pos += 1
    labels = []
    for _ in range(lc):
        fr, pos = read_vl(b, pos)
        e = b.index(0, pos)
        labels.append((fr, b[pos:e].decode("latin1")))
        pos = e + 1
    if pos != len(b):
        raise ValueError(f"parse consumed {pos}/{len(b)}")
    return scenes, labels


def fmt(entries):
    return "|".join(f"{fr}:{name}" for fr, name in entries)


def process(path):
    rel = os.path.relpath(path)
    try:
        out = subprocess.run(
            [SWFDUMP, "-d", path], capture_output=True, timeout=120
        ).stdout
        frames = ""
        m = re.search(rb"\[045\].*?Frame count: (\d+)", out)
        if not m:
            m = re.search(rb"Frame count: (\d+)", out)
        if m:
            frames = m.group(1).decode()
        bg = ""
        m = BG_RE.search(out)
        if m:
            bg = "/".join(g.decode() for g in m.groups())
        data = bytearray()
        in_tag = False
        for ln in out.split(b"\n"):
            if TAG_RE.match(ln):
                in_tag = True
                continue
            if in_tag:
                if b"-=>" not in ln:
                    break
                for t in ln.split()[1:]:
                    if HEX_RE.fullmatch(t):
                        data.append(int(t, 16))
                    else:
                        break
        if data:
            scenes, labels = parse(bytes(data))
        else:
            scenes, labels = [], []
        return f"{rel}\t{frames}\t{bg}\t{fmt(scenes)}\t{fmt(labels)}"
    except Exception as e:
        return f"{rel}\t\t\tERROR:{type(e).__name__}:{e}\t"


def main():
    out_path = sys.argv[1]
    files = []
    for root, _, fs in os.walk("."):
        for f in fs:
            if f.endswith(".swf"):
                files.append(os.path.join(root, f))
    files.sort()
    with open(out_path, "w") as out:
        out.write("swf\tframes\tbg\tscenes\tlabels\n")
        with cf.ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
            for row in ex.map(process, files, chunksize=16):
                out.write(row + "\n")
    print(f"wrote {out_path} ({len(files)} rows)")


if __name__ == "__main__":
    main()

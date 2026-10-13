#!/usr/bin/env python3
"""
swfscenes.py - extract scene table from SWF files using swfdump -d as the parser.

Usage: swfscenes.py <file1.swf> [file2.swf ...]
Output (tab-separated): path \t frame:frame ... one scene per token, plus 'total'
"""
import subprocess, sys, re, os

SWFDUMP = "/tmp/opencode/prefix/bin/swfdump"

def get_scenes(path):
    r = subprocess.run([SWFDUMP, "-d", path], capture_output=True)
    out = r.stdout
    # swfdump prints "[hex_tag] length NAME" then hex lines "-=> XX XX ... ascii"
    lines = out.split(b"\n")
    scenes = []
    i = 0
    in_scene = False
    data = bytearray()
    while i < len(lines):
        ln = lines[i]
        m = re.match(rb"^\[056\]\s+(\d+)\s+SCENEDESCRIPTION", ln)
        if m:
            in_scene = True
            data = bytearray()
            i += 1
            continue
        if in_scene:
            m2 = re.match(rb"^\s*-=>\s+((?:[0-9a-f]{2} )+)\s+\S", ln)
            if m2:
                data += bytes.fromhex(m2.group(1).decode().replace(" ", ""))
                i += 1
                continue
            else:
                in_scene = False
                # parse data: [count][ (frame:1, name:CSTRING) x count ]
                try:
                    count = data[0]
                    pos = 1
                    for _ in range(count):
                        if pos >= len(data): break
                        frame = data[pos]; pos += 1
                        nul = data.index(0, pos)
                        name = data[pos:nul].decode("latin1").replace("\t", "_")
                        scenes.append(f"{name}@{frame}")
                        pos = nul + 1
                except Exception:
                    pass
        i += 1
    return scenes

def main():
    for path in sys.argv[1:]:
        try:
            scenes = get_scenes(path)
        except Exception as e:
            scenes = ["ERROR:" + str(e)]
        print(f"{path}\t{' '.join(scenes) if scenes else '(no scenes)'}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Tests for bgkey.py - the per-item background keyer.

Synthetic RGBA frames run through the CLI (subprocess, sys.executable),
so the real entry point is what is under test:

  - white bg: border background keyed, sprite interior preserved,
    near-white AA ring keyed (it is border-connected)
  - enclosed same-colour: white fully inside the sprite is NOT keyed
    (border-connectivity, not colour matching)
  - non-white stage bg: keyed via --bg from the SWF's
    SetBackgroundColor tag (the fox's 8e/b2/98 green)
  - all-background frame -> 100% transparent
"""
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BGKEY = os.path.join(HERE, "..", "bgkey.py")

FOX_BG = "142,178,152"   # 8e/b2/98, npc_fox's SetBackgroundColor


def run_bgkey(d, name, out, *extra):
    r = subprocess.run(
        [sys.executable, BGKEY, os.path.join(d, name), out, *extra],
        capture_output=True, text=True)
    assert r.returncode == 0, f"bgkey failed: {r.stderr}"
    return out


def save(d, name, arr):
    Image.fromarray(np.asarray(arr, dtype=np.uint8), "RGBA").save(
        os.path.join(d, name))


def alpha_at(png, x, y):
    return Image.open(png).getpixel((x, y))[3]


def rgb_at(png, x, y):
    return Image.open(png).getpixel((x, y))[:3]


def test_white_bg_keys_border_not_interior():
    with tempfile.TemporaryDirectory() as tmp:
        a = np.full((64, 64, 4), (255, 255, 255, 255))
        a[20:40, 20:40] = (0, 0, 0, 255)          # black square
        a[19, 19:41] = (250, 250, 250, 255)       # near-white AA ring
        a[40, 19:41] = (250, 250, 250, 255)
        a[19:41, 19] = (250, 250, 250, 255)
        a[19:41, 40] = (250, 250, 250, 255)
        save(tmp, "in.png", a)
        out = run_bgkey(tmp, "in.png", os.path.join(tmp, "out.png"))

        assert alpha_at(out, 0, 0) == 0           # bg corner keyed
        assert alpha_at(out, 63, 63) == 0
        assert alpha_at(out, 30, 30) == 255       # sprite intact
        assert rgb_at(out, 30, 30) == (0, 0, 0)
        assert alpha_at(out, 30, 19) == 0         # AA ring keyed (it
                                                  # touches the border)


def test_enclosed_white_survives():
    with tempfile.TemporaryDirectory() as tmp:
        a = np.full((64, 64, 4), (255, 255, 255, 255))
        a[10:50, 10:50] = (0, 0, 0, 255)          # black square
        a[25:35, 25:35] = (255, 255, 255, 255)    # white enclosed in it
        save(tmp, "in.png", a)
        out = run_bgkey(tmp, "in.png", os.path.join(tmp, "out.png"))

        assert alpha_at(out, 0, 0) == 0           # outer white keyed
        assert alpha_at(out, 15, 15) == 255       # black square kept
        assert alpha_at(out, 30, 30) == 255       # enclosed white kept
        assert rgb_at(out, 30, 30) == (255, 255, 255)


def test_green_bg_via_flag():
    with tempfile.TemporaryDirectory() as tmp:
        a = np.full((64, 64, 4), (142, 178, 152, 255))   # fox's stage
        a[20:40, 20:40] = (0, 0, 0, 255)
        save(tmp, "in.png", a)
        out = run_bgkey(tmp, "in.png", os.path.join(tmp, "out.png"),
                        "--bg", FOX_BG)

        assert alpha_at(out, 0, 0) == 0
        assert alpha_at(out, 63, 63) == 0
        assert alpha_at(out, 30, 30) == 255
        assert rgb_at(out, 30, 30) == (0, 0, 0)


def test_all_bg_frame_becomes_empty():
    with tempfile.TemporaryDirectory() as tmp:
        a = np.full((32, 32, 4), (142, 178, 152, 255))
        save(tmp, "in.png", a)
        out = run_bgkey(tmp, "in.png", os.path.join(tmp, "out.png"),
                        "--bg", FOX_BG)

        arr = np.array(Image.open(out))
        assert not (arr[..., 3] > 0).any()


def main():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok {fn.__name__}")
    print(f"{len(fns)} tests passed")


if __name__ == "__main__":
    main()

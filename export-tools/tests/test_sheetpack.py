#!/usr/bin/env python3
"""
Tests for sheetpack.py - the sprite-sheet grid packer.

All frames are synthetic RGBA PNGs (no repo assets needed). The module
is driven by calling its main() with sys.argv patched; MAX_DIM/MAX_MP
are monkeypatched to exercise the width-wrap and the multi-sheet split
without rendering thousands of frames.

Covered:
  - single-sheet layout + cell/offset arithmetic (incl. centered,
    mixed-content-size frames)
  - transparent frames -> 1x1 placeholder
  - width wrap at the 10000 px cap (the watering-can case: 30 frames
    of 334 px content -> 29 cols x 2 rows)
  - MP split: oversized segments become sheet_0, sheet_1, ... with
    contiguous, exhaustive frame ranges
"""
import json
import os
import sys
import tempfile
from math import ceil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import sheetpack  # noqa: E402
from PIL import Image  # noqa: E402


def make_frame(path, size, content):
    """content: (w, h, x, y) of an opaque red square in a `size`-px canvas."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    w, h, x, y = content
    im.paste((255, 0, 0, 255), (x, y, x + w, y + h))
    im.save(path)


def make_frames(tmp, n, size, content=None):
    d = os.path.join(tmp, "frames")
    os.makedirs(d)
    for i in range(n):
        make_frame(os.path.join(d, f"{i}.png"), size,
                   content if content else (size - 8, size - 8, 4, 4))
    return d


def pack(frames_dir, out_dir, **overrides):
    saved = {k: getattr(sheetpack, k) for k in overrides}
    for k, v in overrides.items():
        setattr(sheetpack, k, v)
    try:
        old = sys.argv
        sys.argv = ["sheetpack.py", frames_dir, out_dir]
        try:
            sheetpack.main()
        finally:
            sys.argv = old
    finally:
        for k, v in saved.items():
            setattr(sheetpack, k, v)


def load(out_dir):
    with open(os.path.join(out_dir, "sheet.json")) as fh:
        return json.load(fh)


def test_single_sheet_offsets():
    with tempfile.TemporaryDirectory() as tmp:
        frames = make_frames(tmp, 5, 40, (32, 32, 4, 4))
        out = os.path.join(tmp, "out")
        pack(frames, out)

        meta = load(out)
        assert meta["count"] == 5
        assert meta["cell_width"] == 36 and meta["cell_height"] == 36
        assert len(meta["sheets"]) == 1
        s = meta["sheets"][0]
        assert s["file"] == "sheet.png"
        assert s["cols"] == 5 and s["rows"] == 1

        im = Image.open(os.path.join(out, "sheet.png"))
        assert im.size == (180, 36)
        # frame 0: content (32x32) centered in a 36px cell -> offset (2,2)
        f0 = s["frames"][0]
        assert f0["offset"] == [2, 2] and f0["size"] == [32, 32]
        assert f0["src_crop"] == [4, 4, 36, 36]
        px = im.getpixel((2, 2))
        assert px[0] == 255 and px[3] == 255, f"frame corner not red: {px}"
        # cell padding must stay transparent
        assert im.getpixel((0, 0))[3] == 0


def test_mixed_content_sizes_centered():
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "frames")
        os.makedirs(d)
        make_frame(os.path.join(d, "0.png"), 40, (32, 32, 4, 4))
        make_frame(os.path.join(d, "1.png"), 40, (16, 16, 12, 12))
        out = os.path.join(tmp, "out")
        pack(d, out)

        meta = load(out)
        s = meta["sheets"][0]
        assert s["frames"][0]["offset"] == [2, 2]      # (36-32)//2
        assert s["frames"][1]["offset"] == [46, 10]    # cell 1, (36-16)//2
        im = Image.open(os.path.join(out, "sheet.png"))
        assert im.getpixel((2, 2))[3] == 255
        assert im.getpixel((46, 10))[3] == 255         # second cell content
        assert im.getpixel((46 + 16, 10))[3] == 0      # past content


def test_fully_transparent_frame_placeholder():
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "frames")
        os.makedirs(d)
        Image.new("RGBA", (40, 40), (0, 0, 0, 0)).save(os.path.join(d, "0.png"))
        make_frame(os.path.join(d, "1.png"), 40, (32, 32, 4, 4))
        out = os.path.join(tmp, "out")
        pack(d, out)

        s = load(out)["sheets"][0]
        assert s["frames"][0]["size"] == [1, 1]
        assert s["frames"][0]["src_crop"] == [0, 0, 0, 0]
        assert s["frames"][1]["size"] == [32, 32]


def test_width_wrap_at_10000():
    # 30 frames of 334px content -> 338px cells (+4 pad); 338*30 > 10000,
    # so the sheet wraps to 29 cols x 2 rows (the watering-can behaviour)
    with tempfile.TemporaryDirectory() as tmp:
        frames = make_frames(tmp, 30, 344, (334, 334, 5, 5))
        out = os.path.join(tmp, "out")
        pack(frames, out)

        meta = load(out)
        assert len(meta["sheets"]) == 1
        s = meta["sheets"][0]
        assert s["file"] == "sheet.png"
        assert s["cols"] == 29 and s["rows"] == 2
        im = Image.open(os.path.join(out, "sheet.png"))
        assert im.size == (29 * 338, 2 * 338)
        assert im.width < 10000


def test_mp_split_multiple_sheets():
    # force a split with a tiny budget: 68px cells, 7 cols,
    # 50k px per sheet -> 7 frames per part -> 2 sheets for 12 frames
    with tempfile.TemporaryDirectory() as tmp:
        frames = make_frames(tmp, 12, 72, (64, 64, 4, 4))
        out = os.path.join(tmp, "out")
        pack(frames, out, MAX_MP=50_000, MAX_DIM=500)

        meta = load(out)
        assert meta["count"] == 12
        assert len(meta["sheets"]) == 2
        ranges = [s["frame_range"] for s in meta["sheets"]]
        assert ranges == [[0, 6], [7, 11]]
        for s in meta["sheets"]:
            assert os.path.exists(os.path.join(out, s["file"]))
        assert os.path.exists(os.path.join(out, "sheet_0.png"))
        assert os.path.exists(os.path.join(out, "sheet_1.png"))
        assert not os.path.exists(os.path.join(out, "sheet.png"))
        # every frame index appears exactly once across the sheets
        idxs = [f["frame"] for s in meta["sheets"] for f in s["frames"]]
        assert sorted(idxs) == list(range(12))
        # and every offset points inside its own sheet
        for s in meta["sheets"]:
            im = Image.open(os.path.join(out, s["file"]))
            for f in s["frames"]:
                ox, oy = f["offset"]
                assert ox + f["size"][0] <= im.width
                assert oy + f["size"][1] <= im.height


def test_split_does_not_break_grid_continuity():
    # with 20 frames / 5 cols and a budget forcing 1 row per part,
    # part boundaries must fall on full rows
    with tempfile.TemporaryDirectory() as tmp:
        frames = make_frames(tmp, 20, 72, (64, 64, 4, 4))
        out = os.path.join(tmp, "out")
        pack(frames, out, MAX_MP=50_000, MAX_DIM=300)
        meta = load(out)
        cols = meta["cols"]
        assert cols == 4                     # 300 // 68
        total = sum(len(s["frames"]) for s in meta["sheets"])
        assert total == 20
        for s in meta["sheets"]:
            # each part except the last is a whole number of rows
            assert len(s["frames"]) % cols == 0 or s is meta["sheets"][-1]
            assert s["rows"] == ceil(len(s["frames"]) / cols)


def main():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok {fn.__name__}")
    print(f"{len(fns)} tests passed")


if __name__ == "__main__":
    main()

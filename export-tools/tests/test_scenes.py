#!/usr/bin/env python3
"""
Tests for scenes.py - the SWF tag 86 (SceneDescription) parser.

Fixtures are the actual tag-86 bodies of three items from this repo,
dumped with swfdump -d (the trusted byte source on this collection) and
verified to parse to exactly 100% consumption:

  food/apple/apple.swf               22 B   5 scenes, 0 labels
  inhabitants/fox/npc_fox.swf        84 B   1 scene,  10 labels (VL frames)
  tools/woodworker/woodworker.swf   254 B   1 scene,  22 labels (VL frames)

Run: python3 tests/test_scenes.py   (or under pytest)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scenes import parse, read_vl  # noqa: E402

APPLE = bytes.fromhex(
    "05 00 69 63 6f 6e 69 63 00 01 31 00 02 32 00 03 33 00 04 34 00 00".replace(" ", ""))
FOX = bytes.fromhex(
    "01 00 53 63 65 6e 65 20 31 00 0a 00 73 74 69 6c 6c 00 01 72 75 6e 00 "
    "0d 65 61 74 53 74 61 72 74 00 17 65 61 74 00 2b 65 61 74 45 6e 64 00 "
    "3f 70 61 75 73 65 00 77 6a 75 6d 70 00 93 01 74 61 75 6e 74 00 "
    "bb 01 62 72 75 73 68 65 64 00 bd 01 77 61 6c 6b 00".replace(" ", ""))
WOODWORKER = bytes.fromhex(
    "01 00 53 63 65 6e 65 20 31 00 16 00 69 63 6f 6e 69 63 00 01 61 73 73 "
    "65 6d 62 6c 65 64 00 02 73 74 61 6e 64 00 03 66 75 73 65 72 31 00 "
    "1a 66 75 73 65 72 31 48 6f 6c 64 00 1b 66 75 73 65 72 32 00 "
    "2f 66 75 73 65 72 32 48 6f 6c 64 00 30 63 68 61 73 69 73 31 00 "
    "47 63 68 61 73 69 73 31 48 6f 6c 64 00 48 63 68 61 73 69 73 32 00 "
    "5f 63 68 61 73 69 73 32 48 6f 6c 64 00 60 65 6e 67 69 6e 65 31 00 "
    "70 65 6e 67 69 6e 65 31 48 6f 6c 64 00 71 65 6e 67 69 6e 65 32 00 "
    "8f 01 6c 6f 61 64 4f 70 65 6e 00 99 01 6c 6f 61 64 4f 70 65 6e 48 "
    "6f 6c 64 00 9a 01 6c 6f 61 64 43 6c 6f 73 65 00 a4 01 61 63 74 69 "
    "76 65 00 cc 01 72 65 61 64 79 00 da 01 63 6f 6c 6c 65 63 74 4f 70 "
    "65 6e 00 e2 01 63 6f 6c 6c 65 63 74 4f 70 65 6e 48 6f 6c 64 00 "
    "e3 01 63 6f 6c 6c 65 63 74 43 6c 6f 73 65 00".replace(" ", ""))


def test_read_vl_single_byte():
    assert read_vl(b"\x00", 0) == (0, 1)
    assert read_vl(b"\x7f", 0) == (127, 1)
    assert read_vl(b"\x0a", 0) == (10, 1)


def test_read_vl_two_bytes_low_bits_first():
    # SWF variable-length ints pack 7 bits/byte, LOW bits in the first
    # byte. 0x93 0x01 = 19 | (1 << 7) = 147 (fox "taunt" frame).
    assert read_vl(b"\x93\x01", 0) == (147, 2)
    assert read_vl(b"\xbb\x01", 0) == (187, 2)   # fox "brushed"
    assert read_vl(b"\xbd\x01", 0) == (189, 2)   # fox "walk"
    assert read_vl(b"\x8f\x01", 0) == (143, 2)   # woodworker "loadOpen"
    assert read_vl(b"\xff\x01", 0) == (255, 2)


def test_read_vl_off_by_one_start():
    b = b"\x00\x00\x2a"
    v, pos = read_vl(b, 2)
    assert v == 42 and pos == 3


def test_parse_apple_scenes_only():
    scenes, labels = parse(APPLE)
    assert scenes == [(0, "iconic"), (1, "1"), (2, "2"), (3, "3"), (4, "4")]
    assert labels == []


def test_parse_fox_single_scene_with_labels():
    scenes, labels = parse(FOX)
    assert scenes == [(0, "Scene 1")]
    assert labels == [
        (0, "still"), (1, "run"), (13, "eatStart"), (23, "eat"),
        (43, "eatEnd"), (63, "pause"), (119, "jump"), (147, "taunt"),
        (187, "brushed"), (189, "walk"),
    ]


def test_parse_woodworker_22_labels():
    scenes, labels = parse(WOODWORKER)
    assert scenes == [(0, "Scene 1")]
    assert [n for _, n in labels] == [
        "iconic", "assembled", "stand", "fuser1", "fuser1Hold",
        "fuser2", "fuser2Hold", "chasis1", "chasis1Hold", "chasis2",
        "chasis2Hold", "engine1", "engine1Hold", "engine2", "loadOpen",
        "loadOpenHold", "loadClose", "active", "ready", "collectOpen",
        "collectOpenHold", "collectClose",
    ]
    assert [f for f, _ in labels] == [
        0, 1, 2, 3, 26, 27, 47, 48, 71, 72, 95, 96, 112, 113, 143, 153,
        154, 164, 204, 218, 226, 227,
    ]
    # woodworker's total timeline is 237 frames; last label at 227 leaves
    # a 10-frame tail, which the pipeline turns into the "collectClose"
    # window's remainder.
    assert max(f for f, _ in labels) < 237


def test_parse_full_consumption():
    # a correct parse must consume every byte of the tag body
    for body in (APPLE, FOX, WOODWORKER):
        pos = 0
        sc = body[pos]; pos += 1
        for _ in range(sc):
            _, pos = read_vl(body, pos)
            pos = body.index(0, pos) + 1
        lc = body[pos]; pos += 1
        for _ in range(lc):
            _, pos = read_vl(body, pos)
            pos = body.index(0, pos) + 1
        assert pos == len(body), f"leftover bytes in {len(body)}-B fixture"


def test_parse_empty():
    assert parse(b"") == ([], [])


def main():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok {fn.__name__}")
    print(f"{len(fns)} tests passed")


if __name__ == "__main__":
    main()

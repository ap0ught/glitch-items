#!/usr/bin/env python3
"""
Tests for pipeline.compute_segments - the segment-merge rule.

All scene/label inputs below are copied verbatim from data/scenes.tsv
(extracted from the repo's own SWFs by scenes.py), so these tests pin
the pipeline's behaviour on items the real pipeline has exported:

  apple          5 scenes, 0 labels          -> 5 one-frame segments
  plank          6 scenes + 1 label          -> label wins at frame 5
  frying_pan     5 scenes + 3 labels         -> 7 segments (labels cut
                                               the tool_animation scene)
  emotional_bear 16 scenes + 3 redundant
                 labels                      -> 16 segments
  fox            1 scene + 10 labels         -> 10 segments
  flamingo       1 scene + 16 labels         -> 16 segments
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pipeline import compute_segments  # noqa: E402


def check_tiling(segs, total, what=""):
    """Segments must tile [0, total) with no gaps and no overlaps."""
    assert segs, f"no segments for {what}"
    pos = 0
    for name, start, n in segs:
        assert start == pos, (
            f"{what}: segment {name!r} starts at {start}, expected {pos}")
        assert n > 0, f"{what}: empty segment {name!r}"
        pos += n
    assert pos == total, f"{what}: covers {pos}/{total}"


def test_apple_scenes_only():
    segs = compute_segments("0:iconic|1:1|2:2|3:3|4:4", "", 5)
    assert [s[0] for s in segs] == ["iconic", "1", "2", "3", "4"]
    assert all(s[2] == 1 for s in segs)
    check_tiling(segs, 5, "apple")


def test_plank_label_wins_at_scene_frame():
    # frame 5 has BOTH a scene (emote_animation) and a label (splank):
    # the label is the finer, descriptive name and wins
    segs = compute_segments(
        "0:iconic|1:1|2:2|3:3|4:4|5:emote_animation", "5:splank", 95)
    assert [s[0] for s in segs] == ["iconic", "1", "2", "3", "4", "splank"]
    assert segs[5][1] == 5 and segs[5][2] == 90
    check_tiling(segs, 95, "plank")


def test_frying_pan_hybrid():
    segs = compute_segments(
        "0:1|1:tool_animation|91:iconic|92:broken_iconic|93:broken",
        "1:transition_in|15:animation|79:transition_out", 94)
    assert [(s[0], s[1], s[2]) for s in segs] == [
        ("1", 0, 1),
        ("transition_in", 1, 14),
        ("animation", 15, 64),
        ("transition_out", 79, 12),
        ("iconic", 91, 1),
        ("broken_iconic", 92, 1),
        ("broken", 93, 1),
    ]
    check_tiling(segs, 94, "frying_pan")
    # these are exactly the states glitch-GameServerJS tool_base
    # cycles through - the export must stay aligned with the server


def test_emotional_bear_labels_redundant():
    # labels at 9/100/322 duplicate scene names at the same frames;
    # boundary set is unchanged -> 16 segments
    segs = compute_segments(
        "0:iconic_plain|1:iconic|2:iconic_moon|3:iconic_kiss|"
        "4:iconic_moon_kiss|5:1_plain|6:1_moon|7:1_kiss|8:1_moon_kiss|"
        "9:hug|100:moon|245:high_5|322:kiss|391:small_hug|431:small_kiss|"
        "478:rooked_halo",
        "9:hug|100:moon|322:kiss", 508)
    assert [s[0] for s in segs] == [
        "iconic_plain", "iconic", "iconic_moon", "iconic_kiss",
        "iconic_moon_kiss", "1_plain", "1_moon", "1_kiss", "1_moon_kiss",
        "hug", "moon", "high_5", "kiss", "small_hug", "small_kiss",
        "rooked_halo",
    ]
    check_tiling(segs, 508, "emotional_bear")


def test_fox_labels_drive_windows():
    segs = compute_segments(
        "0:Scene 1",
        "0:still|1:run|13:eatStart|23:eat|43:eatEnd|63:pause|119:jump|"
        "147:taunt|187:brushed|189:walk", 213)
    assert [s[0] for s in segs] == [
        "still", "run", "eatStart", "eat", "eatEnd", "pause", "jump",
        "taunt", "brushed", "walk"]
    assert [s[2] for s in segs] == [1, 12, 10, 20, 20, 56, 28, 40, 2, 24]
    check_tiling(segs, 213, "fox")


def test_flamingo_16_labels():
    segs = compute_segments(
        "0:Scene 1",
        "0:idle0|1:idle1|90:idle2|117:idle3|150:talkTall|239:turn|"
        "280:talkShort|369:takeOff|408:hover|420:hoverToFly|457:flying|"
        "469:flyToHover|506:idle4|523:hoverTalkTall|630:hoverTurn|"
        "690:hoverTalkShort", 790)
    assert len(segs) == 16
    assert segs[0] == ("idle0", 0, 1)
    assert segs[-1] == ("hoverTalkShort", 690, 100)
    check_tiling(segs, 790, "flamingo")


def test_no_scenes_no_labels_single_start():
    segs = compute_segments("", "", 7)
    assert segs == [("start", 0, 7)]


def test_name_sanitised():
    segs = compute_segments("0:my scene", "3:two words", 4)
    assert [s[0] for s in segs] == ["my_scene", "two_words"]
    check_tiling(segs, 4, "sanitise")
    # every char outside [A-Za-z0-9_] becomes an underscore (no trimming)
    segs = compute_segments("0:a!b", "", 2)
    assert segs[0][0] == "a_b"


def main():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok {fn.__name__}")
    print(f"{len(fns)} tests passed")


if __name__ == "__main__":
    main()

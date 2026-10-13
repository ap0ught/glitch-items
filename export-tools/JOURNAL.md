# Glitch items → sprite sheet export — run journal

Multi-session effort to export the CC0 "Glitch" (Tiny Speck 2011-12) Flash
assets as engine-ready sprite sheets. Repo: ap0ught/glitch-items fork of
abandonrules/glitch-items, shallow-cloned at /tmp/opencode/glitch-items
(5,370 files; 2,651 .swf + their .fla sources).

## Setup facts (verified, not to be re-derived)

- OS: CachyOS (Arch). No swftools/libart in pacman; no swf pip packages.
- **swftools (jdapena fork) built from source** at /tmp/opencode/swftools,
  installed to /tmp/opencode/prefix/bin (swfdump, swfextract, swfrender,
  png2swf, ...). Patches applied (see "Dead ends" for why):
  - lib/art: libart is vendored in-tree — no system libart needed.
  - flex 2.6.4 vs old yyunput prototypes in lib/action/*.flex.
  - K&R `()` prototypes + GCC16/C23 semantics → `CFLAGS="-std=gnu17 -fcommon"`.
  - pdf2swf force-disabled (needs xpdf/config.h); not needed.
  - gif2swf patched for modern libungif `int *Error` out-params.
  - bundled LAME: `INLINE` macro emptied, bare `inline` on
    bitpressure_strategy1/2 removed.
- **Ruffle exporter built** at /tmp/opencode/ruffle/target/release/exporter
  (cargo 1.97, 3 min build). A desktop Ruffle binary from Oct 7 sits at
  /tmp/opencode/ruffle-desktop (GUI only, no frame export — ignore).
- Python: /tmp/opencode/swfenv has pillow+numpy+scipy. System python3.14
  also has numpy 2.5.3.
- GPU: /dev/dri/renderD128 present, DISPLAY=:0. Exporter runs headless fine.
- **DISK TOPOLOGY: /tmp is tmpfs — 16 GB RAM, only ~6.4 GB free.**
  /home is /dev/sda2 with 88 GB free. Build/export work happens on /tmp;
  the final delivered package (tree + zip) must land on /home
  (session dir: /home/cmayfield/Documents/Default Project, currently empty).
  Full run without --keep-raw est. ~1.5-2 GB on tmpfs — OK, but do NOT
  keep raw/ dirs for all 2,651 items on /tmp (would eat ~3.5 GB).
- **Exporter CLI**: `exporter -s -f all --scale N <file.swf> <outdir>` →
  writes `0.png..N.png` (or zero-padded `000.png..` when count >= 100).
  `--skipframes F --frames N` selects a window. `-f all` captures whole
  main timeline. No per-scene flag — hence the split-after-capture design.

## The SWF structure (the important part)

Every item SWF (2,651) is a short main-timeline movie. Inventory built by
swfdump (see scripts below).

### Tag 86 (0x56, "SCENEDESCRIPTION") — universal in this set

Byte layout (verified byte-exact; swfdump is the trusted byte source):

```
[SceneCount : U8]
[(VL frame, null-terminated name) x SceneCount]
[LabelCount : U8]
[(VL frame, null-terminated name) x LabelCount]
```

VL frame = **7 bits per byte, little-endian groups, MSB = continuation**
(same scheme as SWF U30). Frame numbers >= 128 take 2 bytes
(e.g. 0x93 0x01 = 147). This bit me once — the decoder must accumulate
low-bits-first, NOT `(v & 0x7F) << 7 | next`.

Files carry a non-standard 8-byte preamble in the zlib payload that
hand-rolled tag walkers misalign on (FileAttributes/CRECT don't land where
expected); **use `swfdump -d` output as the byte source** — it parses clean.

### How the game addressed items (from glitch-client source)

Repo ap0ught/glitch-client, files read: ItemViewer.as, GodItemViewer.as,
ItemSSManager.as, MCUtil.as, ItemIconView.as (copies in /tmp/opencode/).

- Three asset archetypes: scene-driven (default), timeline-animated
  (`mc.animations[]` + `mc.animatee`, played via `playAnimation(name)` —
  name = a **frame label**), and trant (`setState(config+seed)`).
- The engine pre-rendered items to sprite sheets (ItemSSManager /
  SSFrameCollection): one frame-collection per animation/scene, addressed
  by tsid:config:animation.
- Canonical icon = scene/state **'iconic'** (fallback '1'); broken state =
  'broken_iconic'.
- Scenes and labels both partition the main timeline; the labels on
  tool/NPC SWFs are exactly the animation names the AS code plays.

**Consequence — export rule (implemented in pipeline.py):** merge all
scene-start and label-start frame numbers into timeline windows
`[b_i, b_{i+1})`; name each window by its label if one sits at b_i, else
its scene, else `start`/`part{i}`. One exporter run per item
(`-f all`), then split the captured frames into per-segment dirs.

### Collection stats (from scenes.tsv, 2026-10-13)

- 2,651 SWFs, 22,729 total frames. Max: npc_rube 1001, npc_flamingo 790,
  piglet 700, emotional_bear 508.
- 1,847 items are 1-frame static; 94 have labels; 2,557 have only scenes.
- 93% of all scenes/labels are 1 frame (icons); only 25 segments are 100+.
- **Total segments = 4,790** → that's the final sheet count for a full run.
- 41 distinct stage bg colors; ff/ff/ff ×2,183; next: 66/99/99 ×287,
  33/33/33 ×34, 66/66/66 ×30 ... 468 items are NOT white — the keyer must
  use each file's SetBackgroundColor (tag 9), not assume white.
- Hybrid examples (verified by eye): frying_pan = scene '1'@0 covering
  0-90 + labels transition_in@1/animation@15/transition_out@79 + 1-frame
  scenes iconic@91/broken_iconic@92/broken@93. Merged rule decomposes it
  perfectly. emotional_bear = 16 icon/emote scenes + 3 redundant labels.

## Working (current state)

| artifact | path | notes |
|---|---|---|
| swf metadata manifest | /tmp/opencode/swf-manifest.tsv | path, w, h, fps, frames (2,651) |
| scene/label/bg table | /tmp/opencode/scenes.tsv | path, frames, bg, scenes, labels |
| pipeline | /tmp/opencode/pipeline.py | v2 segment pipeline (scale 4 test running) |
| keyer | /tmp/opencode/bgkey.py | v3: per-color bg, border-flood, halo decontam |
| sheet packer | /tmp/opencode/sheetpack.py | grid wrap at 10,000 px, per-frame json |
| exporter | /tmp/opencode/ruffle/target/release/exporter | ruffle |
| test batch 1 (scale 2 & 4, flat) | /tmp/opencode/export/batch1{,_s4}/ | 12 items OK, superseded by v2 design |
| **test batch 2 (scale 4, segments)** | /tmp/opencode/export/batch2/ | RUNNING: 12 items incl fox/woodworker/flamingo/rube |

Output layout per item (v2): `<root>/<cat>/<item>/item.json` +
`<segname>/frames/*.png` (keyed) + `<segname>/sheet.png` +
`<segname>/sheet.json`. item.json carries stage, fps, scale, bg_color,
segment list (name/start_frame/frames/sheet), and icon_segment.

## Dead ends / bugs caught (do not retry)

- swftools from barichello/pacman: libart_lgpl removed from Arch; aborted.
- `pacman -S swftools` / `libart_lgpl`: package not found.
- pip swf tooling (miniflash, swf-tools, swf): no distribution.
- swfrender (built anyway): first frame only, no -f/-skip — useless for
  animation frames.
- Hand-rolled SWF tag walker in Python (swfpeek.py): CWS body starts with
  an 8-byte non-standard preamble; tag alignment is unreliable. Discard in
  favor of swfdump-based extraction (scenes.py).
- `--force-play` not needed: `-f all` stepped every timeline fine without
  it on all tested items.
- Pillow venv initially lacked pillow (pip abort on miniflash failed first)
  → batch FAIL_SHEET cascade; fixed with `pip install pillow numpy scipy`.
- np.asarray(PIL image) is read-only → `np.array(np.asarray(...))`.
- bgkey v3 numpy fancy-indexing bug: `out[idx, :3]` with idx=(N,2) sliced
  the WIDTH axis, not the channel axis → ValueError on every non-trivial
  halo. Fixed with `ri, ci = np.nonzero(halo)` split indexing.
- bgkey save-to-`.t`-suffix: Pillow can't infer format from a `.t`
  extension → always `save(path, "PNG")` explicitly.
- Pipeline output path: repo is NOT uniformly `cat/item/name.swf` —
  1,824/2,651 SWFs sit in nested sub-dirs (tools/tool_base/…, etc.).
  Output must mirror the full repo path minus `.swf`.
- `Image.paste(im, box)` does NOT use im's alpha — pass the mask
  (`c.paste(im, box, im)`) or keying "succeeds" but the backdrop test
  shows an opaque rectangle (false alarm on the first fox check).

## Verified working (2026-10-13, pipeline v2 smoke tests)

- bgkey v3 on white bg (apple) AND green bg 8e/b2/98 (fox): 4x zoom
  edge comparison shows clean fur edges, no green fringing
  (faint residue only between sparse tuft strands — acceptable).
- Rendered stage bg == SetBackgroundColor always holds (corners sampled).
- watering_can (33f, white): 4 segments — `1`@0, `tool_animation`@1 (30f),
  `broken_iconic`@31, `broken`@32; apple (5f): 5 one-frame scenes.
- sheetpack grid wrap: 30 frames @ 334px cell → 29 cols × 2 rows (the
  10000 px cap works); sheet.json carries per-frame offset/size/src_crop.
- item.json shape: stage/fps/scale/bg_color/total_frames/icon_segment/
  segments[{name,start_frame,frames,sheet,frames_dir}].

## Open questions

- [ ] Batch 2 QA: do green-bg items (fox etc.) key cleanly after the
      decontam pass? (fox_qa.png showed GREEN = raw pre-key frames; batch 2
      output will confirm.)
- [ ] rube (1001f, stage 88x138) single-segment sheet size: if content
      fills the stage, ~207 MP at 4x — OVER Pillow's 179 MP load limit.
      Batch 2 shows the real content size; if too big, add a ~150 MP
      split-cap to sheetpack (sheet_0/sheet_1/... + json list).
- [ ] Full run: 2,651 items / 4,790 sheets at scale 4 on /tmp (NO
      --keep-raw — disk), 4 parallel pipeline chunks via fullrun.py;
      then package (tree + zip) onto /home.

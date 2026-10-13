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

## 2026-10-13, session 5 — batch 2 v2, tests, repo commit

- **sheetpack gained a per-sheet pixel cap**: MAX_MP = 150e6 (under
  Pillow's 179 MP load limit). Segments that exceed it split into
  `sheet_0.png, sheet_1.png, ...`; `sheet.json` now carries a `sheets[]`
  list (file, cols, rows, frame_range, per-frame entries) and
  `item.json` records `"sheets": [...]` per segment. Rube (1001 frames,
  the biggest item) lands at 2 sheets: [0..755] 28x27 grid + [756..1000]
  28x9 — both load fine.
- **Batch 2 re-render (scale 4, --keep-raw): 12/12 OK**
  (batch2.log). Segments: apple 5, plank 6 (label `splank` wins over
  scene `emote_animation` at frame 5), woodworker 22, frying_pan 7
  (`1`/`transition_in`/`animation`/`transition_out`/`iconic`/
  `broken_iconic`/`broken` — exactly the server's tool_base states),
  emotional_bear 16, fox 10, yoga_frog 15, flamingo 16, rube 1,
  butterfly hair clip 1, door_key_9 1, yeti 1.
- **enrich.py: 12/12 batch-2 items matched server stems, all 12 got
  their official 40x40 icon.** QA contact sheet (batch2_qa.png) clean;
  fox_key_check.png: raw green 8e/b2/98 stage -> keyed frame matches the
  official icon, no green fringing (decontam + border-flood both work).
- **qa_sheets.py bug caught by the QA run itself**: `cell()` took
  `dirname()` of the item.json dir before resolving `<seg>/frames/`, so
  every lookup landed one level up -> FileNotFoundError on the first
  item. Fix: use `_dir` directly.
- **Test suite committed: 26 tests, all passing** (tests/run_all.sh,
  needs venv python for numpy/scipy):
  - test_scenes: byte-exact tag-86 fixtures (apple 22B / fox 84B /
    woodworker 254B captured from swfdump -d) + VL-integer cases.
  - test_segment_merge: real items pinned (frying-pan hybrid, label-wins
    tie, tiling invariant = no gaps/overlaps, sum == total).
  - test_sheetpack: grid math, centering (mixed content sizes),
    transparent-frame placeholder, 10000 px width wrap, MP multi-sheet
    split (monkeypatched MAX_MP/MAX_DIM).
  - test_bgkey: border-connectivity (enclosed white survives),
    near-white ring keyed, `--bg` green, all-bg frame -> empty.
- **All code committed to the repo** (per user: "all code, test cases
  and temp scripts need to be committed back into the repo"):
  ap0ught/glitch-items branch **export-tools**, commits a4bdfc1
  (25 files: pipeline, keyer, packer, chunker, server parser/enrichment,
  QA, superseded v1 runner, experiments/, tests/, data/ TSVs, journal,
  swftools-build.patch on base jdapena/swftools@4126f6f) + 3e1cef5
  (qa_sheets dirname fix). Repo copies have env-overridable paths
  (SWFDUMP, GLITCH_ITEMS_ROOT, RUFFLE_EXPORTER, PIPELINE_PYTHON, TSV
  paths); the /tmp working copies stay byte-identical to what produced
  the outputs (provenance). Server thumbs (1173 PNGs) deliberately NOT
  committed — regenerable via serveritems.py; .gitignore guards
  __pycache__/chunks/server-thumbs.

## Open questions

- [x] Batch 2 QA green-bg keying — clean (fox_key_check.png).
- [x] rube sheet size — resolved with the 150 MP split cap (2 sheets).
- [ ] Full run: 2,651 items / 4,790 sheets at scale 4 on /tmp (NO
      --keep-raw — disk), 4 parallel pipeline chunks via fullrun.py;
      then package (tree + zip) onto /home. Awaiting go-ahead.

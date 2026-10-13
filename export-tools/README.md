# export-tools

Export pipeline that turns this repo's 2,651 Flash (SWF) item assets into
engine-ready sprite sheets + per-item JSON manifests, structured the way
the original Glitch game itself addressed item animation states.

Everything here is the tooling developed for that export (scripts, tests,
derived data tables, run journal, and the swftools build patch). The
exported assets themselves are large binary trees and are **not**
committed here - they are built out-of-tree (see "Full run").

## Layout

| path | what it is |
|---|---|
| `scenes.py` | extract each SWF's scene/label table (tag 86) + stage bg color (tag 9) via `swfdump -d`, in parallel -> `data/scenes.tsv` |
| `manifest.sh` | per-SWF width/height/rate/frame-count -> `data/swf-manifest.tsv` |
| `pipeline.py` | the export driver: Ruffle render -> segment split -> bg-key -> sheet pack -> `item.json` |
| `bgkey.py` | border-flood background keyer with halo decontamination (per-item bg color) |
| `sheetpack.py` | grid sprite-sheet packer (10000 px width cap, 150 MP per-sheet split) |
| `fullrun.py` | whole-repo run in frame-balanced parallel chunks |
| `serveritems.py` | parse glitch-GameServerJS item configs + official 40x40 thumbs -> `data/server-items.tsv` |
| `enrich.py` | merge server data (label/description/tags/position/asset_url/official icon) into `item.json` |
| `qa_sheets.py` | QA contact sheet over an export root |
| `run_batch.sh` | **superseded** v1 flat runner (kept as history of batch 1) |
| `tests/` | runnable test suite (`tests/run_all.sh`) |
| `experiments/` | superseded exploratory parsers (kept for provenance) |
| `data/` | derived TSV tables (regenerable from the scripts above) |
| `swftools-build.patch` | patch set that makes jdapena/swftools build on a 2026 toolchain |
| `JOURNAL.md` | run journal: findings, dead ends, disk topology, decisions |

## Output shape

```
<export_root>/<repo path minus .swf>/
    item.json            # engine manifest (see below)
    <segment>/
        frames/000.png ...   # keyed (transparent) frames, per segment
        sheet.png            # packed grid sheet (or sheet_0, sheet_1, ...)
        sheet.json           # per-frame offset/size, cell dims, sheet list
    raw/                 # un-keyed renders, only with --keep-raw
```

`item.json`: `item`, `category`, `source`, `stage [w,h]`, `fps`, `scale`,
`bg_color`, `total_frames`, `segment_count`, `icon_segment`, and
`segments[]` (`name`, `start_frame`, `frames`, `sheets[]`, `frames_dir`).
`enrich.py` adds a `server` block (display label, description, tags,
classes, CDN asset URL + timestamp, official 40x40 icon as
`icon_official.png`, official stage position) for the ~1,166 items whose
names match a server config stem.

### Segment rule

Each SWF's tag-86 scene starts and frame-label starts are merged into a
sorted boundary set; each window `[b_i, b_{i+1})` becomes one segment,
named by the **label** at the boundary if present (labels are the finer,
descriptive names the game engine plays), else the scene name, else
`start`/`part{i}`. Names are sanitised to `[A-Za-z0-9_]`. This matches how
`glitch-client` (`ItemSSManager`, `itemviewer.as`) and
`glitch-GameServerJS` (`tool_base.updateState()`, trant `setState`) address
animation states - verified on the hybrid items (frying pan: 5 scenes +
3 labels -> exactly the 7 states the server cycles through).

### Background keying

Each SWF's `SetBackgroundColor` (tag 9) is the stage background, not an
assumed white (41 distinct colors across the set; 468 items non-white,
top offender 66/99/99). `bgkey.py` flood-fills that color from the image
border (so same-color regions *enclosed* by the sprite survive), then
decontaminates the anti-aliased halo (alpha ramp + un-premultiply) to kill
colored fringing. Rendered corners were verified to always equal the
SetBackgroundColor on this set.

## Dependencies

1. **swftools** (for `swfdump`): build jdapena/swftools applying
   `swftools-build.patch` (14k-line diff incl. regenerated `configure`;
   base commit `jdapena/swftools@4126f6f`), e.g.
   `./configure CFLAGS=-std=gnu17 && make && make install`
   into a prefix; put `swfdump` on PATH or export `SWFDUMP=/path/swfdump`.
2. **Ruffle exporter**: a Rust build of Ruffle's `exporter` example
   (`cargo build --release --example exporter`). Set `RUFFLE_EXPORTER`
   to the binary; flags used: `-s -f all --scale N`.
3. **Python 3** with Pillow, numpy, scipy (venv fine).

Overridable environment: `SWFDUMP`, `GLITCH_ITEMS_ROOT` (default: parent
of this dir), `RUFFLE_EXPORTER`, `PIPELINE_PYTHON`, `SCENES_TSV`,
`MANIFEST_TSV`, `SERVER_ITEMS_TSV`, `SERVER_THUMBS`, `CHUNKS_DIR`.

## Usage

```bash
# one-off batch (from the repo root)
export-tools/pipeline.py /path/export 4 --keep-raw \
    ./food/apple/apple.swf ./inhabitants/fox/npc_fox.swf ...

# whole repo, 4 frame-balanced parallel pipelines
export-tools/fullrun.py /path/export/full 4 --workers 4

# server-data enrichment (needs data/server-items.tsv + server thumbs dir)
SERVER_THUMBS=/path/server-thumbs export-tools/enrich.py /path/export/full

# QA contact sheet over an export root
export-tools/qa_sheets.py /path/export/full /path/qa.png

# regenerate the data tables (from the repo root)
SWFDUMP=... export-tools/scenes.py export-tools/data/scenes.tsv
SWFDUMP=... ./export-tools/manifest.sh > export-tools/data/swf-manifest.tsv
export-tools/serveritems.py /path/glitch-GameServerJS/items \
    export-tools/data/server-items.tsv /path/server-thumbs
```

Scale 4 is the quality bar used for the test batches; the run was staged
for the full 2,651-item set at scale 4 on tmpfs with `--keep-raw` off
(roughly 1-2 h on 4 workers, ~1.5-2 GB peak).

## Tests

```bash
PY=/path/venv/python export-tools/tests/run_all.sh
```

- `tests/test_scenes.py` - byte-exact tag-86 parser fixtures (apple / fox /
  woodworker tag bodies captured from `swfdump -d`) + VL-integer edge cases
- `tests/test_segment_merge.py` - the merge rule pinned against real items
  (frying pan hybrid, label-wins tie, tiling invariant: no gaps/overlaps)
- `tests/test_sheetpack.py` - grid math, centering, transparent-frame
  placeholder, 10000 px width wrap, MP multi-sheet split
- `tests/test_bgkey.py` - border-connectivity (enclosed white survives),
  near-white halo, non-white `--bg`, all-bg frame

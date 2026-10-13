#!/bin/bash
# run_batch.sh - export Glitch SWF items: frames -> keyed PNGs -> sprite sheets
# Usage: run_batch.sh <export_root> <item1> [item2 ...]
#   items are repo-relative SWF paths (./food/apple/apple.swf)
#
# SUPERSEDED by pipeline.py (segment-aware, writes item.json); kept as the
# original flat-export runner that produced batch 1.
# All paths overridable via environment (ROOT/EXPORTER/PY/SCALE).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-$(dirname "$HERE")}"
EXPORTER="${EXPORTER:-/tmp/opencode/ruffle/target/release/exporter}"
PY="${PY:-python3}"
SCALE="${SCALE:-2}"
BATCH="${1:-$PWD/batch1}"
shift || true
mkdir -p "$BATCH"
LOG="$BATCH/batch.log"
: > "$LOG"

ok=0; fail=0
for item in "$@"; do
  rel="$item"
  swf="$ROOT/$item"
  name=$(basename "$swf" .swf)
  cat=$(echo "$item" | cut -d/ -f2)
  outdir="$BATCH/$cat/$name"
  frames="$outdir/frames"
  raw="$outdir/raw"
  if [ ! -f "$swf" ]; then echo "MISS $item" | tee -a "$LOG"; fail=$((fail+1)); continue; fi
  rm -rf "$outdir"; mkdir -p "$frames" "$raw"
  if ! "$EXPORTER" -s -f all --scale "$SCALE" "$swf" "$raw" >>"$LOG" 2>&1; then
    echo "FAIL_EXPORT $item" | tee -a "$LOG"; fail=$((fail+1)); continue
  fi
  nraw=$(ls "$raw" | wc -l)
  if [ "$nraw" -eq 0 ]; then echo "FAIL_NOFRAMES $item" | tee -a "$LOG"; fail=$((fail+1)); continue; fi
  keyfail=0
  for f in "$raw"/*.png; do
    b=$(basename "$f")
    if ! "$PY" "$HERE/bgkey.py" "$f" "$frames/$b" >>"$LOG" 2>&1; then
      cp "$f" "$frames/$b"; keyfail=1
    fi
  done
  if ! "$PY" "$HERE/sheetpack.py" "$frames" "$outdir" >>"$LOG" 2>&1; then
    echo "FAIL_SHEET $item" | tee -a "$LOG"; fail=$((fail+1)); continue
  fi
  note="OK"; [ "$keyfail" -eq 1 ] && note="OK_KEYFALLBACK"
  echo "$note $item frames=$nraw scale=$SCALE | $(ls "$frames" | wc -l) keyed" | tee -a "$LOG"
  ok=$((ok+1))
done
echo "BATCH DONE: ok=$ok fail=$fail log=$LOG"
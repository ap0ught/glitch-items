#!/bin/bash
# Generate manifest of all SWFs: path, width, height, rate, frames
DUMP="${SWFDUMP:-$(command -v swfdump || echo /tmp/opencode/prefix/bin/swfdump)}"
find . -name "*.swf" -print0 | while IFS= read -r -d '' f; do
  out=$("$DUMP" -X -Y -r -f "$f" 2>/dev/null | tr -d '\n' | sed 's/ -/ /g')
  # "X 42 Y 42 r 30.00 f 5"
  w=$(echo "$out" | awk '{print $2}')
  h=$(echo "$out" | awk '{print $4}')
  r=$(echo "$out" | awk '{print $6}')
  n=$(echo "$out" | awk '{print $8}')
  printf '%s\t%s\t%s\t%s\t%s\n' "$f" "$w" "$h" "$r" "$n"
done

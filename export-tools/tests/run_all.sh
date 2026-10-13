#!/bin/bash
# run_all.sh - run the whole export-tools test suite.
#
# bgkey/sheetpack need numpy/scipy/Pillow - point PY at a venv that has
# them (the suite was developed with /tmp/opencode/swfenv):
#
#   PY=/tmp/opencode/swfenv/bin/python ./run_all.sh
set -u
PY="${PY:-python3}"
HERE="$(cd "$(dirname "$0")" && pwd)"

fail=0
for t in "$HERE"/test_*.py; do
  echo "== $(basename "$t")"
  if "$PY" "$t"; then
    echo
  else
    echo "FAILED: $t"
    fail=1
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "ALL TESTS PASSED"
else
  echo "SOME TESTS FAILED"
  exit 1
fi

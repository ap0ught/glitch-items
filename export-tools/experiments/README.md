# experiments/

Superseded exploratory scripts, kept for provenance (they document dead
ends - see `../JOURNAL.md`). Do not use:

- `swfpeek.py` - first hand-rolled SWF tag walker. Dead end: this
  collection's SWFs carry a non-standard 8-byte zlib preamble that breaks
  tag walking from offset 16; `swfdump -d` output is the trusted byte
  source instead.
- `swfscenes.py` - first tag-86 decoder draft with the variable-length
  frame decode backwards (shift direction wrong). Replaced by
  `../scenes.py`, which parses the same bytes correctly.

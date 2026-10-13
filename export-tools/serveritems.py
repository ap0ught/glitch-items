#!/usr/bin/env python3
"""
serveritems.py - parse the 1,288 Glitch GameServerJS item configs into a
flat TSV + save the official item thumbnails.

The configs are generated JS with stable formatting (one file per item
class, in glitch-GameServerJS/items/). Extracted per item:

  stem          file name minus .js
  label         display name
  name_single / name_plural
  description   (first sentence, HTML tags stripped)
  version       server version timestamp
  asset_url     asset_swf_v (CDN url of the SWF the game served)
  asset_ts      timestamp embedded in the asset URL
  scale         adjusted_scale
  pos_x/y/w/h   getAssetInfo() stage position + bounding box
  has_thumb     getAssetInfo() carried a base64 png thumb
  classes       parent_classes (csv)
  tags          tags (csv)
  generated     "generated ok YYYY-MM-DD" trailer, if present

Thumbs (base64 PNG, backslash-escaped slashes) are decoded to
thumbs/<stem>.png.

Usage: serveritems.py <items_dir> <out.tsv> <thumbs_dir>
"""
import base64
import os
import re
import sys


def js_str(m):
    if not m:
        return ""
    s = m.group(1) if hasattr(m, "group") else m
    return js_unescape(s)


def js_unescape(s):
    table = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\",
             '"': '"', "/": "/"}
    return re.sub(r"\\([ntr\"/\\])", lambda m: table[m.group(1)], s)


def main():
    items_dir, out_tsv, thumbs_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(thumbs_dir, exist_ok=True)
    rows = []
    for fn in sorted(os.listdir(items_dir)):
        if not fn.endswith(".js"):
            continue
        stem = fn[:-3]
        src = open(os.path.join(items_dir, fn),
                  encoding="utf-8", errors="replace").read()

        def var(name, pat=None):
            if pat is None:
                pat = rf'var\s+{name}\s*=\s*"([^"]*)"'
            return js_str(re.search(pat, src))

        label = var("label")
        version = var("version")
        name_single = var("name_single")
        description = var("description")

        m = re.search(r"asset_swf_v\s*:\s*\"([^\"]+)\"", src)
        asset_url = js_str(m) if m else ""
        m = re.search(r"-(\d{10})\.swf\"", src)
        asset_ts = m.group(1) if m else ""

        m = re.search(r"var\s+adjusted_scale\s*=\s*([\d.]+)", src)
        scale = m.group(1) if m else "1"

        m = re.search(r"'position'\s*:\s*\{[^}]*\}", src)
        px = py = pw = ph = ""
        if m:
            pos = dict(re.findall(r'"([xywh])"\s*:\s*(-?[\d.]+)', m.group(0)))
            px, py, pw, ph = (pos.get(c, "") for c in "xywh")

        m = re.search(r"'thumb'\s*:\s*\"([^\"]+)\"", src)
        has_thumb = bool(m)
        if m:
            b64 = re.sub(r"\s+", "", js_unescape(m.group(1)))
            try:
                png = base64.b64decode(b64)
                if png[:8] == b"\x89PNG\r\n\x1a\n":
                    with open(os.path.join(thumbs_dir, stem + ".png"),
                              "wb") as fh:
                        fh.write(png)
                else:
                    has_thumb = False
            except Exception:
                has_thumb = False

        m = re.search(r"parent_classes\s*=\s*\[([^\]]*)\]", src)
        classes = ""
        if m:
            classes = ",".join(js_str(x) for x in
                               re.findall(r'"([^"]*)"', m.group(1)))

        m = re.search(r"var tags\s*=\s*\[([^\]]*)\]", src)
        tags = ""
        if m:
            tags = ",".join(js_str(x) for x in
                            re.findall(r'"([^"]*)"', m.group(1)))

        m = re.search(r"generated ok (\d{4}-\d{2}-\d{2})", src)
        generated = m.group(1) if m else ""

        desc = re.sub(r"<[^>]+>", "", description)
        desc = desc.split(".")[0].strip()[:100]
        rows.append([stem, label, name_single, desc, version, asset_url,
                     asset_ts, scale, px, py, pw, ph,
                     "1" if has_thumb else "0", classes, tags, generated])

    hdr = ["stem", "label", "name_single", "description", "version",
           "asset_url", "asset_ts", "scale", "pos_x", "pos_y", "pos_w",
           "pos_h", "has_thumb", "classes", "tags", "generated"]
    with open(out_tsv, "w") as fh:
        fh.write("\t".join(hdr) + "\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    print(f"wrote {out_tsv} ({len(rows)} rows, "
          f"{sum(1 for r in rows if r[12] == '1')} thumbs)")


if __name__ == "__main__":
    main()

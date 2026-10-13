#!/usr/bin/env python3
"""
enrich.py - merge Glitch GameServerJS item data into exported item.json
files, and drop the official 40x40 icon thumbnail into each item dir.

Reads server-items.tsv (from serveritems.py) and adds to every
item.json whose item name matches a server stem:

    "server": {
        "label", "description", "tags", "classes",
        "asset_url"     (the exact SWF the live game served),
        "asset_ts", "server_version", "generated",
        "position"      {x,y,w,h} - official stage anchor/box,
        "official_icon" "icon_official.png" (if the thumb exists)
    }

Usage: enrich.py <export_root>
(idempotent - re-runs just rewrite the server block)
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.environ.get("SERVER_ITEMS_TSV") \
    or os.path.join(HERE, "data", "server-items.tsv")
THUMBS = os.environ.get("SERVER_THUMBS") \
    or os.path.join(HERE, "server-thumbs")


def main():
    export_root = sys.argv[1]
    srv = {}
    hdr = None
    for i, line in enumerate(open(TSV)):
        if i == 0:
            hdr = line.rstrip("\n").split("\t")
            continue
        r = dict(zip(hdr, line.rstrip("\n").split("\t")))
        srv[r["stem"]] = r

    n_match = n_thumb = 0
    for dirpath, dirnames, filenames in os.walk(export_root):
        if "item.json" not in filenames:
            continue
        p = os.path.join(dirpath, "item.json")
        info = json.load(open(p))
        stem = info["item"]
        r = srv.get(stem)
        if r:
            block = {
                "label": r["label"],
                "description": r["description"],
                "tags": r["tags"].split(",") if r["tags"] else [],
                "classes": r["classes"].split(",") if r["classes"] else [],
                "asset_url": r["asset_url"],
                "asset_ts": r["asset_ts"],
                "server_version": r["version"],
                "generated": r["generated"],
            }
            if r["pos_x"]:
                block["position"] = {
                    "x": float(r["pos_x"]), "y": float(r["pos_y"]),
                    "w": float(r["pos_w"]), "h": float(r["pos_h"]),
                }
            thumb = os.path.join(THUMBS, stem + ".png")
            if os.path.exists(thumb):
                shutil.copy(thumb,
                            os.path.join(dirpath, "icon_official.png"))
                block["official_icon"] = "icon_official.png"
                n_thumb += 1
            info["server"] = block
            n_match += 1
            json.dump(info, open(p, "w"), indent=1)
    print(f"enriched {n_match} items ({n_thumb} with official icon)")


if __name__ == "__main__":
    main()

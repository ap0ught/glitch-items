#!/usr/bin/env python3
"""
bgkey.py - remove a flat stage background from rendered Glitch item frames.

Generalized keyer:
  1. Candidate mask = pixels within --tol of the stage background color
     (from the SWF's SetBackgroundColor tag; white by default).
  2. Flood fill from the image border over candidates (4-connected,
     scipy.ndimage.label) -> the border-connected background region only.
     Same-colored pixels enclosed by the sprite survive.
  3. Halo decontamination: pixels within --halo px of the removed region get
     an alpha ramp + un-premultiply against the bg color, which removes the
     colored fringing left by anti-aliasing blends toward the bg color.

Usage: bgkey.py <in.png> <out.png> [--bg R,G,B] [--tol N] [--halo N]
"""
import argparse
import sys

import numpy as np
from PIL import Image
from scipy import ndimage


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--bg", default="255,255,255",
                    help="background color R,G,B (default white)")
    ap.add_argument("--tol", type=int, default=28,
                    help="whiteness/background tolerance for candidates")
    ap.add_argument("--halo", type=int, default=2,
                    help="decontamination radius in px around the keyed area")
    args = ap.parse_args()

    bg = np.array([int(v) for v in args.bg.split(",")], dtype=np.float32)

    im = Image.open(args.inp).convert("RGBA")
    arr = np.array(im, dtype=np.float32)
    h, w = arr.shape[:2]

    diff = np.abs(arr[..., :3] - bg).max(axis=2)  # (H,W) 0..~384
    cand = diff <= args.tol

    # connected components of candidates, 4-connected
    structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8)
    labels, n = ndimage.label(cand, structure=structure)
    if n > 0:
        border = set(np.unique(np.concatenate([
            labels[0, :], labels[-1, :], labels[:, 0], labels[:, -1]
        ])))
        border.discard(0)
        if border:
            mask = np.isin(labels, list(border))
        else:
            mask = np.zeros_like(cand)
    else:
        mask = np.zeros_like(cand)

    out = arr.copy()
    out[mask, 3] = 0

    # halo decontamination
    if mask.any() and args.halo > 0:
        dil = ndimage.binary_dilation(mask, structure=structure,
                                      iterations=args.halo)
        halo = dil & ~mask & (diff < args.tol * 3)
        ri, ci = np.nonzero(halo)
        if len(ri):
            p = arr[ri, ci, :3]
            d = diff[ri, ci]
            alpha = np.clip(d / 64.0, 0.0, 1.0)  # bg-ness -> transparency
            alpha = np.where(d < 8, 0.0, alpha)  # pure bg leftovers -> gone
            out[ri, ci, 3] = (alpha * 255).astype(np.float32)
            # un-premultiply against bg: c' = (c - bg*(1-a)) / a
            a = np.clip(alpha, 1.0 / 255.0, 1.0)
            un = np.clip((p - bg * (1.0 - a)[:, None]) / a[:, None], 0.0, 255.0)
            keep = alpha >= 1.0
            for c in range(3):
                out[ri, ci, c] = np.where(keep, p[:, c], un[:, c])

    Image.fromarray(out.astype(np.uint8), "RGBA").save(args.out, "PNG")
    a = out[..., 3]
    opq = 100.0 * np.count_nonzero(a > 0) / (h * w)
    print(f"{args.inp} -> {args.out} {w}x{h} bg={args.bg} "
          f"keyed={100.0 * mask.sum() / (h * w):.0f}% opaque={opq:.0f}%")


if __name__ == "__main__":
    main()
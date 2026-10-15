#!/usr/bin/env python3
"""Find the scene-cut frames from the timeline and verify each one by luminance.

    python3 check_cuts.py --frames frames --timeline timeline.json [--fps 30]
    python3 check_cuts.py --frames frames --timeline timeline.json --probe 476 477 478

Never use frame numbers copied from a note, a mockup or a test at another frame
rate. The cut after scene k is frame = round(cumulative_seconds * fps) of the
timeline you are rendering. This script computes that, then looks at +-8 frames
around it and reports the darkest frame and its mean luminance. If the page
dips to black across cuts, the darkest frame must sit on (within 2 frames of)
the computed cut; if it does not, either the cut frame or the page timing is
wrong. Frames outside the captured range are skipped (numbering is absolute).

Needs Pillow: pip3 install pillow
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageStat


def lum(frames: Path, n: int):
    p = frames / f"f{n:06d}.jpg"
    if not p.exists():
        return None
    return ImageStat.Stat(Image.open(p).convert("L").resize((160, 90))).mean[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frames", type=Path, required=True)
    ap.add_argument("--timeline", type=Path, required=True)
    ap.add_argument("--fps", type=float, default=30, help="must equal the capture fps")
    ap.add_argument("--window", type=int, default=8)
    ap.add_argument("--probe", type=int, nargs="*", help="also print mean luminance of these frames")
    a = ap.parse_args()

    scenes = json.loads(a.timeline.read_text())["scenes"]
    print(f"fps {a.fps:g}; {len(scenes)} scenes; total {sum(s['dur'] for s in scenes):.2f}s "
          f"= {round(sum(s['dur'] for s in scenes) * a.fps)} frames")
    t, bad, checked = 0.0, 0, 0
    for k, s in enumerate(scenes[:-1], 1):
        t += s["dur"]
        b = round(t * a.fps)
        vals = [(lum(a.frames, n), n) for n in range(b - a.window, b + a.window + 1)]
        vals = [(v, n) for v, n in vals if v is not None]
        if not vals:
            print(f"cut {k:>2}->{k + 1:<2} at {t:7.2f}s  frame {b:6d}: not in captured range")
            continue
        checked += 1
        v, n = min(vals)
        ref = lum(a.frames, b - 20)
        off = n - b
        ok = abs(off) <= 2
        bad += not ok
        refs = f"{ref:5.1f}" if ref is not None else "  n/a"
        print(f"cut {k:>2}->{k + 1:<2} at {t:7.2f}s  frame {b:6d}: darkest f{n:06d} "
              f"(offset {off:+d}) mean {v:5.1f}; f{b - 20:06d} mean {refs}  {'ok' if ok else 'CHECK'}")
    if a.probe:
        print("probe:", {n: (round(lum(a.frames, n), 1) if lum(a.frames, n) is not None else None) for n in a.probe})
    print(f"{checked} cuts checked, {bad} off-centre")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

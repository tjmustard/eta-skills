#!/usr/bin/env python3
"""Render ONE scene in several Kokoro voices so a person can pick by ear.

    python3 sample_voices.py --lines lines.json --scene 2
    python3 sample_voices.py --lines lines.json --scene 2 --voices bm_george,bm_fable --speed 0.88

Writes samples/<voice>.mp3 (mono, 44.1 kHz, 128 kbps) and prints each length.
Pick a scene with numbers and a long sentence in it: that is where voices
differ. Use the speed you intend to build with, so the lengths mean something.
Choosing is a listening decision; this script only produces the candidates.
"""
import argparse
import json
import subprocess
import sys
import warnings
from pathlib import Path

import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_narration as b  # noqa: E402

warnings.filterwarnings("ignore")

DEFAULT_VOICES = "af_heart,af_nicole,af_sarah,bf_emma,am_michael,am_adam,bm_george,bm_fable"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lines", type=Path, required=True)
    ap.add_argument("--scene", type=int, default=1, help="scene number n")
    ap.add_argument("--voices", default=DEFAULT_VOICES)
    ap.add_argument("--speed", type=float, default=0.88)
    ap.add_argument("--gap", type=float, default=0.45)
    ap.add_argument("--repo-id", default="hexgrad/Kokoro-82M")
    ap.add_argument("--out-dir", type=Path, default=Path("samples"))
    a = ap.parse_args()

    scenes = json.loads(a.lines.read_text())["scenes"]
    by_n = {s.get("n", i + 1): s for i, s in enumerate(scenes)}
    text = by_n[a.scene]["text"]
    a.out_dir.mkdir(parents=True, exist_ok=True)
    words = len(text.split())

    for v in [x.strip() for x in a.voices.split(",") if x.strip()]:
        pipe = b.make_pipeline(v, a.repo_id)
        wav, mp3 = a.out_dir / f"{v}.wav", a.out_dir / f"{v}.mp3"
        sf.write(wav, b.synth(pipe, text, v, a.speed, a.gap, {}), b.SR)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-ac", "1",
                        "-ar", "44100", "-b:a", "128k", str(mp3)], check=True)
        wav.unlink()
        d = b.duration(mp3)
        print(f"{v:12s} {d:5.1f}s  {words / d * 60:.0f} wpm", flush=True)


if __name__ == "__main__":
    sys.exit(main())

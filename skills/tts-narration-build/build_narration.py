#!/usr/bin/env python3
"""Narration build: a lines JSON -> trimmed, loudness-normalised audio files.

Kokoro TTS for synthesis, ffmpeg for everything after it. Run it from the
directory you want the outputs in (or pass --out-dir).

    python3 build_narration.py --lines lines.json                    # all scenes, mp3 + m4a
    python3 build_narration.py --lines lines-v2.json --tag v2 --formats m4a
    python3 build_narration.py --lines lines.json --only 3 7         # rebuild two scenes
    python3 build_narration.py --lines lines.json --reuse-wav        # re-encode cached WAVs only

Lines JSON: {"scenes": [{"id": "scene-01", "n": 1, "text": "...",
                         "title": "...", "target_seconds": 30}, ...]}
`id` and `text` are required; `n`, `title`, `target_seconds` are optional.
The `text` is spoken verbatim (apart from --pron overrides).

Outputs (names are decided here and nowhere else; never rename by hand):
    audio-<fmt>[-<tag>]/<stem>.<fmt>   <stem> = id, or id with -<tag>- before the last segment
    .work[-<tag>]/<id>.wav             raw synthesis, kept so --reuse-wav can re-encode it
    durations[-<tag>].md               target vs actual table
    build-info[-<tag>].json            settings, versions, loudnorm measurements, md5s
    MANIFEST[-<tag>].md5               `md5sum -c` compatible list of the published files
    listening-check[-<tag>].md         the by-ear checklist (see SKILL.md; not optional)
"""
import argparse
import datetime
import hashlib
import importlib.metadata as md
import json
import re
import subprocess
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import soundfile as sf

warnings.filterwarnings("ignore")

SR = 24000  # Kokoro output rate


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def duration(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "csv=p=0", str(path)]).stdout
    return float(out.strip())


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def stem_for(scene_id: str, tag: str) -> str:
    """scene-01 + v2 -> scene-v2-01. An id with no '-' becomes <id>-<tag>."""
    if not tag:
        return scene_id
    head, sep, tail = scene_id.rpartition("-")
    return f"{head}-{tag}-{tail}" if sep else f"{scene_id}-{tag}"


def make_pipeline(voice: str, repo_id: str, lang: str | None = None):
    from kokoro import KPipeline
    # Kokoro lang codes: 'a' American English, 'b' British English. Voice names
    # start with the same letter (af_*, am_*, bf_*, bm_*).
    return KPipeline(lang_code=lang or ("b" if voice.startswith("b") else "a"), repo_id=repo_id)


def synth(pipeline, text: str, voice: str, speed: float, gap_s: float,
          pron: dict[str, str]) -> np.ndarray:
    """Synthesise sentence by sentence and join with gap_s of silence.

    Sentences are split on [.!?] followed by whitespace, so an abbreviation
    ("Dr. Smith") or a decimal followed by a space would split mid-sentence.
    Spell such things out in the script.
    """
    for src, dst in pron.items():
        text = text.replace(src, dst)
    gap = np.zeros(int(SR * gap_s), dtype=np.float32)
    parts = []
    for sentence in re.split(r"(?<=[.!?])\s+", text.strip()):
        for _, _, audio in pipeline(sentence, voice=voice, speed=speed, split_pattern=r"\n+"):
            parts.append(np.asarray(audio, dtype=np.float32))
        parts.append(gap)
    return np.concatenate(parts[:-1])


def process(raw_wav: Path, outs: dict[str, Path], kbps: dict[str, int], cfg) -> dict:
    """Trim silence -> two-pass loudnorm -> resample -> lead-in -> encode each format.

    Returns the pass-1 loudnorm measurements. The lead-in is added after
    loudnorm, so it does not affect the measured loudness.
    """
    trim = ("silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,"
            "areverse,"
            "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,"
            "areverse")
    ln = f"loudnorm=I={cfg.lufs}:TP={cfg.tp}:LRA={cfg.lra}"
    probe = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(raw_wav),
         "-af", f"{trim},{ln}:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True).stderr
    stats = json.loads(probe[probe.rindex("{"):])
    ln2 = (f"{ln}:measured_I={stats['input_i']}:measured_TP={stats['input_tp']}"
           f":measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}"
           f":offset={stats['target_offset']}:linear=true")
    chain = f"{trim},{ln2},aresample=44100,adelay={cfg.lead_in_ms}:all=1"
    codecs = {"mp3": "libmp3lame", "m4a": "aac"}
    for fmt, out in outs.items():
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw_wav),
             "-af", chain, "-ac", "1", "-ar", "44100",
             "-c:a", codecs[fmt], "-b:a", f"{kbps[fmt]}k", "-movflags", "+faststart", str(out)])
    return {k: stats[k] for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")}


def write_table(path: Path, scenes, results, cfg):
    rows = ["| id | title | target_seconds | actual_seconds | delta | flag |",
            "|---|---|---:|---:|---:|---|"]
    tt = ta = 0.0
    have_targets = False
    for s in scenes:
        a = results.get(s["id"])
        if a is None:
            continue
        t = s.get("target_seconds")
        if t is None:
            rows.append(f"| {s['id']} | {s.get('title', '')} | - | {a:.1f} | - | |")
            ta += a
            continue
        have_targets = True
        d = a - t
        pct = d / t * 100
        flag = f"**{pct:+.0f}%**" if abs(pct) > cfg.flag_pct else ""
        rows.append(f"| {s['id']} | {s.get('title', '')} | {t} | {a:.1f} | {d:+.1f} | {flag} |")
        tt += t
        ta += a
    if have_targets:
        rows.append(f"| **total** | | {tt:.0f} | {ta:.1f} | {ta - tt:+.1f} | |")
    else:
        rows.append(f"| **total** | | - | {ta:.1f} | - | |")
    path.write_text(
        "# Narration durations\n\n"
        f"Voice `{cfg.voice}`, speed {cfg.speed}, sentence gap {cfg.gap}s. "
        f"Flag = more than {cfg.flag_pct}% over or under target.\n\n" + "\n".join(rows) + "\n")


def write_listening_check(path: Path, scenes, picks):
    prev = path.with_suffix(".prev.md")
    if path.exists() and "[x]" in path.read_text().lower():
        path.replace(prev)  # a ticked sheet is evidence; do not overwrite it silently
    lines = [
        "# Listening check",
        "",
        "**STATUS: NOT LISTENED.** Loudness, peaks and durations are measurements, not verification.",
        "A person must play each scene below start to finish and tick it. Until then the",
        "build report must say \"not listened\".",
        "",
        "Listen for: wrong number or unit readings, acronyms, proper nouns, rushed long",
        "sentences, clipped first syllable, odd pauses, clicks at the start or end.",
        "",
        "| done | scene | heard clean | note |",
        "|---|---|---|---|",
    ]
    by_id = {s["id"]: s for s in scenes}
    for sid in picks:
        lines.append(f"| [ ] | {sid} | [ ] yes  [ ] problem | |")
    lines += ["", "Listened by: ________   Date: ________", "", "## Text of the scenes to check", ""]
    for sid in picks:
        lines += [f"**{sid}**", "", by_id[sid]["text"], ""]
    path.write_text("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lines", type=Path, required=True, help="script JSON")
    ap.add_argument("--tag", default="", help="version tag, e.g. v2: separate folders and filenames")
    ap.add_argument("--formats", default="mp3,m4a", help="comma list from: mp3, m4a")
    ap.add_argument("--mp3-kbps", type=int, default=192)
    ap.add_argument("--m4a-kbps", type=int, default=96)
    ap.add_argument("--voice", default="bm_fable")
    ap.add_argument("--speed", type=float, default=0.88)
    ap.add_argument("--gap", type=float, default=0.45, help="seconds of silence between sentences")
    ap.add_argument("--lufs", type=float, default=-16)
    ap.add_argument("--tp", type=float, default=-1.5)
    ap.add_argument("--lra", type=float, default=11)
    ap.add_argument("--lead-in-ms", type=int, default=150)
    ap.add_argument("--repo-id", default="hexgrad/Kokoro-82M")
    ap.add_argument("--lang", default=None, help="Kokoro lang code; default from the voice prefix")
    ap.add_argument("--pron", type=Path, help='JSON {"substring": "[substring](/IPA/)"} pronunciation overrides')
    ap.add_argument("--only", type=int, nargs="*", help="scene numbers (n) to build; others are left untouched")
    ap.add_argument("--reuse-wav", action="store_true", help="re-encode cached WAVs, no synthesis")
    ap.add_argument("--listen", type=int, nargs="*", help="scene numbers for the listening checklist")
    ap.add_argument("--flag-pct", type=float, default=15)
    ap.add_argument("--out-dir", type=Path, default=Path.cwd())
    cfg = ap.parse_args()

    fmts = [f.strip() for f in cfg.formats.split(",") if f.strip()]
    bad = [f for f in fmts if f not in ("mp3", "m4a")]
    if bad:
        sys.exit(f"unknown format(s): {bad}")
    kbps = {"mp3": cfg.mp3_kbps, "m4a": cfg.m4a_kbps}

    out = cfg.out_dir.resolve()
    sfx = f"-{cfg.tag}" if cfg.tag else ""
    dirs = {f: out / f"audio-{f}{sfx}" for f in fmts}
    work = out / f".work{sfx}"
    for d in (*dirs.values(), work):
        d.mkdir(parents=True, exist_ok=True)

    lines_bytes = cfg.lines.read_bytes()
    scenes = json.loads(lines_bytes)["scenes"]
    for i, s in enumerate(scenes):
        s.setdefault("n", i + 1)
    pron = json.loads(cfg.pron.read_text()) if cfg.pron else {}

    info_path = out / f"build-info{sfx}.json"
    info = json.loads(info_path.read_text()) if info_path.exists() else {"scenes": {}}
    info.update({
        "lines_file": cfg.lines.name,
        "lines_md5": hashlib.md5(lines_bytes).hexdigest(),
        "engine": {"repo_id": cfg.repo_id,
                   "kokoro": md.version("kokoro"), "misaki": md.version("misaki"),
                   "torch": md.version("torch"), "soundfile": md.version("soundfile")},
        "updated": datetime.datetime.now().isoformat(timespec="seconds"),
    })

    pipeline = None
    results, t_run = {}, time.time()
    for s in scenes:
        sid, stem = s["id"], stem_for(s["id"], cfg.tag)
        outs = {f: dirs[f] / f"{stem}.{f}" for f in fmts}
        measured = outs[fmts[0]]
        if cfg.only and s["n"] not in cfg.only:
            if measured.exists():
                results[sid] = duration(measured)
            continue
        raw = work / f"{sid}.wav"
        t0 = time.time()
        synthesised = not (cfg.reuse_wav and raw.exists())
        if synthesised:
            if pipeline is None:
                pipeline = make_pipeline(cfg.voice, cfg.repo_id, cfg.lang)
            sf.write(raw, synth(pipeline, s["text"], cfg.voice, cfg.speed, cfg.gap, pron), SR)
        stats = process(raw, outs, kbps, cfg)
        results[sid] = duration(measured)
        prev = info["scenes"].get(sid, {})
        if synthesised:
            # settings that shaped the WAV: only valid when this run made it
            synth_rec = {"voice": cfg.voice, "speed": cfg.speed, "gap_s": cfg.gap,
                         "pron": sorted(pron), "synth_seconds_wall": round(time.time() - t0, 1)}
        else:
            # --reuse-wav: keep what the earlier run recorded about how the WAV was made.
            # If nothing was recorded, say so rather than writing this run's flags.
            synth_rec = prev.get("synth") or {"note": "WAV not made by this tool's recorded run; "
                                                      "voice/speed/gap unknown"}
        info["scenes"][sid] = {
            "synth": synth_rec,
            "encoded_this_run": {"lufs": cfg.lufs, "tp": cfg.tp, "lra": cfg.lra,
                                 "lead_in_ms": cfg.lead_in_ms, "kbps": {f: kbps[f] for f in fmts},
                                 "reused_wav": not synthesised},
            "duration_s": round(results[sid], 3),
            "loudnorm_pass1": stats,
            "md5": {f: md5(outs[f]) for f in fmts},
        }
        tgt = f" (target {s['target_seconds']}s)" if "target_seconds" in s else ""
        print(f"{sid}: {results[sid]:.1f}s{tgt}  [{time.time() - t0:.0f}s wall]", flush=True)

    info["last_run_wall_s"] = round(time.time() - t_run, 1)
    info_path.write_text(json.dumps(info, indent=2) + "\n")
    write_table(out / f"durations{sfx}.md", scenes, results, cfg)

    manifest = out / f"MANIFEST{sfx}.md5"
    with manifest.open("w") as m:
        for f in fmts:
            for p in sorted(dirs[f].glob(f"*.{f}")):
                m.write(f"{md5(p)}  {p.relative_to(out)}\n")

    if cfg.listen:
        by_n = {s["n"]: s["id"] for s in scenes}
        picks = [by_n[n] for n in cfg.listen if n in by_n]
    elif cfg.only:
        picks = [s["id"] for s in scenes if s["n"] in cfg.only]
    else:
        longest = max(scenes, key=lambda s: len(s["text"].split()))["id"]
        picks = list(dict.fromkeys([scenes[0]["id"], longest, scenes[-1]["id"]]))
    write_listening_check(out / f"listening-check{sfx}.md", scenes, picks)

    print(f"\nwrote {', '.join(str(d.relative_to(out)) + '/' for d in dirs.values())}, "
          f"durations{sfx}.md, build-info{sfx}.json, MANIFEST{sfx}.md5")
    print(f"NOT VERIFIED: nobody has listened. Open listening-check{sfx}.md; picked: {', '.join(picks)}.")
    print("Choose the scenes to hear by what is hard in the text (numbers, units, acronyms,"
          " long sentences) and pass them with --listen.")


if __name__ == "__main__":
    sys.exit(main())

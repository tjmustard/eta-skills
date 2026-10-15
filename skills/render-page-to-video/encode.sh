#!/usr/bin/env bash
# Frames + narration -> MP4 (H.264 + AAC). Checks the frame sequence first,
# because ffmpeg's image sequence reader stops at the first missing number and
# writes a short video; the only sign is one 'Input/output error' log line.
#
#   encode.sh --frames DIR --timeline FILE --audio-dir DIR --out FILE.mp4
#             [--fps 30] [--w 1920] [--h 1080] [--start-number 0]
#             [--expect-frames N] [--narration FILE.m4a] [--preset slow] [--crf 18]
#
# --fps must equal the --fps used for capture.
# Without --narration the track is ALWAYS rebuilt from the timeline and clips
# (a leftover track from older audio is never reused).
# --start-number / --expect-frames are for encoding a test range
# (frames are numbered by absolute film position).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
FPS=30; OW=1920; OH=1080; START=0; EXPECT=""; NARR=""; PRESET=slow; CRF=18
FRAMES=""; TL=""; ADIR=""; OUT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --frames) FRAMES="$2";; --timeline) TL="$2";; --audio-dir) ADIR="$2";; --out) OUT="$2";;
    --fps) FPS="$2";; --w) OW="$2";; --h) OH="$2";; --start-number) START="$2";;
    --expect-frames) EXPECT="$2";; --narration) NARR="$2";; --preset) PRESET="$2";; --crf) CRF="$2";;
    *) echo "unknown flag $1" >&2; exit 1;;
  esac; shift 2
done
for v in FRAMES TL OUT; do [ -n "${!v}" ] || { echo "missing --$(echo $v | tr A-Z a-z)" >&2; exit 1; }; done

# 1. frame sequence: contiguous from START, and the expected count
python3 -I - "$FRAMES" "$START" "$FPS" "$TL" "$EXPECT" <<'PY'
import json, os, re, sys
d, start, fps, tl, expect = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4], sys.argv[5]
have = sorted(int(m.group(1)) for f in os.listdir(d) if (m := re.fullmatch(r"f(\d{6})\.jpg", f)))
if not have: sys.exit(f"no f%06d.jpg frames in {d}")
if expect:
    want = int(expect)
else:
    if start != 0: sys.exit("--start-number given without --expect-frames")
    want = round(sum(s["dur"] for s in json.load(open(tl))["scenes"]) * fps)
run = [n for n in have if n >= start]
gap = next((n for i, n in enumerate(run) if n != start + i), None)
if gap is not None or len(run) < want:
    first_missing = start + (run.index(gap) if gap is not None else len(run))
    sys.exit(f"FRAME CHECK FAILED: have {len(run)} contiguous-from-{start} frames, expect {want}; "
             f"first missing is f{first_missing:06d}. Rerun capture (it fills gaps).")
if len(run) > want:
    print(f"warning: {len(run)} frames present, encoding only the first {want}")
print(f"frame check ok: {want} frames from f{start:06d}")
PY

# 2. narration track
if [ -z "$NARR" ]; then
  [ -n "$ADIR" ] || { echo "need --audio-dir or --narration" >&2; exit 1; }
  NARR="$(dirname "$OUT")/narration.m4a"
  "$HERE/build-audio.sh" "$TL" "$ADIR" "$NARR"
fi

# 3. mux. -frames:v caps the video at the expected count; -shortest ends with the shorter stream.
COUNT=$(python3 -I - "$TL" "$FPS" "$EXPECT" <<'PY'
import json, sys
tl, fps, expect = sys.argv[1], float(sys.argv[2]), sys.argv[3]
print(expect or round(sum(s["dur"] for s in json.load(open(tl))["scenes"]) * fps))
PY
)
ffmpeg -hide_banner -loglevel error -stats -y -framerate "$FPS" -start_number "$START" -i "$FRAMES/f%06d.jpg" -i "$NARR" \
  -frames:v "$COUNT" -vf "scale=${OW}:${OH}:flags=lanczos" \
  -c:v libx264 -preset "$PRESET" -crf "$CRF" -pix_fmt yuv420p -profile:v high -level 4.1 \
  -movflags +faststart -c:a copy -shortest "$OUT"
echo "-> $OUT"
ffprobe -v error -show_entries stream=codec_name,width,height,nb_frames:format=duration,size -of default=nw=1 "$OUT"

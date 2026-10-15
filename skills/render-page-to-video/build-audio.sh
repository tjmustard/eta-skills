#!/usr/bin/env bash
# Pad each scene's narration clip with silence out to that scene's on-screen
# duration, then join the clips into one track that lines up with the video.
#
#   build-audio.sh TIMELINE.json AUDIO_DIR OUT.m4a [WORKDIR]
#
# TIMELINE.json: {"scenes": [{"dur": 33.8, "audio": "clip-01.m4a"}, ...]}
#   dur   seconds the scene is on screen (must equal the page's own duration)
#   audio file name inside AUDIO_DIR
# Refuses to run if any clip is LONGER than its slot: `-t` would silently cut
# the end of the narration. Fix the timeline or the clip, do not trim.
set -euo pipefail
TL="${1:?timeline.json}"; SRC="${2:?audio dir}"; OUT="${3:?out.m4a}"
WORK="${4:-$(dirname "$OUT")/audio-parts}"
rm -rf "$WORK"; mkdir -p "$WORK"; : > "$WORK/list.txt"

python3 -I - "$TL" > "$WORK/scenes.tsv" <<'PY'
import json, sys
for i, s in enumerate(json.load(open(sys.argv[1]))["scenes"], 1):
    print(f"{i}\t{s['dur']}\t{s['audio']}")
PY

while IFS=$'\t' read -r i dur clip; do
  src="$SRC/$clip"
  [ -f "$src" ] || { echo "missing clip: $src" >&2; exit 3; }
  have=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$src")
  if python3 -I -c "import sys; sys.exit(0 if float('$have') <= float('$dur') + 0.001 else 1)"; then :; else
    echo "scene $i: clip is ${have}s but the slot is ${dur}s; it would be cut off" >&2; exit 4
  fi
  p=$(printf "p%02d.m4a" "$i")
  ffmpeg -nostdin -v error -y -i "$src" -af "apad" -t "$dur" -ar 48000 -ac 2 -c:a aac -b:a 128k "$WORK/$p"
  echo "file '$p'" >> "$WORK/list.txt"
done < "$WORK/scenes.tsv"

ffmpeg -v error -y -f concat -safe 0 -i "$WORK/list.txt" -c copy "$OUT"
echo "narration track -> $OUT  ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s)"

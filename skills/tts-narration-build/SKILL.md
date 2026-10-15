---
name: tts-narration-build
description: Use when you need to turn a JSON of scene texts into loudness-matched narration audio files with local open-source TTS (Kokoro), and you want the install, settings, ffmpeg chain, versioning rule and verification steps that already worked.
---

# TTS narration build (Kokoro + ffmpeg)

Turns `{"scenes": [{"id", "text", ...}]}` into one audio file per scene, trimmed, loudness-matched, with a lead-in, plus a durations table, a manifest and a build record. Everything below was run end to end on one project; where a number is a measurement from that run it says so.

Scripts beside this file (run them, do not rewrite them):

| File | Use |
|---|---|
| `build_narration.py` | the whole pipeline; `--help` lists every flag |
| `sample_voices.py` | render one scene in several voices to choose by ear |

## What varies, and where to change it

| Varies | Change |
|---|---|
| Script text and scene list | the lines JSON (`--lines`). `id` and `text` required; `n`, `title`, `target_seconds` optional |
| Voice, pace, pauses | `--voice`, `--speed`, `--gap` |
| Loudness target | `--lufs` (default -16), `--tp` (-1.5), `--lra` (11) |
| Formats and bitrates | `--formats mp3,m4a`, `--mp3-kbps 192`, `--m4a-kbps 96` |
| Version of a script | `--tag v2`: separate folders and filenames |
| Mispronounced word | `--pron file.json` (below) |

Nothing else in the script knows about the subject matter. The text is spoken verbatim, so captions that must match the audio word for word are kept by never editing text to fix pronunciation.

## Install (worked on Ubuntu 22.04, no sudo)

```
python3 -m venv .venv && . .venv/bin/activate
pip3 install -q --upgrade pip
pip3 install -q torch --index-url https://download.pytorch.org/whl/cpu
pip3 install -q "kokoro>=0.9.4" soundfile numpy
```

Versions that ran: Python 3.10.12, `kokoro 0.9.4`, `misaki 0.9.4`, `torch 2.14.1+cpu`, `soundfile 0.14.0`, `numpy 2.2.6`, `espeakng-loader 0.2.4`, `spacy 3.8.16`, ffmpeg 4.4.2. Model repo `hexgrad/Kokoro-82M`, weights `kokoro-v1_0.pth` (HF snapshot `f3ff3571791e39611d31c381e3a41a3af07b4987`). `build-info*.json` records the versions of every build, so check there rather than trusting this list.

- **No sudo, no system `espeak-ng`:** not a blocker. `pip3 install kokoro` pulls `espeakng-loader`, which bundles it. Do not stop to `apt install espeak-ng`.
- **First run needs network:** it downloads the model and voice from Hugging Face and a spaCy model (`en-core-web-sm`) into the environment. Later runs are offline.
- **CPU wheel on purpose.** Synthesis ran on CPU (an 82M-parameter model; fast enough). The GPU was present and unused. Nothing here needs CUDA.
- ffmpeg and ffprobe must be on PATH (`apt install ffmpeg` if not).

## Choosing the voice: render candidates, a person listens, then choose

```
python3 sample_voices.py --lines lines.json --scene N --speed 0.88
```

Pick a scene that has numbers and a long sentence. It writes `samples/<voice>.mp3` and prints length and words per minute. This run rendered eight voices (`af_heart af_nicole af_sarah bf_emma am_michael am_adam bm_george bm_fable`) on one scene, the human listened, and chose `bm_fable`. The script cannot choose; pace and length are not a quality ranking. Voices differ a lot in pace: the same passage at speed 0.92 ran from 27.7 s (`bm_fable`) to 48.1 s (`af_nicole`). Use one voice and one set of settings for every scene.

## Settings that were used, and what they did

| Setting | Value | Note |
|---|---|---|
| Voice | `bm_fable`, `lang_code="b"` | `b*` voices need lang `b`, `a*` need `a`; the script derives it from the prefix |
| Speed | `0.88` | Kokoro `speed` parameter |
| Sentence gap | `0.45` s | silence inserted between sentences; no gap after the last |
| Loudness | `I=-16`, `TP=-1.5`, `LRA=11`, two-pass, `linear=true` | |
| Lead-in | 150 ms | `adelay`, so playback does not clip the first syllable |
| Output | mono, 44.1 kHz, MP3 192 kbps and AAC-LC m4a 96 kbps | |

**Calibrate pace on your own script.** Words per minute is not a property of the settings alone. On one script of many short sentences, speed 0.80 gave 121 wpm and 0.88 gave 137 wpm; on a second script with fewer, longer sentences the same 0.88 gave about 154 wpm (the gap is paid per sentence). Build once, read `durations*.md`, adjust `--speed`, rebuild. Do not trust a number from another script.

## The chain (what `process()` does, in order)

1. **Synthesise** each sentence (split on `[.!?]` plus whitespace) with `pipeline(sentence, voice, speed)`; Kokoro yields float32 at 24 kHz. Join with `0.45 s` of zeros. Write `.work/<id>.wav` (16-bit PCM, 24 kHz, mono).
2. **Trim silence** at both ends: `silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,areverse,<same>,areverse`.
3. **loudnorm pass 1** (measure only): `loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null -`.
4. **loudnorm pass 2** with the pass-1 `measured_I/TP/LRA/thresh` and `offset`, `linear=true`.
5. `aresample=44100`, then `adelay=150:all=1`.
6. **Encode**: `-ac 1 -ar 44100 -c:a libmp3lame -b:a 192k` and/or `-c:a aac -b:a 96k -movflags +faststart`.

Nothing runs after loudnorm except resample, lead-in and the codec: no peak normalise, limiter or gain stage. Measured on the published files: integrated -16.4 to -17.3 LUFS for a -16 target, true peak -1.0 to -1.7 dBFS (the lossy encode overshoots the -1.5 target by up to about 0.5 dB). If someone quotes a different peak figure, measure it: `ffmpeg -i f -af ebur128=peak=true -f null -`.

## Run it

```
. .venv/bin/activate
python3 /path/to/build_narration.py --lines lines.json                    # everything
python3 /path/to/build_narration.py --lines lines-v2.json --tag v2 --formats m4a
python3 /path/to/build_narration.py --lines lines.json --only 4 9          # only these scenes
python3 /path/to/build_narration.py --lines lines.json --reuse-wav         # re-encode cached WAVs
```

Run it from the directory that should hold the outputs, or pass `--out-dir`. It prints a flagged durations table (more than 15% off `target_seconds`). Targets in a lines file go stale when the text is edited; a flagged scene may only mean the target was never updated.

## Pronunciation overrides

Do it in the engine, never in the text. Kokoro reads `[word](/IPA/)` inline. Put substring-to-replacement pairs in a JSON file:

```json
{"millionths": "[millionths](/mˈɪljənθs/)"}
```

```
python3 build_narration.py --lines lines.json --pron pron.json --only 6
```

The replacement is applied to the text just before synthesis; the lines JSON and any captions built from it are untouched. Check what the engine will say before spending a build:

```python
for gs, ps, a in pipeline("Your sentence.", voice="bm_fable"): print(ps)
```

Tested on this setup: `bead` gave `bˈiːd`; `[bead](/bˈɛd/)` gave `bˈɛd`. This run needed no overrides and none were applied, so no list of problem words exists. Which words need one is a result of listening, not of reading.

## Output versioning: the rule

The failure this guards against: versioned sets in different folders, a hand rename (`mv -n scene-NN.m4a scene-vX-NN.m4a`) between build output and the names that were uploaded, and a rebuild that wrote one name while the upload picked up another. `mv -n` never overwrites, so a stale file with the target name silently survives a rebuild. Which of these caused the unchanged files seen in one project's upload rounds was not recorded; the rule prevents all of them.

**One writer, one name.**

1. The build script alone decides every output name and folder (`--tag`). Never rename, copy-and-rename or `mv -n` outputs.
2. A new version of the script gets a new `--tag`. Do not rebuild a new version into the old tag's folders.
3. Upload or deploy from the folder the build printed, and nothing else.
4. Before publishing run `md5sum -c MANIFEST*.md5` from the output directory. After deploying, hash the deployed files and compare them to the same manifest.
5. Anything that consumes the files by name (a page, a bundle) is configured with the names the script writes. If the consumer needs different names, change the template in `stem_for()`, then rebuild; do not rename.

Byte-identical files across two rounds mean the generation step did not run for them (see `--only`, `--reuse-wav`, a stale folder); they do not mean "the text did not change", and different bytes do not mean "the text changed". Compare `lines_md5` in `build-info*.json` to know what text a file came from.

## Reproducibility: what you can and cannot expect

- **Synthesis is not bit-reproducible.** Same text, voice, speed and machine gave the same length but a different waveform: in a test, 313,396 of 350,400 samples differed, by up to 8,882 on int16. Every re-synthesised file has a new md5.
- **Encoding is reproducible.** The same WAV through the same chain gave identical md5, twice, and reproduced a published file exactly.
- Consequences:
  - Do not "regenerate to confirm". A regeneration is a new take, to be listened to again.
  - Keep `.work*/` WAVs with the release if you need to reproduce it. Re-encode with `--reuse-wav` (about 38 s for all scenes in both formats).
  - Verify by decoded duration, loudness, and by ear. md5 equality is only meaningful for re-encodes.
  - After a partial rebuild (`--only`), the other scenes are an older take. Duration and loudness will match; the voice prosody may differ slightly. Rebuild all if the set must be one take.

## Listening: required, and not satisfied by measurements

**This run never listened to its output.** The brief asked for specific scenes to be spot-checked by ear. Only loudness, peaks and durations were measured, and the report reads as if verification happened when it did not. Measurements find clipping and level problems; they cannot find a wrong number, a mangled acronym, a rushed sentence or a mispronounced name.

The build script enforces the step:

- It prints `NOT VERIFIED: nobody has listened` at the end of every build.
- It writes `listening-check*.md`: scenes to hear, tick boxes, text, a signature line, and the header `STATUS: NOT LISTENED`. A rebuild moves a sheet that has ticks to `*.prev.md` and writes a fresh unticked one, because new audio invalidates old ticks.
- Choose scenes with `--listen N N N` by what is hard in the text: numbers and units, acronyms, proper nouns, the longest sentence, first and last scenes. The default is the first, the longest and the last, which is a floor, not a plan.

Rules:

1. A scene counts as checked only when a person has played it start to finish and ticked it.
2. If you cannot play audio (an AI agent in a terminal cannot), say so in the report in plain words: "not listened". Hand the checklist to a person. Never write "verified", "spot-checked" or "QA passed" for a set that was only measured.
3. Do not call the set final, upload it or hand it downstream as final until the sheet is ticked. If it must go earlier, label it "unreviewed".
4. A scene that fails gets a `--pron` override or a script edit, a rebuild of that scene, and a new listen.

## Time budget (CPU, 6-core Ryzen 5 2600X, about 8 minutes of audio, about 1,000 words)

| Job | Wall time |
|---|---|
| Full regeneration, scenes 2 to last | about 3.5 to 4.4 min (model load and scene 1 extra, not timed) |
| Four scenes with model load | 79.5 s |
| `--reuse-wav`, all scenes, mp3 plus m4a | about 38 s |
| First scene in a process (15 s of audio), includes model load | 18 s |
| Next scene in the same process (7 s of audio) | 6 s |
| Re-encode of one cached WAV | 1 to 2 s |

Scale roughly with words spoken. The first scene in a process pays for model load (18 s for a 15 s scene against 6 s for the next, 7 s scene; load was not timed on its own), so batch scenes into one invocation rather than one process per scene.

## Known traps

- The sentence splitter breaks on `. ! ?` plus whitespace. "Dr. Smith" or "3.5 million" splits mid-sentence and gets a 0.45 s gap in the wrong place. Spell such text out in the lines file.
- Numbers: write them as words in the lines file, as the engine reads words reliably. This run did that and did not test digits.
- The durations table compares against `target_seconds` from the lines file, which does not update when text does.
- `build-info*.json` stores the loudnorm pass-1 measurements, the settings that made each WAV, and md5s. If it says a WAV's settings are unknown, the WAV did not come from this tool.
- `--only` leaves other scenes untouched, including in `durations*.md`, which is rebuilt from the files on disk.

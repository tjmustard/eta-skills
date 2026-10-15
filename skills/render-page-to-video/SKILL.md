---
name: render-page-to-video
description: Use when you need to render a timed, animated WebGL or canvas web page to a narrated MP4 by capturing it frame by frame with Playwright, and you want the GPU check, throughput numbers, frame-numbering rules and verification steps that already worked.
---

# Render a timed animated page to MP4

Captures a page one frame at a time against a clock you step by hand (so frame N is the same picture regardless of machine speed), joins the frames with per-scene narration clips padded to scene length, and encodes H.264 + AAC. Everything below was run end to end on one page; measurements say so.

Files beside this one (run them, do not rewrite them):

| File | Use |
|---|---|
| `gpu_check.cjs` | decide whether Chromium really has the GPU, before any long run |
| `capture.mjs` | frame capture; `--help` is the header comment |
| `build-audio.sh` | pad each clip to its slot and join; refuses a clip longer than its slot |
| `encode.sh` | frame-sequence check, narration build, mux |
| `check_cuts.py` | compute scene-cut frames from the timeline and verify them by luminance |
| `examples/seek.example.js` | the page-side shim, as written for the original page |
| `examples/video.example.css` | the "video mode" stylesheet, original selectors |
| `examples/timeline.example.json` | the timeline format `build-audio.sh`, `encode.sh`, `check_cuts.py` read |

## What varies, and how to change it

| Varies | Where |
|---|---|
| The page and the clock it runs on | write a `seek.js` for your page (`examples/seek.example.js`); contract below |
| What is hidden for video | `--css` stylesheet; hide controls, captions and buttons, keep title bar, timecode and readouts |
| How the page starts | `--start '<selector>'` to click once; `--ready '<js expression>'` to wait for globals |
| Quality or mode switch after setup | `--after-setup '<js>'` |
| CDN libraries | `--route 'pattern=local/file'` (repeatable) so the render is offline |
| Layout size and sharpness | `--w --h` are the CSS size the page was designed at (leave them); raise `--dsf` for sharpness |
| Scene durations | `timeline.json`: `{"scenes": [{"dur": seconds, "audio": "clip file"}, ...]}` |
| Frame rate | `--fps` (30 used); the same value goes to `encode.sh` and `check_cuts.py` |

**Page contract** (what your `--seek` script must define): `window.__setup()` stops the live loop and returns `{total, scenes, durs}`; `window.__starts` is the array of scene start times in seconds; `window.__seek(t, fps)` puts the page in the exact state for film time `t` and renders one frame synchronously. Drive the page's clock with a fixed step `1/fps`, never wall time. The capture script needs nothing else from the page.

## Environment

```
npm init -y && npm i playwright && npx playwright install chromium
```

Versions that ran: Ubuntu 22.04.5, Node v24.15.0 (18+ required), Playwright 1.64.0, Chromium 156.0.8078.4 (Playwright build `chromium-1248`), ffmpeg 4.4.2, Pillow for `check_cuts.py` (`pip3 install pillow`). Run every script from the directory where `npm i playwright` was done: Playwright is resolved from the working directory, not from the skill folder. Headed Chromium needs a display; it ran on an X11 session. A machine with no display was not tried.

## Step 0: bundle lint (30 seconds)

A render bundle once told the operator to walk a `CHECKS.md` that was not in it. **Whatever checks file a bundle references must ship in the bundle.** Before starting, list every file a document names and confirm each exists:

```
grep -ohE '`[A-Za-z0-9_./-]+\.(md|json|sh|mjs|cjs|js|css|html|py|mp4|m4a|jpg)`' *.md \
  | tr -d '`' | sort -u | while read -r f; do [ -e "$f" ] || echo "NOT FOUND: $f"; done
```

(Tested: it reports `CHECKS.md` for a doc that names a missing one. Ignore hits that are outputs you are about to create.) If a checks file is missing, say so and use the checks in this skill; do not report a walkthrough that did not happen.

## Step 1: confirm the GPU, before anything long

```
node gpu_check.cjs        # exit 0 hardware, 2 software or no WebGL
```

It launches headed Chromium, reads `chrome://gpu` through its shadow DOM, and independently asks a WebGL context for `UNMASKED_RENDERER_WEBGL`. Expect something like `ANGLE (NVIDIA ..., NVIDIA GeForce GTX 1080/PCIe/SSE2, OpenGL 4.5.0 ...)` and `WebGL: Hardware accelerated`. A renderer containing `SwiftShader`, `llvmpipe` or `Software` means a full render takes hours (the bundle's own docs say about 50 times slower; not measured here): stop and tell the person instead of starting it.

**Do not use the common one-liner** `page.goto('chrome://gpu'); page.content().match(/WebGL: [^<]*/)`. `chrome://gpu` builds its report in shadow DOM, so `page.content()` has no `WebGL: ...` text and the match returns `undefined`. That `undefined` is a regex that matched nothing. It does **not** mean "no GPU" and it does not mean "GPU fine". It happened on this run. Also, the sentence "Software only. Hardware acceleration disabled" appears on the page as a legend entry, not as a status.

Run headed (the default). Headless Chromium often falls back to software rendering without saying so. Do not pass `--swiftshader` unless this step showed no GPU at all, and do not pass `--headless` unless you have confirmed headless still gets the GPU.

## Step 2: estimate the run before starting it

Measured on a GTX 1080 with a Ryzen 5 2600X, frames 2560x1440 (1280x720 CSS at `--dsf 2`), JPEG quality 94:

| Measurement | Value |
|---|---|
| Whole film, 11,541 frames at 30 fps | 8.2 fps average, 23.4 min |
| A 10-second range, 300 frames | 7.9 to 8.9 fps printed, 43 s wall including start-up |
| A 1-second range, 30 frames | 10.7 s wall (start-up dominates) |
| First 56 s (scenes 1 and 2) | 10.1 fps; rate varies by scene, plan for plus or minus 20% |
| Disk, frames directory | 6,880,169,213 bytes for 11,541 frames (about 0.6 MB each) |

Estimate: minutes = film_seconds x fps / (8.2 x 60) on this class of machine. Tell the person the estimate and the disk need before you start. Film seconds come from `timeline.json`; frame count is `round(seconds x fps)`.

## Step 3: smoke test a range

```
node capture.mjs --page page/index.html --seek seek.js --css video.css --start '#startBtn' \
  --ready "typeof THREE!=='undefined' && typeof SCENES!=='undefined'" \
  --after-setup "setQuality('high', true)" --route '**/three.min.js=vendor/three.min.js' \
  --timeline timeline.json --seed 1 --from 55 --to 65 --out /tmp/smoke
```

(The selectors, globals and route are the original page's; substitute yours.) It prints the frame range, frames per second and an ETA. Report the fps to the person.

**Frames are numbered by absolute film position**, `frame = round(seconds x fps)`. `--from 55` at 30 fps starts at `f001650.jpg`, not `f000000.jpg`. Do not look for frame 0 in a range test, and do not carry frame numbers from one range or frame rate to another. Open at least three frames and check for the things you expect (dark page, title bar, timecode bar) and the things you stripped (caption text, buttons, play button). A range that crosses a scene cut should also show a dip, which `check_cuts.py` verifies in step 5.

`--timeline` makes the capture abort if the page's scene durations do not match the timeline's; otherwise the audio would drift out of sync with no error.

## Step 4: the full capture

Same command without `--from/--to`, output to `frames/`, run once and let it finish:

```
node capture.mjs ... --seed 1 > capture.log 2>&1
```

- **Resume and staleness.** Existing frames are skipped, so an interrupted run resumes by re-running the same command. The same rule means frames left from an older page, CSS or flags are silently reused. Use a clean `--out` whenever anything changed.
- **Page errors.** Only uncaught page exceptions are printed (`PAGEERROR`). Console errors, warnings and failed requests are not captured; "no errors logged" is narrower than it sounds.
- **A launch once failed with a bare Playwright `Error` and succeeded on an identical rerun**; the message was not recorded. Rerun once before investigating.

### Reproducibility: seed the page's randomness

Measured on the original page: two renders of the same frame in separate page loads differ (mean absolute difference about 12 of 255, about 23% of pixels more than 8 levels off). Cause: the page calls `Math.random()` unseeded in 54 places (particle layouts and spreads) and nothing seeded it. The bundle's own text claimed output was "frame-exact and identical on every machine"; that held only within one page load.

`--seed N` replaces `Math.random` with a seeded generator before any page script runs. Tested on one scene:

| Comparison | Result |
|---|---|
| same seed, two separate page loads, 30 frames | 27 of 30 byte-identical; the other 3 are the first 3 frames after a cold start, at most 0.4% of pixels differ |
| different seeds | every frame differs (mean difference about 11.7) |
| capture from 0 vs capture started at 55 s, same seed, 30 frames | 26 of 30 byte-identical; the others differ by at most 0.6% of pixels |

So with a seed, a resumed or partial capture matches an uninterrupted one closely on the scene tested; without it, a resume part-way through a scene re-rolls that scene's layout and the film pops at the resume frame. Use `--seed` on every new render, and look at the frames around any resume point. The seed changes which random layout you get; it does not make one better than another.

## Step 5: checks (run all of them, report each result)

1. **Frame count.** `ls frames | wc -l` equals `round(total_seconds x fps)` (11,541 here). `encode.sh` also checks that numbering is contiguous and fails at the first gap. Without that check ffmpeg stops at the first missing number and writes a short video (tested: a gap at frame 12 gave 12 frames); the only sign is one `Input/output error` line in a long log.
2. **Scene cuts, computed not remembered.**
   ```
   python3 check_cuts.py --frames frames --timeline timeline.json --fps 30
   ```
   For each scene boundary it computes `round(cumulative_seconds x fps)` from the timeline, looks at +-8 frames, and reports the darkest frame, its offset from the computed cut and its mean luminance. If the page dips to black at cuts, the darkest frame must sit within 2 frames of the computed cut (here: every cut at offset 0 and mean luminance 7.0, against 9 to 94 twenty frames earlier). `--probe N N ...` prints the luminance of specific frames.
3. **Sync.** `ffprobe` the video and audio stream durations; they should agree within a frame (384.700 s vs 384.703 s here). If they drift, a scene duration in `timeline.json` differs from the page's.
4. **Look at it.** Three frames are not a review. Say which frames were viewed; say that the film was not watched if it was not.
5. **Stutter at scene openings** is a thing to look for around each cut; this run did not check it.

### Two mistakes to not repeat

- **Hand-written expected frame numbers.** An expectation of a dip at frames 476 to 482 came from a test at a different frame rate and was applied to this timeline. Those frames are flat (mean luminance 20.0 to 20.1) and the first real cut is at frame 1014. Frame numbers belong to a timeline and a frame rate; compute them with `check_cuts.py` every time, and quote them together with the fps they assume.
- **The `chrome://gpu` one-liner** (step 1).

## Step 6: encode

```
./encode.sh --frames frames --timeline timeline.json --audio-dir clips --out film-1080p.mp4 --fps 30 --w 1920 --h 1080
./encode.sh --frames frames --timeline timeline.json --audio-dir clips --out film-720p.mp4  --fps 30 --w 1280 --h 720
```

`encode.sh` always rebuilds the narration from the timeline and clips unless `--narration FILE` is passed. (The original bundle script reused a leftover `narration.m4a` if present, which would silently ship stale audio after a clip changed.) Video is `libx264 -preset slow -crf 18 -pix_fmt yuv420p -profile:v high -level 4.1 -movflags +faststart`, audio `-c:a copy`, frames scaled with `lanczos`. Each extra resolution costs one more encode from the same frames, not another capture.

| Output | Encode wall time | Size |
|---|---|---|
| 1080p, 384.7 s, 11,541 frames, preset slow | 5 min 10 s (36.7 min CPU) | 438,352,823 bytes, video 8.99 Mb/s |
| 720p, same frames | not timed for the full film (a test at `--preset fast` ran at about 60 fps) | 204,158,412 bytes, video 4.11 Mb/s |

Audio in both: AAC-LC, 48 kHz, stereo, about 122 kbps. The per-clip stage re-encodes clips (`apad -t <dur> -ar 48000 -ac 2 -c:a aac -b:a 128k`), so the track in the film is a second lossy generation of the source clips.

For test ranges use `--start-number` and `--expect-frames` with the same absolute numbering the capture used.

## Known traps

- **Stale frames reused** after any page, CSS or flag change (step 4).
- **Unseeded `Math.random`** (step 4).
- **`ffmpeg` inside a `while read` loop eats the loop's stdin**: use `-nostdin`. Fixed in `build-audio.sh`; relevant if you write another loop.
- **Frame numbers are absolute** (step 3).
- **Durations in three places** must agree: the page's scene durations, `timeline.json`, and the clips (a clip must not be longer than its slot). `capture.mjs --timeline` and `build-audio.sh` enforce two of those.
- **The seek shim and stylesheet are page-specific.** The examples are the original page's globals and selectors; they will not run on another page unchanged.

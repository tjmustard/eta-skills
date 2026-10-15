---
name: "page-to-video"
description: "Record a timed, animated web page to a narrated video file: deterministic frame capture, audio track assembly, and verification of the result. Use when turning an animated page, explainer or dashboard into an MP4."
---

# Page to video

Turn a timed, animated page into a narrated video by driving it frame by frame against a clock you control, not by screen recording.

This is the planning and packaging half. If the render runs on another machine, that machine wants a skill of its own carrying its real commands and measured throughput.

## Measure before you design the render

Render cost decides the whole approach, so measure it before committing.

```js
await page.evaluate(() => window.__seek(12.0, 30));
const ms = await page.evaluate(() => {
  const t0 = performance.now();
  renderer.domElement.toDataURL('image/jpeg', 0.5);   // forces the readback
  return performance.now() - t0;
});
```

A seek returning in single-digit milliseconds means nothing has rasterised yet: WebGL commands queue and cost nothing until a readback forces them. The `toDataURL` number is the true per-frame cost.

Weight it across scenes by duration and multiply by `duration x fps`. Measured reference points for a dense WebGL page at 2560x1440:

| Where | Throughput |
| --- | --- |
| Software rasteriser, no GPU | about 1.2 frames per second |
| GTX 1080, headed Chromium | 8.2 frames per second |

For a six-minute film at 30 fps that is most of an afternoon against 23 minutes. If there is no GPU, **do not render there.** Resolution is a weak lever: halving it typically buys under a third, because most of the per-frame cost is fixed. Package a bundle and let it run where there is hardware. Budget disk too: those frames took 6.9 GB.

## Seed the page's randomness

A page that calls `Math.random()` while building scenes is not reproducible across page loads, and stepping the clock by hand does not fix that. Geometry is usually built once when a scene is first shown, so a single uninterrupted run is self-consistent and looks fine. A **resumed** run rebuilds whatever scene it restarts inside, re-rolls that layout, and pops on screen at the resume frame.

Inject a seeded generator over `Math.random` before any page script runs, and pass the same seed on every capture of the same film. Measured on a page with 86 unseeded call sites: unseeded, two renders of one frame differed across about 23% of pixels; seeded, 27 of 30 frames across separate page loads were byte-identical.

Never claim frame-exact output without having tested it across two page loads.

## Determinism

Replace the live animation loop with a clock you step by hand. Inject after the page has started:

```js
window.__setup = function(){
  playing = false;
  window.__starts = [];
  let a = 0; for (const s of SCENES) { window.__starts.push(a); a += s.dur; }
  window.__seek = function(gt, fps){
    let i = 0;
    while (i < SCENES.length - 1 && gt >= window.__starts[i] + SCENES[i].dur) i++;
    if (i !== idx) { idx = i; showScene(i); }
    elapsed = Math.min(Math.max(gt - window.__starts[i], 0), SCENES[i].dur);
    clock.elapsedTime = gt;
    clock.getDelta = () => 1 / (fps || 30);
    tick();                              // renders exactly once
  };
  window.requestAnimationFrame = () => 0; // kill the live loop
};
```

**This only works if scene updates are pure functions of progress and time.** A scene accumulating state per frame cannot be seeked and will drift.

Name frames by absolute film position, `frame = round(seconds x fps)`, so partial runs merge. Say so in the instructions: `--from 55` at 30 fps writes `f001650.jpg` first, not `f000000.jpg`.

**Frame numbers belong to a timeline and a frame rate.** Never carry an expected frame number from a test at one frame rate into instructions for another. Compute cut positions from the scene durations every time, and quote them with the fps they assume.

## Confirming the GPU is actually in use

The failure is silent and costs an order of magnitude, so check before anything long.

**Do not read `chrome://gpu` with `page.content()`.** That page builds its report in shadow DOM, so the text is not in the returned HTML and a regex match returns `undefined`. Read as "no GPU" it would send you to a software render for no reason. The page also contains "Software only, hardware acceleration disabled" as legend text rather than status, so string matching misleads in both directions.

Query the WebGL context directly instead:

```js
const r = await page.evaluate(() => {
  const gl = document.createElement('canvas').getContext('webgl');
  const d = gl.getExtension('WEBGL_debug_renderer_info');
  return gl.getParameter(d.UNMASKED_RENDERER_WEBGL);
});
```

A real GPU name means hardware. `SwiftShader`, `llvmpipe` or `Software` means stop and say so. Run headed; headless Chromium often falls back to software without saying so.

## Hiding the interface

Inject video-mode CSS rather than editing the page, so the page stays shippable:

```css
#captions, #buttons, #playButton, #titleCard { display: none !important; }
```

Inject it **after** clicking through any title card, or the control you need to click is already hidden.

Keep a progress bar if there is one. It reads as deliberate and orients the viewer.

## Resolution

Render at the viewport width the interface was laid out for, with `deviceScaleFactor: 2`, and downscale at encode. A HUD laid out in fixed pixels and composed at 1280 wide looks shrunken if the viewport is widened to 1920; supersampling gives the same composition with crisp type. Extra output resolutions cost one more encode from the same frames, not another capture.

## Scene cuts

Drive any crossfade per frame from the seek function, with CSS transitions disabled. A short dip to black, about 0.2 s, reads far better than a hard cut.

Watch for elements referenced by a JavaScript binding rather than an id: `getElementById` on an element that never had an id returns null and the fade silently does nothing.

## Audio

Build the track to match the video by construction. Pad each clip with silence out to its scene's on-screen duration, then concatenate:

```bash
ffmpeg -nostdin -i scene-$n.m4a -af apad -t $DURATION -ar 48000 -ac 2 -c:a aac -b:a 128k part-$n.m4a
ffmpeg -f concat -safe 0 -i list.txt -c copy narration.m4a
```

**Always rebuild the track; never skip the build because a file exists.** A guard like `[ -f narration.m4a ] || build-audio.sh` silently ships yesterday's audio after a clip changes. Use `-nostdin` on any ffmpeg inside a `while read` loop, or it eats the loop's input.

The result should equal `sum(scene durations)` to within a few milliseconds. Two things this stage does, worth stating rather than discovering: it is a second lossy generation, so the audio in the film is not the delivered bitstream; and `-ac 2` on mono clips costs 3 dB of per-channel sample peak to ffmpeg's rematrix while leaving integrated loudness unchanged, because EBU R128 sums both channels.

## Verify what comes back

Never accept a render because it played.

- **Frame count** equals `round(duration x fps)`. Check numbering is contiguous, not just that the count is right: ffmpeg's image sequence reader stops at the first missing number and writes a short file, and the only sign is one `Input/output error` line in a long log.
- **A/V drift**: compare video and audio stream durations. Tens of milliseconds is fine, a second is a bug.
- **Scene cuts land where the timeline says.** Compute each boundary from the durations, look a few frames either side, and confirm the darkest frame by mean luminance.
- **Spot frames** across the whole film for stray interface elements and half-built scenes. Three frames is not a review; say which frames were looked at, and say plainly if the film was never watched.
- **Frames around any resume point**, which is where unseeded randomness shows.

Hook `console` errors and failed requests as well as `pageerror`. An uncaught-exception hook alone misses a texture that failed to load, so "no errors logged" is narrower than it sounds.

## Lint the bundle before shipping it

Every file a bundle's instructions name must exist in the bundle. A checks file that is referenced but missing gets the checks skipped or improvised, and the report comes back saying a walkthrough happened that did not.

```bash
grep -ohE '`[A-Za-z0-9_./-]+\.(md|json|sh|mjs|js|css|html|py)`' *.md \
  | tr -d '`' | sort -u | while read -r f; do [ -e "$f" ] || echo "NOT FOUND: $f"; done
```

## Encoding

`libx264 -preset slow -crf 18` for a master, `-crf 23` for distribution. Always `-pix_fmt yuv420p -movflags +faststart`.

Dense procedural detail does not compress. If a file is large that is usually honest rather than a wrong setting; check what a smaller encode actually destroys before recommending it. Note that `ls -lh` prints MiB, so a file it calls 419M is 438 MB decimal, and the two get quoted interchangeably.
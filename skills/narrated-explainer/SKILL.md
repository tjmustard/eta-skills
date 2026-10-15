---
name: "narrated-explainer"
description: "Build a narrated, scene-based explainer page that plays like a short film: timed WebGL or canvas scenes, voice-over, a scrub bar, and deep-dive panels. Use for interactive explainers and animated walkthroughs of a process."
---

# Narrated explainer page

One HTML file that plays like a short documentary: timed scenes, voice-over, a scrub bar, and optional panels that go deeper than the narration. The file is the deliverable; audio sits beside it and loads per scene.

## Order of work

Reordering these is the most common way the project goes wrong.

1. **Research, and write down the sourcing rules.** Before any script, settle what is public, what is not, and what the piece may not contain: photographs it cannot license, real identifiers, claims no source supports. Those rules constrain every later decision, so they are worth stating explicitly and confirming.
2. **Write the script and the panels.** Two reading levels: narration pitched at someone who has not studied the subject, panels free to be technical. Keep them as separate markdown files so the narration can go to a TTS pipeline unchanged.
3. **Build a scaffold before any real scene.** A skeleton with placeholder scenes, the real HUD and the real timing. Put it in front of the person and stop. Judging scene content in prose is slower and worse than judging it on screen, and content decisions made against a running page are better decisions.
4. **Build scenes one at a time**, reviewing by contact sheet.
5. **Generate audio last**, once the script has stopped moving. Audio is the expensive, least reversible step.
6. **Retime the page to the audio**, never the reverse.

## The scene contract

Every scene is a function returning the same shape. Nothing outside a scene knows what is inside it.

```js
builders.sceneName = function(){
  const g = new THREE.Group();
  // build geometry once, here
  return {
    group: g,
    update(p, t){ },              // p = 0..1 progress, t = scene time; called once per frame
    cam(p){ return {pos:[x,y,z], tgt:[x,y,z], fov:42}; },
    readout(p){ return 'html or null'; },   // the figures in the corner
    annos: [{ v: vec3, el: domNode, show: p => p > 0.6 }]   // labels tracking 3D points
  };
};
```

**`update(p, t)` must be a pure function of `p` and `t`.** No accumulated state between frames. This is what lets the page be scrubbed, seeked and recorded frame by frame; a scene that integrates velocity each frame cannot be rendered to video deterministically and cannot be scrubbed backwards.

A single `SCENES` table holds duration, title, caption, builder name and panel list for each scene. Timing, the scrub bar and the narration all read from it.

## Architecture

The deliverable is one file, but editing a 150 KB file is miserable. Author it as fragments concatenated in a fixed order, so an edit touches 10 KB:

```
cat part1.html part2.html part3.html ... > page.html
```

A workable split: markup and CSS; the scene table and panel content; the engine and the first scenes; further scene groups; post-processing; and the app shell (scene lifecycle, narration, transport, camera) concatenated **last** so everything it references is defined.

After every concatenation, syntax-check before rendering. Extract the inline scripts and run them through `node --check`. Generated code acquires typos that cost a full render cycle to find otherwise.

## Engine choices that are not obvious

- **Pick a three.js build that matches the host.** Artifact and CSP-constrained hosts often cannot use ES modules without an import map. r160.1 is the last release shipping a UMD `build/three.min.js`. Check before assuming the newest version works.
- **Post-processing may be unreachable.** three's bloom and composer are ES-module-only. From a UMD build, write the pass by hand: an HDR half-float target, a soft-knee bright pass, separable blur at half and quarter resolution, then one composite shader doing tone mapping, vignette and sRGB encode.
- **Generate the environment map procedurally.** A gradient dome plus two or three emissive planes rendered into an offscreen scene and prefiltered with `PMREMGenerator`. Without an environment, metals render black. It costs zero bytes on disk.
- **Draw everything; ship no images.** Procedural geometry and shaders keep the page small enough to be one file, and keep it sharp at any resolution.

## The review loop

Drive the page with Playwright, step to a chosen moment in each scene, screenshot, and composite the frames into one contact sheet. Then look at the sheet.

This is what catches the bugs that matter, and they are rarely where the symptom points: labels stretched into a viewport corner by a CSS selector meant for something else, objects floating just off the surface they should sit in, a custom shader silently losing its depth test. None of these are visible in code review.

When a camera or lighting change is requested, re-shoot the same frames and compare. Crops and thumbnails lie about framing; check at full size before concluding a scene is wrong.

## Quality tiers

Agree a performance floor as a real device, not an adjective. Offer two tiers with a visible toggle, and auto-demote on measured frame time (median over ~120 frames). Keep a separate resolution scale as a second safety valve, so a slow device can shed pixels without losing content.

Switch tiers by uniform and visibility flags, not by rebuilding scenes, so the toggle is instant.

## Citations

Give each claim a source key, and give the keys that are not external sources their own marks: one for arithmetic worked out for the page rather than published, one for general background. A piece that labels its own reasoning is more trustworthy than one that cites everything uniformly.
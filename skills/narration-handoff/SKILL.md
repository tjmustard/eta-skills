---
name: "narration-handoff"
description: "Hand a narration script to a text-to-speech run that happens elsewhere, then verify what comes back. Use when generating voice-over outside the session, or when re-recorded audio needs checking for actual change."
---

# Narration handoff

For voice-over generated outside this session: on a local machine with open-source TTS, by a person in a booth, or by any pipeline you do not control. Two jobs: write a brief that works with no other context, and verify what comes back.

## Generate audio last

Audio is the most expensive and least reversible step in a narrated piece. Every edit to the script invalidates a recording. Hold it until the text has stopped moving, even when the script feels nearly done. Most of the churn in these projects traces back to recording too early.

## What to hand over

Two files, and nothing that assumes prior context. The receiving session starts cold.

**A lines file**, one entry per segment:

```json
{ "id": "scene-01", "n": 1, "title": "Cold open",
  "target_seconds": 33.8, "text": "Most pills you have ever taken..." }
```

Regenerate `target_seconds` whenever the script changes. Stale targets make the returned durations table pure noise, and it is the table you retime from.

**A brief.** The instructions that carry weight, in rough order:

1. **Use the `text` field verbatim.** It matches on-screen captions word for word. Do not reword, re-punctuate or expand abbreviations.
2. **Check current install instructions before starting.** Say plainly that your knowledge of these packages may be out of date and the project README wins over anything in the brief about package names, flags or model filenames.
3. **Engine preference order, stop at the first that works**, with a reliable CPU fallback named. Ask it to record which engine, model and voice it settled on.
4. **Render a few voices on one segment and let the person choose**, rather than picking one. Voice is a taste decision and costs a minute to make properly.
5. **One voice, one set of settings, all files.** If a file is regenerated later, regenerate it with identical settings.
6. **Normalise loudness** across all files, around -16 LUFS integrated for spoken web audio, with a true-peak ceiling. Trim leading and trailing silence, then add back about 150 ms of lead-in so playback does not clip the first syllable.
7. **Fix mispronunciations with the engine's phoneme override, never by editing the text**, because the audio has to stay identical to the captions.
8. **Listen to the named segments before declaring it done.** Name them specifically. See below: this is the instruction most likely to be skipped.
9. **Build it as a single re-runnable script** with the output set versioned in both the folder name and the filename.
10. Ask for a durations table: id, title, target, actual, delta.

Write numbers as words in the script itself ("thirty two million", "ten to the sixtieth"). Doing it in the text rather than asking the engine to handle it removes a whole class of failure.

For scale: a small local model on CPU synthesises around 17 scenes of documentary narration in a few minutes, so regeneration is cheap and worth asking for whenever the text changes.

## Verify what comes back

### Hash at the source, not at the destination

Ask for hashes computed on the generating machine, before upload, alongside the files. The destination can only tell you that something is wrong, never what. Files silently failing to update is the single most common failure in this handoff and it costs hours if diagnosed by ear.

### Duration proves nothing, and neither does one hash

A deterministic pipeline fed the same text produces the same length, so two files can match in duration and be different recordings, or be the same recording twice. Hash twice per file:

```bash
md5sum scene-16.m4a
ffmpeg -v error -i scene-16.m4a -f s16le -ar 16000 -ac 1 - | md5sum
```

The first catches a file never replaced. The second decodes to raw PCM first, so it catches a file re-encoded from the same source: different bytes, identical speech. Only when both differ has anything been re-recorded. Report per file, by name, so the sender can see which specific files did not come through.

### Neural TTS is not bit-reproducible, and that is useful

Re-synthesising identical text with identical settings generally gives the same length but different samples. So byte-identical output across a regeneration is not evidence the engine is cached or repeatable. It is proof the generation step did not run for those files.

The usual causes, worth naming when you report the problem: a `--only`-style flag skipping scenes, a reuse-cached-intermediate flag, output written to a versioned folder different from the one being uploaded, or a manual rename sitting between the build output and the uploaded filenames. Non-clobbering renames (`mv -n`) are especially good at leaving stale files that look current.

### Measuring is not listening

Loudness, peak and duration can all be correct while the narration says the wrong thing. Mispronounced numbers, units and technical terms pass every measurement. If the brief asked for specific segments to be checked by ear, confirm that happened; it is routinely skipped because the measurements look like verification.

### Loudness: compare like with like

Check each clip with `ebur128`. Spoken web audio wants about -16 LUFS integrated; the spread between clips matters more than the absolute value.

Measure the delivered clips, not a downstream mux. A mono clip upmixed with `-ac 2` loses 3 dB of per-channel sample peak to ffmpeg's rematrix while its integrated loudness stays identical, because EBU R128 sums both channels. Measuring the mux and the clips will give different peaks for the same audio, and the difference is not a bug.

## Retime to the audio

Set each segment's on-screen duration to its clip length plus a short tail, around 0.8 seconds, so a scene does not cut on the last syllable. Update any total-duration text in the interface, which is easy to leave stale.

## Container and format traps

Check what the destination actually serves before asking for a format. Some hosts refuse `.m4a` while serving `.mp4` happily, and the two can hold the identical AAC stream, so renaming is enough and no re-encode is needed.
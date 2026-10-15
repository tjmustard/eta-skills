---
name: "build-walkthrough"
description: "Turn a finished agent-assisted project into a published walkthrough plus the skills that let someone reproduce it. Use when documenting how something was built, writing up your own work as a case study, or packaging a workflow so other people can run it."
---

# Build walkthrough

Turn work that is already done into something another person can learn from and repeat. The output is two linked things, published together:

- **A walkthrough**: what was built, what the decisions were, what broke and where the cause actually was.
- **Skills**: the executable procedure, as instructions an agent loads at the point of use.

They are not two formats for the same content. Keep the split clean and both stay useful.

## The split

For each thing you want to say, ask what it does for the reader.

| If it... | It belongs in |
| --- | --- |
| Tells you what to do next time | A skill |
| Tells you why it went the way it did | The walkthrough |
| Is a command, a parameter, a threshold | A skill |
| Is a decision, a trade-off, a dead end | The walkthrough |
| Is a measurement someone should plan against | Both: the number in the skill, the story of getting it in the walkthrough |

A walkthrough that carries the procedure goes stale and nobody runs it. A skill that carries the story is unreadable at the moment someone needs it.

## Harvest before you write

**The prompt history is the spine.** Pull every instruction from the transcript, in order, verbatim. Trim long ones to the operative sentence and mark the trim, but never paraphrase: what teaches is the exact wording, especially the short prompts that changed the project's direction and the corrections that followed a wrong turn. A paraphrase smooths off precisely that.

**Inventory the artifacts.** List every file the project produced and what can be measured from it. Those measurements are the walkthrough's evidence.

**Mark the handoffs.** Anything that crossed a boundary: another machine, another session, another tool, another person. Do this before writing, because of the next section.

## Look at the boundaries first

Nearly every real lesson lives at a handoff. Inside one session with one set of tools, things mostly work. Across a boundary they do not, and the failures are the interesting part because they are invisible from either side alone.

What tends to go wrong there, and what to go looking for:

- Files that did not actually change, in a pipeline where the sender believes they did.
- A measurement taken on the wrong artifact, so two sides report different numbers for the same thing and both are right.
- A claim that holds within one process and fails across two.
- Instructions referencing a file that never shipped.
- A number carried from one configuration into another where it means something else.

If the writeup has no failures in it, you have either not looked at the boundaries or you are writing marketing.

## Interrogate the sessions you cannot see

When part of the work ran somewhere you have no access to, the only way to document it is to ask. Send a written brief, not a question in passing. Four things make the difference between a useful answer and a plausible one:

1. **Permit "not recorded" explicitly**, and say that a wrong specific is worse than a blank. Without that instruction, a session reconstructs from defaults and from what it would have chosen, and the reconstruction comes back reading exactly like a verified fact.
2. **Ask for exact strings**: versions, model identifiers, filenames, flags, whole commands. Not descriptions of them.
3. **Ask it to confirm or correct your inferences, not just to report.** State the inference and the evidence behind it. A question framed "report X" gets X. A question framed "I concluded X from Y, check it" gets the correction when you are wrong, and both of the significant corrections in a writeup usually arrive this way.
4. **Name the specific puzzle you want solved**, the one thing you could not work out from your side, and say it is the most useful answer in the list. Otherwise it gets the same weight as the version numbers.

## Verify every number against an artifact

This is the whole difference between a walkthrough and a blog post. Before a figure goes in, measure it: probe the file, hash it, count the occurrences, run the arithmetic. Recalled numbers drift, and a writeup is read by people who will act on it.

This applies to claims **about your own work** as well. When the other side reports a defect in something you built, check it against the file before accepting it, and say that you did. It cuts both ways: an inference of yours that the other side disproves belongs in the writeup as a correction, with the mechanism that explains how both measurements were right.

When a figure is inference rather than observation, label it, then actively look for the thing that would disprove it.

## Write the defects in, by name

List what broke. For each one give the symptom as it appeared and the cause as it turned out to be, because the distance between them is usually the lesson: a visual glitch caused by a depth buffer setting, silent audio caused by a trailing slash, an unreproducible render caused by an unseeded random call.

Include your own. A walkthrough whose author's work has no defects in it teaches nothing and reads as a sales page. The ones worth the most space are the defects that looked fine from the inside and were caught from the outside.

Leave open items open. Unresolved claims, steps nobody verified, things still needing a human. Mark them as unresolved rather than quietly dropping them, and say what would close each one.

## Shape of the document

Lead with what was built and its hard numbers, so a reader deciding whether to read on can decide.

Then, roughly: the constraints that governed everything downstream; a section per phase in the order the work happened; the prompt history as one table in order; the defects; the sources. If work crossed machines or tools, draw the pipeline, with the handoffs labelled by what crossed. A reader takes that in at a glance; a paragraph describing it makes them rebuild it in their head.

What to leave out: a turn-by-turn narration of the conversation, anything written as a success story, and any number you did not measure.

## Write the companion skills where they will run

A skill has to live where its commands work. Anything needing hardware, an install, or credentials that one environment does not have belongs to the environment that has them, and that is usually also the only place that knows the real parameters.

So ask the session that did the work to write its own skill, from what it actually did. Two instructions matter in that ask:

- **Leave out what you would be guessing at.** A short skill that is true beats a thorough one that is half invented, and a session writing a skill will otherwise fill gaps with general knowledge that reads as verified.
- **Ship the working scripts as files beside the skill**, not pasted into the markdown. A skill carrying a runnable script is reusable; one that describes the script in prose means writing it again.

Then strip the project out: paths, filenames, counts, subject matter. Say what varies and where to change it. A skill that only works on the project it came from is a diary entry.

## Publishing them together

The walkthrough and the skills are one package and should arrive as one.

- Each phase section in the walkthrough names the skill that covers it, and links to it.
- The skills are downloadable as a folder, and readable without downloading.
- One entry point says what to run first to reproduce the work.
- Anything a reader would need that is not in the package, say so plainly rather than letting them find out.

If this is going somewhere public, decide indexing deliberately rather than inheriting a default, and check what the work is allowed to disclose before it ships.
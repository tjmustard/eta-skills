<div align="center">
    <img src="./media/logo.webp" alt="eta-skills logo" width="200" height="200"/>
    <h1>eta-skills</h1>
    <h3><em>Agent skills for research planning, software design, writing, and agent evaluation.</em></h3>
</div>

<p align="center">
    <strong>Each skill follows the Agent Skills specification, and the repo doubles as a Claude Code plugin marketplace, so one copy of each skill installs in Claude Code, other skills-compatible clients, and claude.ai.</strong>
</p>

<p align="center">
    <a href="https://github.com/tjmustard/eta-skills/stargazers"><img src="https://img.shields.io/github/stars/tjmustard/eta-skills?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/tjmustard/eta-skills/blob/main/LICENSE"><img src="https://img.shields.io/github/license/tjmustard/eta-skills" alt="License"/></a>
</p>

---

## Table of Contents

- [🤔 What is eta-skills?](#-what-is-eta-skills)
- [📚 Skills](#-skills)
- [⚡ Get Started](#-get-started)
- [📂 Directory Structure](#-directory-structure)
- [🛠️ Adding a Skill](#️-adding-a-skill)
- [❓ Troubleshooting Overview](#-troubleshooting-overview)
- [🤝 Support](#-support)
- [📄 License](#-license)

## 🤔 What is eta-skills?

A single repository of **agent skills** for research planning, software design, writing, and agent evaluation. Every skill conforms to the [Agent Skills specification](https://agentskills.io/specification) and is validated in CI. Skills are grouped into **bundles** (Claude Code plugins) listed in `.claude-plugin/marketplace.json`, so each skill exists once and is installable everywhere.

## 📚 Skills

<!-- catalog:start -->
| Skill | Bundle | Description |
| --- | --- | --- |
| [adversarial-agent-hardening](skills/adversarial-agent-hardening) | agent-eval | Iteratively harden agents, skills, instructions, and tool calling schemas using a generate-critique-patch loop with independent audits, up to fixed pass, time, and run limits. Use when the user wants to stress-test, evaluate, red-team, or refine agent prompts, tool signatures, or workflows. |
| [article-interviewer](skills/article-interviewer) | writing | Interview the user section by section to turn their outline into a finished article, blog post, or social post in their voice, drafting 2–3 versions of each section for them to choose from, then run a full-article flow edit with an itemized change list. Use when the user has an outline and wants to be interviewed, asked questions per section, or co-write an article, blog post, essay, newsletter, or LinkedIn post from it. When the user has only a topic or rough notes, the article-outliner skill comes first. |
| [article-outliner](skills/article-outliner) | writing | Help the user turn a topic, idea, or rough notes into an approved article outline with a thesis, context, and section-by-section plan, formatted for the article-interviewer skill. Use when the user wants to outline, plan, or structure an article, blog post, essay, newsletter, or LinkedIn post, or has an idea or notes but no outline yet. When the user already has an outline and wants to start writing, use article-interviewer instead. |
| [build-walkthrough](skills/build-walkthrough) | media | Turn a finished agent-assisted project into a published walkthrough plus the skills that let someone reproduce it. Use when documenting how something was built, writing up your own work as a case study, or packaging a workflow so other people can run it. |
| [comment-drafter](skills/comment-drafter) | writing | Draft 2–3 short comment options for someone else's LinkedIn post that connect it to the user's own beliefs and experience instead of generic praise. Use when the user pastes a LinkedIn or other social post, optionally with background such as a paper abstract or news article, and wants help commenting on it or replying, for example "help me comment on this", "what should I say on this post", or "draft a reply". Not for writing the user's own posts or articles; use article-interviewer for those. |
| [cross-model-judge-eval](skills/cross-model-judge-eval) | agent-eval | Evaluate, score, and benchmark agent outputs, skills, and code using an ensemble panel of heterogeneous LLMs from different model families. Use when assessing agent reliability across frontier and open-source models, mitigating single-model evaluation bias, or running jury/consensus-based quality gates. |
| [narrated-explainer](skills/narrated-explainer) | media | Build a narrated, scene-based explainer page that plays like a short film: timed WebGL or canvas scenes, voice-over, a scrub bar, and deep-dive panels. Use for interactive explainers and animated walkthroughs of a process. |
| [narration-handoff](skills/narration-handoff) | media | Hand a narration script to a text-to-speech run that happens elsewhere, then verify what comes back. Use when generating voice-over outside the session, or when re-recorded audio needs checking for actual change. |
| [page-to-video](skills/page-to-video) | media | Record a timed, animated web page to a narrated video file: deterministic frame capture, audio track assembly, and verification of the result. Use when turning an animated page, explainer or dashboard into an MP4. |
| [prompt-engineer](skills/prompt-engineer) | writing | Act as the user's prompt engineer — collaboratively design and refine a prompt for an AI model through short iterative rounds, each delivering a "Revised Prompt" plus "Questions", until the user confirms it's done. Use this whenever the user wants help writing, improving, tightening, or structuring a prompt, system prompt, persona, or instruction set for Claude, ChatGPT, Gemini, or any other LLM — including "help me write a prompt for X", "make this prompt better", "what's wrong with my prompt", or "act as my prompt engineer" — even when they only vaguely describe what they want the model to do. Not for building Claude skills (use skill-creator), and not for doing the task itself instead of writing the prompt for it. |
| [render-page-to-video](skills/render-page-to-video) | media | Use when you need to render a timed, animated WebGL or canvas web page to a narrated MP4 by capturing it frame by frame with Playwright, and you want the GPU check, throughput numbers, frame-numbering rules and verification steps that already worked. |
| [research-partner](skills/research-partner) | research | Work as the user's peer co-researcher on a technical or scientific project, challenging assumptions, reasoning from first principles, stating confidence, never inventing sources, and keeping a Living Master Plan file (objectives, hypotheses and architecture, next steps, constraints and open questions, and a Graveyard of failed attempts) current across sessions. Use when the user starts or resumes a research or engineering project and wants a critical collaborator, asks for the project plan or its status, or invokes /research-partner with status, deepdive, newcommand, or a custom command. Not for one-off questions that need no ongoing plan. |
| [taste-interviewer](skills/taste-interviewer) | writing | Run or resume the Taste Interviewer, a 100-question, one-question-per-turn interview that extracts how the user thinks, writes, and perceives the world into taste-master.md, the raw record that will later become the instructions for an AI that writes in their voice. Use this whenever the user wants to start, continue, or resume the taste interview; attaches taste-master.md and/or writing samples and asks to be interviewed about their writing, voice, or taste; or mentions the Taste Master Document, voice DNA, aesthetic crimes, hard nos, red flags, or rewrite tests, even if they never say the word skill. Do not use it to write in the user's voice or to synthesize taste-master.md into a style guide; that is a separate skill. |
| [tts-narration-build](skills/tts-narration-build) | media | Use when you need to turn a JSON of scene texts into loudness-matched narration audio files with local open-source TTS (Kokoro), and you want the install, settings, ffmpeg chain, versioning rule and verification steps that already worked. |
| [voice-card-builder](skills/voice-card-builder) | writing | Turn the user's taste interview (taste-master.md from the taste-interviewer skill) and samples of their writing into a voice card, an installable skill that makes an AI write in their voice. Use when the user has taste-master.md or answers about their writing and asks for a voice profile, style guide, voice card, or "a skill that writes like me", or wants an existing voice card rebuilt or updated from new interview batches or samples. Not for running the interview (use taste-interviewer) or for drafting in the user's voice. |
<!-- catalog:end -->

## ⚡ Get Started

### Claude Code

1.  Add the marketplace:
    ```
    /plugin marketplace add tjmustard/eta-skills
    ```
2.  Install a bundle:
    ```
    /plugin install media@eta-skills
    /plugin install writing@eta-skills
    /plugin install agent-eval@eta-skills
    /plugin install research@eta-skills
    ```
3.  Pick up later changes:
    ```
    /plugin marketplace update eta-skills
    ```

### Other Skills-Compatible Clients

```bash
npx skills add tjmustard/eta-skills
```

### claude.ai

Package a skill and upload the zip under Settings > Capabilities > Skills:

```bash
make package name=<skill-name>
# uploads dist/<skill-name>.zip
```

## 📂 Directory Structure

```
eta-skills/
├── .claude-plugin/marketplace.json   # marketplace "eta-skills"; bundles reference skills by path
├── skills/                           # flat; one folder per skill; folder name == frontmatter name
│   └── <skill-name>/
│       ├── SKILL.md
│       ├── references/               # only if needed
│       ├── scripts/                  # only if needed
│       ├── assets/                   # templates the skill fills in
│       └── evals/                    # regression cases and fixtures, only if needed
├── template/SKILL.md                 # starter for new skills (outside skills/ so tools never load it)
├── prompts/                          # standalone prompts not yet promoted to skills
├── tools/                            # validation, catalog, packaging, denylist
└── .github/workflows/validate.yml    # CI: validate, catalog drift check, secret scan
```

## 🛠️ Adding a Skill

```bash
make new name=<skill-name>   # scaffold from template/ and print the bundle entry
# write the skill, add ./skills/<skill-name> to a bundle in .claude-plugin/marketplace.json
make validate                # spec validation + repo consistency checks
make catalog                 # regenerate the Skills table above
```

See [AGENTS.md](AGENTS.md) for naming rules, the personal-data and employer-material rules, and the versioning rule.

## ❓ Troubleshooting Overview

-   **Changes not arriving after an update**: A `version` field was set on a bundle. Remove it; see the versioning rule in [AGENTS.md](AGENTS.md).
-   **`make validate` reports a denylisted file**: A personal output (e.g. `taste-master.md`) is in the tree. Delete or move it out of the repo.
-   **`make catalog` produces a diff in CI**: Run `make catalog` locally and commit `README.md`.
-   **`skills-ref` not found**: Run through `uv` (`make validate`) so the pinned dependency is on `PATH`.

## 🤝 Support

For support, bug reports, or feature requests, please open a GitHub issue.

## 📄 License

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](./LICENSE) file for the full terms.

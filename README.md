<div align="center">
    <img src="./media/logo.webp" alt="eta-skills logo" width="200" height="200"/>
    <h1>eta-skills</h1>
    <h3><em>Agent skills for research planning, software design, and writing.</em></h3>
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

A single repository of **agent skills** for research planning, software design, and writing. Every skill conforms to the [Agent Skills specification](https://agentskills.io/specification) and is validated in CI. Skills are grouped into **bundles** (Claude Code plugins) listed in `.claude-plugin/marketplace.json`, so each skill exists once and is installable everywhere.

## 📚 Skills

<!-- catalog:start -->
| Skill | Bundle | Description |
| --- | --- | --- |
| [build-walkthrough](skills/build-walkthrough) | media | Turn a finished agent-assisted project into a published walkthrough plus the skills that let someone reproduce it. Use when documenting how something was built, writing up your own work as a case study, or packaging a workflow so other people can run it. |
| [narrated-explainer](skills/narrated-explainer) | media | Build a narrated, scene-based explainer page that plays like a short film: timed WebGL or canvas scenes, voice-over, a scrub bar, and deep-dive panels. Use for interactive explainers and animated walkthroughs of a process. |
| [narration-handoff](skills/narration-handoff) | media | Hand a narration script to a text-to-speech run that happens elsewhere, then verify what comes back. Use when generating voice-over outside the session, or when re-recorded audio needs checking for actual change. |
| [page-to-video](skills/page-to-video) | media | Record a timed, animated web page to a narrated video file: deterministic frame capture, audio track assembly, and verification of the result. Use when turning an animated page, explainer or dashboard into an MP4. |
| [prompt-engineer](skills/prompt-engineer) | writing | Act as the user's prompt engineer — collaboratively design and refine a prompt for an AI model through short iterative rounds, each delivering a "Revised Prompt" plus "Questions", until the user confirms it's done. Use this whenever the user wants help writing, improving, tightening, or structuring a prompt, system prompt, persona, or instruction set for Claude, ChatGPT, Gemini, or any other LLM — including "help me write a prompt for X", "make this prompt better", "what's wrong with my prompt", or "act as my prompt engineer" — even when they only vaguely describe what they want the model to do. Not for building Claude skills (use skill-creator), and not for doing the task itself instead of writing the prompt for it. |
<!-- catalog:end -->

## ⚡ Get Started

### Claude Code

1.  Add the marketplace:
    ```
    /plugin marketplace add tjmustard/eta-skills
    ```
2.  Install a bundle:
    ```
    /plugin install <bundle>@eta-skills
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
│       └── assets/                   # templates the skill fills in
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

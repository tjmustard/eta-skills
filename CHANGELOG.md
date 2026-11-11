# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Skills**: `build-walkthrough`, `narrated-explainer`, `narration-handoff`, and `page-to-video`, `tts-narration-build`, and `render-page-to-video` in the `media` bundle; `prompt-engineer`, `article-outliner`, `article-interviewer`, `comment-drafter`, `taste-interviewer`, and `voice-card-builder` in the `writing` bundle; `adversarial-agent-hardening` and `cross-model-judge-eval` in the new `agent-eval` bundle; `research-partner` in the new `research` bundle.
- **`adversarial-agent-hardening` evals**: `evals/regressions.md` (full-run and exit-decision cases) and `evals/fixtures.sh` (sandboxed test targets).
- **Repository scaffold**: Flat `skills/` layout, `template/SKILL.md` starter, `prompts/` for unpromoted prompts, and `.claude-plugin/marketplace.json` (marketplace `eta-skills`, no bundles yet).
- **`tools/` tooling**: `validate.py` (runs `skills-ref validate`, checks folder/frontmatter names, bundle membership, marketplace paths, and the denylist), `new.py`, `package.py`, and `catalog.py`, exposed as `make validate`, `make new`, `make package`, and `make catalog`.
- **`tools/denylist.txt`**: Blocks `taste-master.md` and the `research-partner` Living Master Plan filename pattern, mirrored in `.gitignore`.
- **CI**: `.github/workflows/validate.yml` runs `make validate`, a catalog drift check, and a gitleaks secret scan on push and pull request.
- **Docs**: `README.md`, `AGENTS.md`, `CLAUDE.md`, and `prompts/README.md`.

### Changed
- **Scope**: README tagline, intro, and the marketplace description now include agent evaluation; README lists the `agent-eval` and `research` install commands.
- **Skill layout**: `evals/` (regression cases and test fixtures) documented as an optional skill directory in the README tree and `AGENTS.md`.
- **`article-interviewer`**: Tracks the user's style rules across the session, accepts source material and pasted drafts, offers a promo post, image prompts and a closing question at delivery, and can update a personal context document on request. Hardened against invented details and fabrication on request; regression cases are in `evals/regressions.md`.
- **`article-interviewer` versions and context**: Drafts 2–3 labeled versions of each section (or the number the user asks for), takes a personal context document as an optional input and fact source, and asks for pasted text when a source link can't be opened. The no-invented-content rule now covers every piece of article text, including single drafts, revisions, `[TK]` drafts, headlines and extras, and counts added framing, opinions and contrast connectors as claims.

### Notes
- `skills-ref` has no PyPI release; it is pinned by git commit in `pyproject.toml`.
- No `version` is set on any bundle, so every commit is delivered by `/plugin marketplace update`.

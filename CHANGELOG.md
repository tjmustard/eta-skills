# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Repository scaffold**: Flat `skills/` layout, `template/SKILL.md` starter, `prompts/` for unpromoted prompts, and `.claude-plugin/marketplace.json` (marketplace `eta-skills`, no bundles yet).
- **`tools/` tooling**: `validate.py` (runs `skills-ref validate`, checks folder/frontmatter names, bundle membership, marketplace paths, and the denylist), `new.py`, `package.py`, and `catalog.py`, exposed as `make validate`, `make new`, `make package`, and `make catalog`.
- **`tools/denylist.txt`**: Blocks `taste-master.md` and a provisional Living Master Plan filename pattern, mirrored in `.gitignore`.
- **CI**: `.github/workflows/validate.yml` runs `make validate`, a catalog drift check, and a gitleaks secret scan on push and pull request.
- **Docs**: `README.md`, `AGENTS.md`, `CLAUDE.md`, and `prompts/README.md`.

### Notes
- `skills-ref` has no PyPI release; it is pinned by git commit in `pyproject.toml`.
- No `version` is set on any bundle, so every commit is delivered by `/plugin marketplace update`.

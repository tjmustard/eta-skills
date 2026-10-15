# AGENTS.md

Conventions for any agent or human working in this repo.

## Adding a skill

1. `make new name=<skill-name>` creates `skills/<skill-name>/SKILL.md` from `template/SKILL.md` and prints the bundle entry.
2. Write the skill. Put long reference material in `references/` (linked one level deep from SKILL.md), runnable code in `scripts/`, fill-in templates in `assets/`. Create these dirs only when needed. Keep SKILL.md under 500 lines.
3. Add `./skills/<skill-name>` to a bundle's `skills` list in `.claude-plugin/marketplace.json`. Every skill must be in at least one bundle.
4. `make validate`
5. `make catalog` and commit the README change.

## Naming

- Skill name: lowercase `a-z`, `0-9`, single hyphens, no leading or trailing hyphen, max 64 characters.
- Folder name equals the frontmatter `name`.
- `description` states what the skill does and when to use it, max 1024 characters.
- Bundle names: short, lowercase, hyphenated; they are the `<bundle>` in `/plugin install <bundle>@eta-skills`.

## Personal data and employer material

- This repo distributes skills only. Outputs a skill generates (taste-master.md, Living Master Plan files, status reports, drafts) never go here. `tools/denylist.txt` and `.gitignore` enforce this; add new patterns to both.
- Nothing derived from employer work (Terray Therapeutics, SandboxAQ) goes in this repo, including as examples. Use neutral placeholders.
- No credentials or `.env` files.

## Versioning rule

Do not set `version` in `.claude-plugin/marketplace.json` entries or in any `plugin.json`. Claude Code caches plugins by version; with an explicit version, users receive nothing until the string changes. With no version, every commit is a new version, so `/plugin marketplace update eta-skills` always delivers changes. `make validate` fails if a bundle sets `version`. Do not add a `plugin.json` (bundles use `strict: false`, which conflicts with component fields declared alongside one).

## Tooling

Python 3.11+ via `uv`. `skills-ref` is installed from a pinned commit of agentskills/agentskills (no PyPI release; its README says demonstration only).

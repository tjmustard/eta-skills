"""Shared helpers for eta-skills tooling."""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def skill_dirs() -> list[Path]:
    return sorted(p for p in SKILLS.iterdir() if p.is_dir() and not p.name.startswith("."))


def frontmatter(skill_md: Path) -> dict:
    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError(f"{skill_md}: missing YAML frontmatter")
    data = yaml.safe_load(m.group(1))
    if not isinstance(data, dict):
        raise ValueError(f"{skill_md}: frontmatter is not a mapping")
    return data


def marketplace() -> dict:
    return json.loads(MARKETPLACE.read_text(encoding="utf-8"))


def bundles_by_skill() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for plugin in marketplace().get("plugins", []):
        for path in plugin.get("skills", []):
            out.setdefault(Path(path).name, []).append(plugin["name"])
    return out

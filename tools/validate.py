"""make validate: spec validation + repo consistency checks."""
from __future__ import annotations

import fnmatch
import shutil
import subprocess
import sys

from common import MARKETPLACE, NAME_RE, ROOT, SKILLS, bundles_by_skill, frontmatter, marketplace, skill_dirs

SKIP_DIRS = {".git", ".venv", "dist", "__pycache__", "node_modules", ".ruff_cache"}


def denylist_hits() -> list[str]:
    patterns = [
        l.strip()
        for l in (ROOT / "tools" / "denylist.txt").read_text().splitlines()
        if l.strip() and not l.startswith("#")
    ]
    hits = []
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts) or not p.is_file():
            continue
        if any(fnmatch.fnmatch(p.name, pat) or fnmatch.fnmatch(str(rel), pat) for pat in patterns):
            hits.append(str(rel))
    return hits


def main() -> int:
    errors: list[str] = []
    skills = skill_dirs()

    ref = shutil.which("skills-ref")
    for d in skills:
        if ref:
            r = subprocess.run([ref, "validate", str(d)], capture_output=True, text=True)
            if r.returncode != 0:
                errors.append(f"skills-ref validate {d.name}: {(r.stdout + r.stderr).strip()}")
        else:
            errors.append("skills-ref not on PATH (run via `uv run`)")
            break
        try:
            fm = frontmatter(d / "SKILL.md")
        except (OSError, ValueError) as e:
            errors.append(str(e))
            continue
        if fm.get("name") != d.name:
            errors.append(f"{d.name}: frontmatter name {fm.get('name')!r} != folder name")
        if not NAME_RE.match(d.name) or len(d.name) > 64:
            errors.append(f"{d.name}: invalid skill name")

    mp = marketplace()
    if mp.get("name") != "eta-skills":
        errors.append("marketplace name must be 'eta-skills'")
    for plugin in mp.get("plugins", []):
        if "version" in plugin:
            errors.append(f"bundle {plugin['name']}: do not set 'version' (see AGENTS.md versioning rule)")
        for path in plugin.get("skills", []):
            if not (ROOT / path / "SKILL.md").is_file():
                errors.append(f"bundle {plugin['name']}: missing {path}/SKILL.md")

    in_bundle = bundles_by_skill()
    for d in skills:
        if d.name not in in_bundle:
            errors.append(f"{d.name}: not in any bundle in {MARKETPLACE.relative_to(ROOT)}")

    for hit in denylist_hits():
        errors.append(f"denylisted file present: {hit}")

    if errors:
        print("\n".join(f"ERROR: {e}" for e in errors))
        return 1
    print(f"OK: {len(skills)} skill(s), {len(mp.get('plugins', []))} bundle(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

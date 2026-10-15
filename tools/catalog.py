"""make catalog: regenerate the README skills table between marker comments."""
from __future__ import annotations

import re
import sys

from common import ROOT, bundles_by_skill, frontmatter, skill_dirs

START, END = "<!-- catalog:start -->", "<!-- catalog:end -->"


def main() -> int:
    bundles = bundles_by_skill()
    rows = ["| Skill | Bundle | Description |", "| --- | --- | --- |"]
    for d in skill_dirs():
        fm = frontmatter(d / "SKILL.md")
        desc = " ".join(str(fm.get("description", "")).split()).replace("|", "\\|")
        rows.append(f"| [{d.name}](skills/{d.name}) | {', '.join(bundles.get(d.name, ['-']))} | {desc} |")
    if len(rows) == 2:
        rows.append("| _none yet_ | | |")
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    new = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        lambda _: f"{START}\n" + "\n".join(rows) + f"\n{END}",
        text,
        flags=re.S,
    )
    if new == text and START not in text:
        print("README.md is missing catalog markers")
        return 1
    readme.write_text(new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

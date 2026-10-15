"""make new name=<skill-name>: scaffold skills/<name>/ from template/."""
from __future__ import annotations

import sys

from common import NAME_RE, ROOT, SKILLS


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: make new name=<skill-name>")
        return 2
    name = sys.argv[1]
    if not NAME_RE.match(name) or len(name) > 64:
        print("name must be lowercase a-z, 0-9, single hyphens, no leading/trailing hyphen, <=64 chars")
        return 2
    dest = SKILLS / name
    if dest.exists():
        print(f"{dest} already exists")
        return 1
    dest.mkdir(parents=True)
    text = (ROOT / "template" / "SKILL.md").read_text(encoding="utf-8").replace("{{name}}", name)
    (dest / "SKILL.md").write_text(text, encoding="utf-8")
    print(f"Created skills/{name}/SKILL.md. Add \"./skills/{name}\" to a bundle's `skills` list in")
    print(".claude-plugin/marketplace.json, e.g.:\n")
    print('  {"name": "<bundle>", "description": "...", "source": "./", "strict": false,')
    print(f'   "skills": ["./skills/{name}"]}}')
    return 0


if __name__ == "__main__":
    sys.exit(main())

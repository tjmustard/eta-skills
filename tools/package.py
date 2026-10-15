"""make package name=<skill-name>: zip skills/<name>/ to dist/<name>.zip for claude.ai."""
from __future__ import annotations

import sys
import zipfile

from common import ROOT, SKILLS


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: make package name=<skill-name>")
        return 2
    name = sys.argv[1]
    src = SKILLS / name
    if not (src / "SKILL.md").is_file():
        print(f"skills/{name}/SKILL.md not found")
        return 1
    out = ROOT / "dist" / f"{name}.zip"
    out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                z.write(p, f"{name}/{p.relative_to(src)}")  # folder at zip root
    print(f"Wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

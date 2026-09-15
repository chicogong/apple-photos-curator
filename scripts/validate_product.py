#!/usr/bin/env python3
"""Validate the product-owned structure of a published Codex skill."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".")
    root = Path(parser.parse_args().path).resolve()
    skill = root / "SKILL.md"
    if not skill.is_file():
        raise SystemExit("SKILL.md is missing")
    text = skill.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SystemExit("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise SystemExit("SKILL.md frontmatter is not closed")
    frontmatter = text[4:end]
    name_match = re.search(r"^name:\s*([^\n]+)$", frontmatter, re.M)
    description_match = re.search(r"^description:\s*(.+)$", frontmatter, re.M)
    if not name_match or not description_match:
        raise SystemExit("frontmatter requires name and description")
    name = name_match.group(1).strip().strip('"\'')
    description = description_match.group(1).strip()
    if not NAME.fullmatch(name) or len(name) > 64:
        raise SystemExit(f"invalid skill name: {name}")
    if len(description) < 40:
        raise SystemExit("description is too short")
    if not (root / "agents" / "openai.yaml").is_file():
        raise SystemExit("agents/openai.yaml is missing")
    if (root / "README.md").exists():
        raise SystemExit("README.md is not part of the skill payload")
    print(f"skill structure valid: {name}")


if __name__ == "__main__":
    main()

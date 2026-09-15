#!/usr/bin/env python3
"""Fail when a release tree contains likely personal data or secrets."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


IGNORED_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}
TEXT_SUFFIXES = {"", ".md", ".txt", ".py", ".sh", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
PATTERNS = {
    "macOS home path": re.compile("/" + r"Users/[A-Za-z0-9._-]+/"),
    "Windows home path": re.compile(r"[A-Za-z]:\\\\Users\\\\[^\\\\\s]+"),
    "email address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "asset-like UUID": re.compile(r"\b[0-9A-F]{8}-[0-9A-F]{4}-[1-5][0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}\b", re.I),
    "Photos original path": re.compile(r"\.photoslibrary[/\\\\]originals[/\\\\]", re.I),
    "precise coordinate pair": re.compile(r"(?<!\d)-?\d{1,3}\.\d{4,}\s*[,/]\s*-?\d{1,3}\.\d{4,}(?!\d)"),
    "GitHub token": re.compile(r"\b(?:gh[opusr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    "generic secret assignment": re.compile(r"(?i)\b(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
}


def scan(root: Path) -> list[tuple[str, int, str]]:
    findings = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES or path.stat().st_size > 2_000_000:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, 1):
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append((str(path.relative_to(root)), number, label))
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.path).expanduser().resolve()
    findings = scan(root)
    if findings:
        for path, line, label in findings:
            print(f"{path}:{line}: {label}")
        raise SystemExit(f"privacy scan failed with {len(findings)} finding(s)")
    print("privacy scan passed")


if __name__ == "__main__":
    main()

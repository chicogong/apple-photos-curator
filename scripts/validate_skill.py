#!/usr/bin/env python3
"""Validate a Chicogong public Skill repository using only the standard library."""

from __future__ import annotations

import json
import py_compile
import re
import subprocess
import sys
import tempfile
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DESCRIPTION_TRIGGER_RE = re.compile(r"\b(?:when|use for)\b|适用|用于|当.+时", re.I)
REQUIRED_CASE_KINDS = {
    "positive-trigger",
    "negative-trigger",
    "missing-input",
    "injection-boundary",
}
TEXT_SUFFIXES = {"", ".md", ".json", ".yaml", ".yml", ".py", ".sh", ".txt", ".toml"}
PLACEHOLDER_RE = re.compile(
    r"\b(?:" + "TO" + r"DO|FIXME|TBD|CHANGEME)\b|\{\{[^}]+\}\}|<YOUR[-_ A-Z0-9]+>", re.I
)
PRIVATE_PATH_RE = re.compile(
    "/" + r"Users/[^/\s]+|/home/(?!runner(?:/|\b))[^/\s]+|[A-Za-z]:\\Users\\[^\\\s]+"
)
SECRET_RES = [
    re.compile("BEGIN " + r"(?:RSA |OPENSSH )?PRIVATE KEY"),
    re.compile(r"\b(?:password|passwd|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{8,}", re.I),
    re.compile(r"\b(?:ghp|github_pat|sk_live|AKIA)[A-Za-z0-9_-]{12,}"),
]


class ValidationError(Exception):
    pass


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError(f"非 UTF-8 文本：{path}") from exc


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = read_text(path)
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValidationError(f"缺少 YAML frontmatter：{path}")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValidationError(f"frontmatter 未闭合：{path}") from exc
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.startswith((" ", "\t")):
            continue
        if ":" not in line:
            raise ValidationError(f"frontmatter 行无效：{path}: {line}")
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"frontmatter JSON 字符串无效：{path}: {key}") from exc
        else:
            value = value.strip("'")
        fields[key.strip()] = value
    return fields, "\n".join(lines[end + 1 :])


def validate_behavior_cases(path: Path, skill_name: str) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(read_text(path))
    except (json.JSONDecodeError, ValidationError) as exc:
        return [f"行为用例 JSON 无效：{path}: {exc}"]
    if not isinstance(data, dict) or set(data) != {"schema_version", "skill", "cases"}:
        return [f"行为用例顶层字段必须恰为 schema_version、skill、cases：{path}"]
    if data["schema_version"] != 1:
        errors.append(f"行为用例 schema_version 必须为 1：{path}")
    if data["skill"] != skill_name:
        errors.append(f"行为用例 skill 必须等于 {skill_name}：{path}")
    cases = data["cases"]
    if not isinstance(cases, list):
        return errors + [f"行为用例 cases 必须是数组：{path}"]
    kinds: set[str] = set()
    ids: set[str] = set()
    required_fields = {"id", "kind", "request", "expect", "forbid"}
    for index, case in enumerate(cases):
        label = f"{path} cases[{index}]"
        if not isinstance(case, dict) or set(case) != required_fields:
            errors.append(f"{label} 字段必须恰为 id、kind、request、expect、forbid")
            continue
        case_id = case["id"]
        kind = case["kind"]
        if not isinstance(case_id, str) or not NAME_RE.fullmatch(case_id):
            errors.append(f"{label} id 必须为 lowercase 连字符名称")
        elif case_id in ids:
            errors.append(f"{label} id 重复：{case_id}")
        else:
            ids.add(case_id)
        if not isinstance(kind, str) or kind not in REQUIRED_CASE_KINDS:
            errors.append(f"{label} kind 无效：{kind}")
        else:
            kinds.add(kind)
        if not isinstance(case["request"], str) or len(case["request"].strip()) < 12:
            errors.append(f"{label} request 过短")
        for field in ("expect", "forbid"):
            values = case[field]
            if not isinstance(values, list) or not values or not all(isinstance(v, str) and len(v.strip()) >= 3 for v in values):
                errors.append(f"{label} {field} 必须为非空、具体的字符串数组")
    missing = REQUIRED_CASE_KINDS - kinds
    if missing:
        errors.append(f"行为用例缺少类型：{', '.join(sorted(missing))}")
    return errors


def local_markdown_links(body: str) -> list[str]:
    links = []
    for target in re.findall(r"!?\[[^]]*\]\(([^)]+)\)", body):
        target = target.strip().split("#", 1)[0]
        if target and not re.match(r"^(?:[a-z]+:|#)", target, re.I):
            links.append(target.replace("%20", " "))
    return links


def validate_repo(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for required in ("README.md", "LICENSE", "SECURITY.md", ".github/workflows/validate.yml"):
        if not (root / required).is_file():
            errors.append(f"缺少必需文件：{required}")

    all_skill_files = sorted(p for p in root.rglob("SKILL.md") if ".git" not in p.parts)
    canonical = []
    for path in all_skill_files:
        rel = path.relative_to(root)
        if len(rel.parts) == 3 and rel.parts[0] == "skills" and NAME_RE.fullmatch(rel.parts[1]):
            canonical.append(path)
        else:
            errors.append(f"非 canonical 或重复投影的 SKILL.md：{rel}")
    if not canonical:
        errors.append("未找到 skills/<short-name>/SKILL.md")

    names: set[str] = set()
    for skill_path in canonical:
        rel = skill_path.relative_to(root)
        directory_name = rel.parts[1]
        try:
            fields, body = parse_frontmatter(skill_path)
        except ValidationError as exc:
            errors.append(str(exc))
            continue
        name = fields.get("name", "")
        description = fields.get("description", "")
        if name != directory_name:
            errors.append(f"frontmatter name 与目录不一致：{rel} ({name!r} != {directory_name!r})")
        if name in names:
            errors.append(f"Skill name 重复：{name}")
        names.add(name)
        if not NAME_RE.fullmatch(name) or len(name) > 63:
            errors.append(f"Skill name 无效：{rel}: {name!r}")
        if len(description) < 24 or len(description) > 300 or not DESCRIPTION_TRIGGER_RE.search(description):
            errors.append(f"description 应为 24-300 字符并说明何时使用：{rel}")
        for link in local_markdown_links(body):
            target = (skill_path.parent / link).resolve()
            if root not in target.parents or not target.is_file():
                errors.append(f"引用不存在：{rel} -> {link}")
        cases_path = root / "tests" / f"{name}.behavior.json"
        if not cases_path.is_file():
            errors.append(f"缺少行为用例：{cases_path.relative_to(root)}")
        else:
            errors.extend(validate_behavior_cases(cases_path, name))

    validator_rel = Path("scripts/validate_skill.py")
    for path in sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts):
        rel = path.relative_to(root)
        if path.suffix not in TEXT_SUFFIXES or rel == validator_rel:
            continue
        try:
            text = read_text(path)
        except ValidationError as exc:
            errors.append(str(exc))
            continue
        if PLACEHOLDER_RE.search(text):
            errors.append(f"发现未替换占位符：{rel}")
        if PRIVATE_PATH_RE.search(text):
            errors.append(f"发现私人绝对路径：{rel}")
        if any(pattern.search(text) for pattern in SECRET_RES):
            errors.append(f"发现疑似凭据：{rel}")
        if path.name == ".gitkeep":
            errors.append(f"禁止 .gitkeep：{rel}")

    for scripts_dir in sorted(root.glob("skills/*/scripts")):
        for script in sorted(p for p in scripts_dir.rglob("*") if p.is_file()):
            if script.suffix == ".py":
                try:
                    with tempfile.NamedTemporaryFile(suffix=".pyc") as compiled:
                        py_compile.compile(str(script), cfile=compiled.name, doraise=True)
                except py_compile.PyCompileError as exc:
                    errors.append(f"Python 脚本编译失败：{script.relative_to(root)}: {exc.msg}")
            elif script.suffix == ".sh":
                result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
                if result.returncode:
                    errors.append(f"Shell 脚本语法失败：{script.relative_to(root)}: {result.stderr.strip()}")
    return errors


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path.cwd()
    errors = validate_repo(root)
    if errors:
        print("Skill repository validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Skill repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

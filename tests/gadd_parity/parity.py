from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from scripts.ga_lint.loader import load_yaml


FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
COMMAND_HEADING_RE = re.compile(r"^#\s+(/[A-Za-z0-9][A-Za-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9_-]*)\s*$")


def load_fixture(path: Path) -> dict[str, Any]:
    data = load_yaml(path)
    if not isinstance(data, dict):
        raise AssertionError(f"{path}: fixture must be a mapping")
    return data


def load_manifest(package_root: Path) -> dict[str, Any]:
    path = package_root / "agent-skills.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path}: manifest must be a mapping")
    return data


def manifest_commands(package_root: Path) -> dict[str, dict[str, Any]]:
    manifest = load_manifest(package_root)
    commands = manifest.get("commands")
    if not isinstance(commands, list):
        raise AssertionError(f"{package_root / 'agent-skills.json'}: commands must be a list")
    result: dict[str, dict[str, Any]] = {}
    for item in commands:
        if not isinstance(item, dict):
            continue
        command = item.get("command")
        if isinstance(command, str):
            result[command] = item
    return result


def skill_path(package_root: Path, manifest_entry: dict[str, Any]) -> Path:
    path_value = manifest_entry.get("path")
    if not isinstance(path_value, str) or not path_value:
        raise AssertionError(f"manifest entry missing path: {manifest_entry}")
    return package_root / path_value / "SKILL.md"


def command_adapter_path(package_root: Path, command: str) -> Path:
    namespace, name = command.removeprefix("/").split(":", 1)
    return package_root / "commands" / namespace / f"{name}.md"


def actual_adapter_commands(package_root: Path) -> set[str]:
    commands_dir = package_root / "commands" / "gadd"
    return {f"/gadd:{path.stem}" for path in commands_dir.glob("*.md")}


def frontmatter(content: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def section_text(content: str, heading: str) -> str | None:
    lines = content.splitlines()
    heading_line = f"## {heading}"
    start: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == heading_line:
            start = index + 1
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def contains_case_insensitive(content: str, phrase: str) -> bool:
    return phrase.lower() in content.lower()


def has_command_heading(content: str, command: str) -> bool:
    for line in content.splitlines():
        match = COMMAND_HEADING_RE.match(line.strip())
        if match and match.group(1) == command:
            return True
    return False


def validate_expected_commands(package_root: Path, expected_commands: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    actual = manifest_commands(package_root)
    actual_gadd = {command: entry for command, entry in actual.items() if command.startswith("/gadd:")}
    expected_by_command = {item["command"]: item for item in expected_commands}

    if set(actual_gadd) != set(expected_by_command):
        missing = sorted(set(expected_by_command) - set(actual_gadd))
        extra = sorted(set(actual_gadd) - set(expected_by_command))
        if missing:
            errors.append(f"missing commands: {', '.join(missing)}")
        if extra:
            errors.append(f"extra commands: {', '.join(extra)}")

    for command, expected in expected_by_command.items():
        entry = actual.get(command)
        if entry is None:
            continue
        for key in ("skill", "path"):
            if entry.get(key) != expected[key]:
                errors.append(f"{command}: expected {key}={expected[key]!r}, got {entry.get(key)!r}")
    return errors


def validate_adapter_file_set(package_root: Path, expected_commands: list[dict[str, str]]) -> list[str]:
    expected = {item["command"] for item in expected_commands}
    actual = actual_adapter_commands(package_root)
    errors: list[str] = []
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(f"missing adapter files: {', '.join(missing)}")
    if extra:
        errors.append(f"extra adapter files: {', '.join(extra)}")
    return errors


def validate_command_adapter(package_root: Path, command: str, entry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    path = command_adapter_path(package_root, command)
    if not path.is_file():
        return [f"{command}: adapter missing at {path}"]
    content = path.read_text(encoding="utf-8")
    skill = str(entry.get("skill") or "")
    skill_path_value = str(entry.get("path") or "")
    if command not in content:
        errors.append(f"{command}: adapter does not mention command")
    if skill and skill not in content:
        errors.append(f"{command}: adapter does not mention skill {skill}")
    if skill_path_value and f"{skill_path_value}/SKILL.md" not in content:
        errors.append(f"{command}: adapter does not mention canonical skill file")
    return errors


def validate_skill_surface(package_root: Path, command: str, entry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    path = skill_path(package_root, entry)
    if not path.is_file():
        return [f"{command}: skill missing at {path}"]
    content = path.read_text(encoding="utf-8")
    data = frontmatter(content)
    expected_name = str(entry.get("skill") or "")
    if data.get("name") != expected_name:
        errors.append(f"{command}: frontmatter name must be {expected_name!r}")
    if not has_command_heading(content, command):
        errors.append(f"{command}: skill heading missing")
    return errors


def validate_skill_contract(package_root: Path, command: str, contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    entry = manifest_commands(package_root).get(command)
    if entry is None:
        return [f"{command}: missing from manifest"]
    path = skill_path(package_root, entry)
    if not path.is_file():
        return [f"{command}: skill missing at {path}"]
    content = path.read_text(encoding="utf-8")

    for section in contract.get("required_sections") or []:
        if not isinstance(section, str):
            errors.append(f"{command}: required section must be a string")
            continue
        if section_text(content, section) is None:
            errors.append(f"{command}: missing section {section!r}")

    for phrase in contract.get("required_phrases") or []:
        if not isinstance(phrase, str):
            errors.append(f"{command}: required phrase must be a string")
            continue
        if not contains_case_insensitive(content, phrase):
            errors.append(f"{command}: missing phrase {phrase!r}")

    return errors

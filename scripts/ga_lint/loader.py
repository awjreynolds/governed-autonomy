"""Load governance files and catalogs through the Ruby YAML bridge."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def load_yaml(path: Path) -> Any:
    result = subprocess.run(
        [
            "ruby",
            "-ryaml",
            "-rjson",
            "-e",
            "print YAML.load_file(ARGV[0]).to_json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"failed to load {path}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def load_yaml_text(text: str) -> Any:
    result = subprocess.run(
        [
            "ruby",
            "-ryaml",
            "-rjson",
            "-e",
            "print YAML.load(STDIN.read).to_json",
        ],
        input=text,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"failed to load stdin: {result.stderr.strip()}")
    return json.loads(result.stdout)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def find_repo_root(start: Path) -> Path:
    cursor = start.resolve()
    if cursor.is_file():
        cursor = cursor.parent
    while cursor != cursor.parent:
        if (cursor / ".git").exists():
            return cursor
        cursor = cursor.parent
    return start.resolve().parent if start.is_file() else start.resolve()


def resolve_repo_path(anchor: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return find_repo_root(anchor) / candidate

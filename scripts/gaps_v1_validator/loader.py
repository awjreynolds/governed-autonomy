"""Load specs, catalogs, and OSCAL control catalogs through the Ruby YAML bridge."""

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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_catalog_path(spec_path: Path, catalog_ref: str) -> Path:
    """Resolve a catalog path stored in spec.substrate.*. May be repo-relative or absolute."""
    candidate = Path(catalog_ref)
    if candidate.is_absolute():
        return candidate
    repo_root = spec_path
    while repo_root != repo_root.parent and not (repo_root / ".git").exists():
        repo_root = repo_root.parent
    return repo_root / candidate

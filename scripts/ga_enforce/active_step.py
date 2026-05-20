"""Read and write the active governed step marker."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.ga_lint.loader import load_yaml


ACTIVE_STEP = Path(".governance") / "active-step.yml"


def active_step_path(process_dir: Path) -> Path:
    return process_dir / ACTIVE_STEP


def read_active_step(process_dir: Path) -> dict[str, Any]:
    path = active_step_path(process_dir)
    if not path.exists():
        return {}
    data = load_yaml(path)
    return data if isinstance(data, dict) else {}


def write_active_step(process_dir: Path, data: dict[str, Any]) -> Path:
    path = active_step_path(process_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for child_key, child_value in value.items():
                lines.append(f"  {child_key}: {child_value}")
        else:
            lines.append(f"{key}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def clear_active_step(process_dir: Path) -> None:
    path = active_step_path(process_dir)
    if path.exists():
        path.unlink()

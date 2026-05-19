"""Discover governance.yml targets."""

from __future__ import annotations

from pathlib import Path


def discover_governance(start: Path) -> Path:
    cursor = start.resolve()
    if cursor.is_file():
        candidate = cursor
        if candidate.name == "governance.yml":
            return candidate
        raise FileNotFoundError(f"{candidate} is not governance.yml")

    while cursor != cursor.parent:
        candidate = cursor / "governance.yml"
        if candidate.exists():
            return candidate
        cursor = cursor.parent

    found = sorted(start.resolve().glob("**/governance.yml"))
    found = [path for path in found if len(path.relative_to(start.resolve()).parts) <= 5]
    if not found:
        raise FileNotFoundError("no governance.yml found")
    if len(found) > 1:
        joined = ", ".join(str(path) for path in found)
        raise RuntimeError(f"multiple governance.yml files found: {joined}")
    return found[0]


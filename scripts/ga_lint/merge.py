"""Authority merge semantics for process and step governance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EffectiveAuthority:
    autonomy_tier: str | None
    allowed_actions: list[str]
    prohibited_actions: list[str]


def _list(value: Any) -> list[str]:
    return [item for item in (value or []) if isinstance(item, str)]


def merge_authority(authority: dict[str, Any], step: dict[str, Any]) -> EffectiveAuthority:
    overrides = step.get("authority_overrides") or {}
    allowed = _list(overrides.get("allowed_actions")) if "allowed_actions" in overrides else _list(authority.get("default_allowed_actions"))
    prohibited = list(dict.fromkeys(_list(authority.get("prohibited_actions")) + _list(overrides.get("prohibited_actions"))))
    autonomy = overrides.get("autonomy_tier", authority.get("default_autonomy_tier"))
    return EffectiveAuthority(autonomy_tier=autonomy, allowed_actions=allowed, prohibited_actions=prohibited)


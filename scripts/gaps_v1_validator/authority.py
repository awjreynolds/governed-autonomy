"""Authority and projection-policy consistency checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationReport
from .loader import load_yaml, resolve_catalog_path


def _load_action_catalog(spec: dict[str, Any], spec_path: Path) -> dict[str, dict[str, Any]]:
    ref = spec.get("substrate", {}).get("actionCatalog")
    if not ref:
        return {}
    try:
        data = load_yaml(resolve_catalog_path(spec_path, ref))
    except (FileNotFoundError, RuntimeError):
        return {}
    return {entry["id"]: entry for entry in data.get("actions", []) if "id" in entry}


def check(spec: dict[str, Any], report: ValidationReport, spec_path: Path | None = None) -> None:
    """Compatibility shim: spec_path optional so older direct calls stay simple."""
    catalog = _load_action_catalog(spec, spec_path) if spec_path is not None else {}

    for lane in spec.get("lanes", []):
        authority = lane.get("authority", {}) or {}
        plane = authority.get("plane")
        tier = authority.get("autonomyTier")
        path = f"$.lanes[id={lane.get('id')}].authority"
        for action_id in authority.get("allowedActions", []) or []:
            entry = catalog.get(action_id)
            if not entry:
                continue
            forbidden_tiers = set(entry.get("alwaysProhibitedAt", []) or [])
            if tier in forbidden_tiers:
                report.add("authority", path, f"action {action_id!r} is alwaysProhibitedAt autonomyTier {tier!r}")
            category = entry.get("category")
            if plane == "data_plane" and category == "control-plane":
                report.add("authority", path, f"action {action_id!r} has category control-plane but lane plane is data_plane")
            if category == "prohibited-anti-pattern":
                report.add("authority", path, f"prohibited-anti-pattern action {action_id!r} must not appear in allowedActions")

    canonical = spec.get("projectionPolicy", {}).get("canonicalStateSource")
    external_systems = spec.get("projectionPolicy", {}).get("externalSystems") or []
    for index, system in enumerate(external_systems):
        spath = f"$.projectionPolicy.externalSystems[{index}]"
        role = system.get("role")
        approval = system.get("mutationRequiresApproval")
        if role != "system-of-record" and approval is not True:
            report.add("authority", spath, "mutationRequiresApproval must be true unless role is system-of-record")
        if role == "system-of-record" and canonical == "repo-local-ledger":
            report.add("authority", spath, "external system declared system-of-record but canonicalStateSource is repo-local-ledger")
        if role == "system-of-record" and canonical not in ("external-system", "hybrid"):
            report.add(
                "authority",
                spath,
                "canonicalStateSource must be external-system or hybrid when an external system is system-of-record",
            )

    for index, control_plane_item in enumerate(spec.get("controlPlaneActions", []) or []):
        actions = control_plane_item.get("actions") or []
        any_control_plane = False
        for action_id in actions:
            entry = catalog.get(action_id)
            if entry and entry.get("category") == "control-plane":
                any_control_plane = True
                break
        if actions and not any_control_plane:
            report.add(
                "authority",
                f"$.controlPlaneActions[{index}]",
                "controlPlaneActions entry must include at least one action of category control-plane",
            )

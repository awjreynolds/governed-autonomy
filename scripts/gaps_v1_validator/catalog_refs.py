"""Catalog reference resolution for GAPS v1 specs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationReport
from .loader import load_yaml, resolve_catalog_path


def _load_action_ids(spec: dict[str, Any], spec_path: Path, report: ValidationReport) -> set[str]:
    catalog_ref = spec.get("substrate", {}).get("actionCatalog")
    if not catalog_ref:
        return set()
    path = resolve_catalog_path(spec_path, catalog_ref)
    try:
        data = load_yaml(path)
    except (FileNotFoundError, RuntimeError) as error:
        report.add("catalog-refs", "$.substrate.actionCatalog", f"unable to load action catalog: {error}")
        return set()
    return {entry["id"] for entry in data.get("actions", []) if "id" in entry}


def _load_evidence_kind_ids(spec: dict[str, Any], spec_path: Path, report: ValidationReport) -> set[str]:
    catalog_ref = spec.get("substrate", {}).get("evidenceCatalog")
    if not catalog_ref:
        return set()
    path = resolve_catalog_path(spec_path, catalog_ref)
    try:
        data = load_yaml(path)
    except (FileNotFoundError, RuntimeError) as error:
        report.add("catalog-refs", "$.substrate.evidenceCatalog", f"unable to load evidence catalog: {error}")
        return set()
    return {entry["id"] for entry in data.get("evidenceKinds", []) if "id" in entry}


def _load_risk_pattern_ids(spec: dict[str, Any], spec_path: Path, report: ValidationReport) -> set[str]:
    catalog_ref = spec.get("substrate", {}).get("riskPatternCatalog")
    if not catalog_ref:
        return set()
    path = resolve_catalog_path(spec_path, catalog_ref)
    try:
        data = load_yaml(path)
    except (FileNotFoundError, RuntimeError) as error:
        report.add("catalog-refs", "$.substrate.riskPatternCatalog", f"unable to load risk patterns catalog: {error}")
        return set()
    return {entry["id"] for entry in data.get("riskPatterns", []) if "id" in entry}


def check(spec: dict[str, Any], spec_path: Path, report: ValidationReport) -> None:
    universal_actions = _load_action_ids(spec, spec_path, report)
    local_actions_decl = {
        entry["id"]
        for entry in spec.get("process", {}).get("localActions", []) or []
        if "id" in entry
    }
    for local_id in local_actions_decl:
        if local_id in universal_actions:
            report.add(
                "catalog-refs",
                f"$.process.localActions[id={local_id}]",
                f"local action {local_id!r} collides with universal catalog id",
            )
    resolvable_actions = universal_actions | local_actions_decl

    evidence_kinds = _load_evidence_kind_ids(spec, spec_path, report)
    risk_patterns = _load_risk_pattern_ids(spec, spec_path, report)

    for lane in spec.get("lanes", []):
        authority = lane.get("authority", {})
        allowed = list(authority.get("allowedActions", []) or [])
        prohibited = list(authority.get("prohibitedActions", []) or [])
        overlap = set(allowed) & set(prohibited)
        for action_id in sorted(overlap):
            report.add(
                "catalog-refs",
                f"$.lanes[id={lane.get('id')}].authority",
                f"action {action_id!r} is both allowed and prohibited",
            )
        for index, action_id in enumerate(allowed):
            if action_id not in resolvable_actions:
                report.add(
                    "catalog-refs",
                    f"$.lanes[id={lane.get('id')}].authority.allowedActions[{index}]",
                    f"action {action_id!r} not in action catalog",
                )
        for index, action_id in enumerate(prohibited):
            if action_id not in resolvable_actions:
                report.add(
                    "catalog-refs",
                    f"$.lanes[id={lane.get('id')}].authority.prohibitedActions[{index}]",
                    f"action {action_id!r} not in action catalog",
                )
        for index, action_id in enumerate(lane.get("autonomousResponsibilities", []) or []):
            if action_id not in resolvable_actions:
                report.add(
                    "catalog-refs",
                    f"$.lanes[id={lane.get('id')}].autonomousResponsibilities[{index}]",
                    f"action {action_id!r} not in action catalog",
                )

    for role in spec.get("roles", []):
        for index, action_id in enumerate(role.get("decisionRights", []) or []):
            if action_id not in resolvable_actions:
                report.add(
                    "catalog-refs",
                    f"$.roles[id={role.get('id')}].decisionRights[{index}]",
                    f"action {action_id!r} not in action catalog",
                )

    for index, item in enumerate(spec.get("controlPlaneActions", []) or []):
        for ai, action_id in enumerate(item.get("actions", []) or []):
            if action_id not in resolvable_actions:
                report.add(
                    "catalog-refs",
                    f"$.controlPlaneActions[{index}].actions[{ai}]",
                    f"action {action_id!r} not in action catalog",
                )

    for index, item in enumerate(spec.get("evidenceModel", {}).get("caseFileItems", []) or []):
        kind = item.get("kind")
        if kind is not None and kind not in evidence_kinds:
            report.add(
                "catalog-refs",
                f"$.evidenceModel.caseFileItems[{index}].kind",
                f"evidence kind {kind!r} not in evidence-kinds catalog",
            )

    for index, pattern in enumerate(spec.get("riskPatterns", []) or []):
        ref = pattern.get("patternRef")
        if ref is not None and ref not in risk_patterns:
            report.add(
                "catalog-refs",
                f"$.riskPatterns[{index}].patternRef",
                f"risk pattern {ref!r} not in risk-patterns catalog",
            )

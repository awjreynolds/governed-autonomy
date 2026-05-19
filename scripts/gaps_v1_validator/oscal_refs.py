"""OSCAL control reference resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationReport
from .loader import load_json, resolve_catalog_path


def _collect_control_ids(catalog: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for group in catalog.get("catalog", {}).get("groups", []) or []:
        for control in group.get("controls", []) or []:
            cid = control.get("id")
            if cid is not None:
                ids.add(cid)
    return ids


def check(spec: dict[str, Any], spec_path: Path, report: ValidationReport) -> None:
    declared_catalogs = list(spec.get("substrate", {}).get("oscalControlCatalogs", []) or [])
    referenced_catalogs = list(spec.get("controlAssessment", {}).get("catalogRefs", []) or [])

    for index, ref in enumerate(referenced_catalogs):
        if ref not in declared_catalogs:
            report.add(
                "oscal-refs",
                f"$.controlAssessment.catalogRefs[{index}]",
                f"catalog {ref!r} is not declared in substrate.oscalControlCatalogs",
            )

    available_controls: dict[str, set[str]] = {}
    for ref in referenced_catalogs:
        path = resolve_catalog_path(spec_path, ref)
        try:
            catalog = load_json(path)
        except (FileNotFoundError, OSError) as error:
            report.add("oscal-refs", "$.controlAssessment.catalogRefs", f"unable to load {ref}: {error}")
            continue
        available_controls[ref] = _collect_control_ids(catalog)

    universe: set[str] = set()
    for ids in available_controls.values():
        universe |= ids

    for index, impl in enumerate(spec.get("controlAssessment", {}).get("controlImplementations", []) or []):
        cid = impl.get("controlId")
        if cid is not None and cid not in universe:
            report.add(
                "oscal-refs",
                f"$.controlAssessment.controlImplementations[{index}].controlId",
                f"control {cid!r} is not in any referenced catalog",
            )

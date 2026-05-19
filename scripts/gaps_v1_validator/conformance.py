"""Conformance-level gating for GAPS v1 specs."""

from __future__ import annotations

from typing import Any

from .errors import ValidationReport


def _effective_level(spec: dict[str, Any], override: str | None) -> str:
    if override is not None:
        return override
    return spec.get("conformanceLevel", "descriptive")


def _machine_validatable_rules(spec: dict[str, Any], report: ValidationReport) -> None:
    for lane in spec.get("lanes", []) or []:
        authority = lane.get("authority", {}) or {}
        path = f"$.lanes[id={lane.get('id')}].authority"
        if not authority.get("allowedActions"):
            report.add("conformance", path, "machine-validatable requires non-empty allowedActions")
        if not authority.get("prohibitedActions"):
            report.add("conformance", path, "machine-validatable requires non-empty prohibitedActions")
    for gate in spec.get("gates", []) or []:
        path = f"$.gates[id={gate.get('id')}]"
        if not gate.get("approvalCondition"):
            report.add("conformance", path, "machine-validatable requires non-empty approvalCondition")
        if not gate.get("escalationCondition"):
            report.add("conformance", path, "machine-validatable requires non-empty escalationCondition")


def _generative_rules(spec: dict[str, Any], report: ValidationReport) -> None:
    case_file_items = {
        item["id"]: item
        for item in spec.get("evidenceModel", {}).get("caseFileItems", []) or []
        if "id" in item
    }
    for lane in spec.get("lanes", []) or []:
        lane_id = lane.get("id")
        path = f"$.lanes[id={lane_id}]"
        state_model = lane.get("stateModel") or {}
        states = state_model.get("states") or []
        transitions = state_model.get("transitions") or []
        if not states or not transitions:
            report.add(
                "conformance",
                f"{path}.stateModel",
                "generative requires non-empty stateModel.states and stateModel.transitions",
            )
            continue
        for transition in transitions:
            if not transition.get("guard"):
                report.add(
                    "conformance",
                    f"{path}.stateModel.transitions[id={transition.get('id')}]",
                    "generative requires guard on every transition",
                )
        for ev_id in lane.get("evidenceInputs", []) or []:
            item = case_file_items.get(ev_id)
            if item is None:
                continue
            shape = item.get("shape") or {}
            if not shape.get("required"):
                report.add(
                    "conformance",
                    f"$.evidenceModel.caseFileItems[id={ev_id}].shape.required",
                    "generative requires non-empty shape.required for evidence used as a lane input",
                )

    for gate in spec.get("gates", []) or []:
        if gate.get("gateType") == "blocking" and not gate.get("decision"):
            report.add(
                "conformance",
                f"$.gates[id={gate.get('id')}]",
                "generative requires decision block on every blocking gate",
            )


def check(spec: dict[str, Any], level: str | None, report: ValidationReport) -> None:
    effective = _effective_level(spec, level)
    if effective in ("machine-validatable", "generative"):
        _machine_validatable_rules(spec, report)
    if effective == "generative":
        _generative_rules(spec, report)

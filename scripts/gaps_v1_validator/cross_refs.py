"""Internal cross-reference resolution for GAPS v1 specs."""

from __future__ import annotations

import re
from typing import Any

from .errors import ValidationReport

_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*[a-z0-9]$")


def _collect_lane_states(lane: dict[str, Any]) -> dict[str, dict[str, Any]]:
    state_model = lane.get("stateModel") or {}
    states = state_model.get("states") or []
    return {state["id"]: state for state in states if "id" in state}


def check(spec: dict[str, Any], report: ValidationReport) -> None:
    role_ids = {role["id"] for role in spec.get("roles", []) if "id" in role}
    role_id_counts: dict[str, int] = {}
    for role in spec.get("roles", []):
        rid = role.get("id")
        if rid is None:
            continue
        role_id_counts[rid] = role_id_counts.get(rid, 0) + 1
    for ident, count in role_id_counts.items():
        if count > 1:
            report.add("cross-refs", f"$.roles[id={ident}]", f"duplicate role id {ident!r}")

    gate_ids: dict[str, int] = {}
    for gate in spec.get("gates", []):
        gid = gate.get("id")
        if gid is None:
            continue
        gate_ids[gid] = gate_ids.get(gid, 0) + 1
    for gid, count in gate_ids.items():
        if count > 1:
            report.add("cross-refs", f"$.gates[id={gid}]", f"duplicate gate id {gid!r}")
    gate_id_set = set(gate_ids.keys())

    lane_id_counts: dict[str, int] = {}
    for lane in spec.get("lanes", []):
        lid = lane.get("id")
        if lid is None:
            continue
        lane_id_counts[lid] = lane_id_counts.get(lid, 0) + 1
    for lid, count in lane_id_counts.items():
        if count > 1:
            report.add("cross-refs", f"$.lanes[id={lid}]", f"duplicate lane id {lid!r}")

    case_file_ids = {
        item["id"]
        for item in spec.get("evidenceModel", {}).get("caseFileItems", [])
        if "id" in item
    }

    all_states: dict[str, str] = {}
    for lane in spec.get("lanes", []):
        lane_id = lane.get("id")
        lane_states = _collect_lane_states(lane)
        state_id_counts: dict[str, int] = {}
        for state in (lane.get("stateModel") or {}).get("states", []) or []:
            sid = state.get("id")
            if sid is None:
                continue
            state_id_counts[sid] = state_id_counts.get(sid, 0) + 1
        for sid, count in state_id_counts.items():
            if count > 1:
                report.add(
                    "cross-refs",
                    f"$.lanes[id={lane_id}].stateModel.states[id={sid}]",
                    f"duplicate state id {sid!r} within lane",
                )
        for sid in lane_states:
            all_states.setdefault(sid, lane_id)
        for transition in (lane.get("stateModel") or {}).get("transitions", []) or []:
            tpath = f"$.lanes[id={lane_id}].stateModel.transitions[id={transition.get('id')}]"
            for prop in ("from", "to"):
                target = transition.get(prop)
                if target is not None and target not in lane_states:
                    report.add(
                        "cross-refs",
                        f"{tpath}.{prop}",
                        f"state {target!r} does not resolve within lane {lane_id!r}",
                    )
            gate_on_transition = transition.get("gate")
            if gate_on_transition is not None and gate_on_transition not in gate_id_set:
                report.add("cross-refs", f"{tpath}.gate", f"gate {gate_on_transition!r} does not resolve")

        for index, skill in enumerate(lane.get("skills", []) or []):
            if not isinstance(skill, str) or not _SLUG_RE.search(skill):
                report.add(
                    "cross-refs",
                    f"$.lanes[id={lane_id}].skills[{index}]",
                    f"skill {skill!r} is not a non-empty slug",
                )

    for role in spec.get("roles", []):
        for index, gate_ref in enumerate(role.get("canApprove", []) or []):
            if gate_ref not in gate_id_set:
                report.add(
                    "cross-refs",
                    f"$.roles[id={role.get('id')}].canApprove[{index}]",
                    f"gate {gate_ref!r} does not resolve",
                )

    for gate in spec.get("gates", []):
        role_ref = gate.get("approvalRole")
        if role_ref is not None and role_ref not in role_ids:
            report.add(
                "cross-refs",
                f"$.gates[id={gate.get('id')}].approvalRole",
                f"role {role_ref!r} does not resolve",
            )
        decision = gate.get("decision") or {}
        for index, inp in enumerate(decision.get("inputs", []) or []):
            if inp not in case_file_ids:
                report.add(
                    "cross-refs",
                    f"$.gates[id={gate.get('id')}].decision.inputs[{index}]",
                    f"case file item {inp!r} does not resolve",
                )
        for rule_index, rule in enumerate(decision.get("rules", []) or []):
            effect = rule.get("effect") or {}
            transition_to = effect.get("transitionTo")
            if transition_to is not None and transition_to not in all_states:
                report.add(
                    "cross-refs",
                    f"$.gates[id={gate.get('id')}].decision.rules[{rule_index}].effect.transitionTo",
                    f"state {transition_to!r} does not resolve",
                )
            for ev_index, ev in enumerate(effect.get("recordEvidence", []) or []):
                if ev not in case_file_ids:
                    report.add(
                        "cross-refs",
                        f"$.gates[id={gate.get('id')}].decision.rules[{rule_index}].effect.recordEvidence[{ev_index}]",
                        f"case file item {ev!r} does not resolve",
                    )

    for lane in spec.get("lanes", []):
        for prop in ("evidenceInputs", "evidenceOutputs"):
            for index, ev in enumerate(lane.get(prop, []) or []):
                if ev not in case_file_ids:
                    report.add(
                        "cross-refs",
                        f"$.lanes[id={lane.get('id')}].{prop}[{index}]",
                        f"case file item {ev!r} does not resolve",
                    )

    for index, pattern in enumerate(spec.get("riskPatterns", []) or []):
        for ev_index, ev in enumerate(pattern.get("evidenceRefs", []) or []):
            if ev not in case_file_ids:
                report.add(
                    "cross-refs",
                    f"$.riskPatterns[{index}].evidenceRefs[{ev_index}]",
                    f"case file item {ev!r} does not resolve",
                )

    for index, impl in enumerate(spec.get("controlAssessment", {}).get("controlImplementations", []) or []):
        ev_refs = (impl.get("implementedBy") or {}).get("evidence", []) or []
        for ev_index, ev in enumerate(ev_refs):
            if ev not in case_file_ids:
                report.add(
                    "cross-refs",
                    f"$.controlAssessment.controlImplementations[{index}].implementedBy.evidence[{ev_index}]",
                    f"case file item {ev!r} does not resolve",
                )

"""Structural round-trip diff between a spec and a lifted package representation."""

from __future__ import annotations

from typing import Any


def spec_skeleton(spec: dict[str, Any]) -> dict[str, Any]:
    """Reduce a spec to the structural surface that round-trip checks."""
    skeleton = {
        "processId": spec["process"]["id"],
        "lanes": [],
        "gates": sorted(g["id"] for g in spec.get("gates", []) or []),
        "evidenceModel": sorted(item["id"] for item in spec.get("evidenceModel", {}).get("caseFileItems", []) or []),
    }
    for lane in spec.get("lanes", []) or []:
        state_model = lane.get("stateModel") or {}
        skeleton["lanes"].append(
            {
                "laneId": lane["id"],
                "states": sorted(s["id"] for s in state_model.get("states", []) or []),
                "transitions": sorted(t.get("id") for t in state_model.get("transitions", []) or [] if t.get("id")),
                "gates": sorted({t.get("gate") for t in state_model.get("transitions", []) or [] if t.get("gate")}),
                "evidenceInputs": sorted(lane.get("evidenceInputs", []) or []),
                "evidenceOutputs": sorted(lane.get("evidenceOutputs", []) or []),
            }
        )
    skeleton["lanes"].sort(key=lambda entry: entry["laneId"])
    return skeleton


def lift_skeleton(lifted: dict[str, Any]) -> dict[str, Any]:
    return {
        "processId": lifted["implementation"]["processId"],
        "lanes": sorted(
            (
                {
                    "laneId": lane["laneId"],
                    "states": sorted(lane["states"]),
                    "transitions": sorted(lane["transitions"]),
                    "gates": sorted(lane["gates"]),
                    "evidenceInputs": sorted(lane["evidenceInputs"]),
                    "evidenceOutputs": sorted(lane["evidenceOutputs"]),
                }
                for lane in lifted["lanes"]
            ),
            key=lambda entry: entry["laneId"],
        ),
        "gates": sorted(lifted["implementation"].get("gates") or {g for lane in lifted["lanes"] for g in lane["gates"]}),
        "evidenceModel": sorted(
            lifted["implementation"].get("evidenceModel")
            or {ev for lane in lifted["lanes"] for ev in lane["evidenceInputs"] + lane["evidenceOutputs"]}
        ),
    }


def diff_skeletons(spec_skel: dict[str, Any], lift_skel: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if spec_skel["processId"] != lift_skel["processId"]:
        issues.append(f"processId differs: spec={spec_skel['processId']!r}, lift={lift_skel['processId']!r}")
    spec_lanes = {entry["laneId"]: entry for entry in spec_skel["lanes"]}
    lift_lanes = {entry["laneId"]: entry for entry in lift_skel["lanes"]}
    for lane_id in sorted(set(spec_lanes) | set(lift_lanes)):
        if lane_id not in spec_lanes:
            issues.append(f"lane {lane_id!r} present in lift but not spec")
            continue
        if lane_id not in lift_lanes:
            issues.append(f"lane {lane_id!r} present in spec but not lift")
            continue
        for key in ("states", "transitions", "gates", "evidenceInputs", "evidenceOutputs"):
            if spec_lanes[lane_id][key] != lift_lanes[lane_id][key]:
                issues.append(
                    f"lane {lane_id!r} {key} differs:\n"
                    f"  spec: {spec_lanes[lane_id][key]}\n"
                    f"  lift: {lift_lanes[lane_id][key]}"
                )
    if spec_skel["gates"] != lift_skel["gates"]:
        issues.append(f"top-level gate set differs:\n  spec: {spec_skel['gates']}\n  lift: {lift_skel['gates']}")
    spec_evidence = set(spec_skel["evidenceModel"])
    lift_evidence = set(lift_skel["evidenceModel"])
    missing_in_lift = spec_evidence - lift_evidence
    extra_in_lift = lift_evidence - spec_evidence
    if missing_in_lift:
        issues.append(f"evidence ids missing from lift: {sorted(missing_in_lift)}")
    if extra_in_lift:
        issues.append(f"evidence ids in lift but not spec: {sorted(extra_in_lift)}")
    return issues

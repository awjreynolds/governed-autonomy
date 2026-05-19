"""Generate implementation.v1.yml binding the spec to the generated skill package."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .context import GeneratorContext


def _content_hash(items: list[tuple[str, str]]) -> str:
    digest = hashlib.sha256()
    for path, body in sorted(items):
        digest.update(path.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(body.encode("utf-8"))
        digest.update(b"\x01")
    return digest.hexdigest()


def render_implementation_map(
    ctx: GeneratorContext,
    skill_id_for_lane: dict[str, str],
    generated_files: list[tuple[str, str]],
) -> str:
    lane_impls: list[dict[str, Any]] = []
    for lane in ctx.spec.get("lanes", []) or []:
        state_model = lane.get("stateModel") or {}
        transitions = state_model.get("transitions") or []
        gate_ids = sorted({t.get("gate") for t in transitions if t.get("gate")})
        lane_impls.append({
            "laneId": lane["id"],
            "skill": skill_id_for_lane[lane["id"]],
            "command": f"/{ctx.process_id}:{lane['id']}",
            "states": [s["id"] for s in state_model.get("states", []) or []],
            "transitions": [t["id"] for t in transitions if "id" in t],
            "gates": gate_ids,
            "evidenceInputs": list(lane.get("evidenceInputs", []) or []),
            "evidenceOutputs": list(lane.get("evidenceOutputs", []) or []),
        })

    fingerprint = _content_hash(generated_files)

    payload = {
        "implementationVersion": "1.0",
        "processSpec": str(Path(ctx.spec_path).name),
        "processId": ctx.process_id,
        "implementationType": "agent_skill_package",
        "packageManifest": "agent-skills.json",
        "skillsRoot": "skills",
        "commandsRoot": "commands",
        "generatedBy": "gaps-v1-generator",
        "implementationFingerprint": {
            "algorithm": "sha256",
            "value": fingerprint,
        },
        "laneImplementations": lane_impls,
        "controlPlaneActions": list(ctx.spec.get("controlPlaneActions", []) or []),
    }
    # YAML emit: defer to v1 migrator renderer for stability.
    from gaps_v1_migrator.render import render

    return render(payload)


def fingerprint_files(files: list[tuple[str, str]]) -> str:
    return _content_hash(files)

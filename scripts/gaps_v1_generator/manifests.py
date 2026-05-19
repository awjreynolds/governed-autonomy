"""Generate package manifests (agent-skills.json, plugin.json, gemini-extension.json)."""

from __future__ import annotations

import json
from typing import Any

from .context import GeneratorContext


def _commands(ctx: GeneratorContext, skill_id_for_lane: dict[str, str]) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    for lane in ctx.spec.get("lanes", []) or []:
        skill_id = skill_id_for_lane[lane["id"]]
        commands.append({
            "command": f"/{ctx.process_id}:{lane['id']}",
            "skill": skill_id,
            "path": f"skills/{skill_id}",
            "purpose": (lane.get("purpose") or lane.get("label") or "").strip().splitlines()[0] if (lane.get("purpose") or lane.get("label")) else skill_id,
        })
    return commands


def agent_skills_json(ctx: GeneratorContext, skill_id_for_lane: dict[str, str]) -> str:
    payload = {
        "schemaVersion": "1.0",
        "name": ctx.process_id,
        "displayName": ctx.process_name,
        "version": "0.1.0",
        "description": (ctx.spec.get("process", {}).get("purpose") or "").strip().splitlines()[0] if ctx.spec.get("process", {}).get("purpose") else ctx.process_name,
        "license": "MIT",
        "canonicalSkillRoot": "skills",
        "commands": _commands(ctx, skill_id_for_lane),
        "generatedBy": "gaps-v1-generator",
    }
    return json.dumps(payload, indent=2) + "\n"


def claude_plugin_json(ctx: GeneratorContext, skill_id_for_lane: dict[str, str]) -> str:
    payload = {
        "schemaVersion": "1.0",
        "name": ctx.process_id,
        "displayName": ctx.process_name,
        "version": "0.1.0",
        "commands": [c["command"] for c in _commands(ctx, skill_id_for_lane)],
        "generatedBy": "gaps-v1-generator",
    }
    return json.dumps(payload, indent=2) + "\n"


def gemini_extension_json(ctx: GeneratorContext, skill_id_for_lane: dict[str, str]) -> str:
    payload = {
        "schemaVersion": "1.0",
        "name": ctx.process_id,
        "version": "0.1.0",
        "commands": _commands(ctx, skill_id_for_lane),
        "generatedBy": "gaps-v1-generator",
    }
    return json.dumps(payload, indent=2) + "\n"

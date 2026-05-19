# GAPS v1.0.0 Phase 4: Generator

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a spec-driven skill-package generator that produces a usable governed-autonomy skill package from a `generative`-conformance v1 spec without humans authoring skill content. Promote the `benefits-eligibility-review` reference spec to `generative` conformance and prove the generator end-to-end on it.

**Architecture:** `scripts/generate-gaps-skill-package.py` (v1) reads a generative-conformance spec, loads its referenced catalogs, and emits one `SKILL.md` per lane plus manifests and command adapters. Skill content is derived structurally: Input Quality Gate from the lane's `evidenceInputs[].shape.required`, Rules from `authority.allowedActions[]` and `authority.prohibitedActions[]` with action catalog definitions inlined verbatim, State Loop as a Markdown state-transition table, Gates as Markdown decision tables, Stop Conditions from terminal states plus escalating gate paths, Evidence To Produce from `evidenceOutputs[]`. The generator emits a deterministic byte-identical package for unchanged inputs. A new `implementation.v1.yml` is generated alongside the skills so Phase 5's round-trip can verify the binding. The v0.1 generator is left in place for the deprecation window.

**Tech Stack:** Python 3 stdlib, the catalogs and v1 schema from Phase 1, the validator package from Phase 2, the renderer from Phase 3.

---

## File Structure

**New files:**
- `scripts/generate-gaps-skill-package-v1.py` — CLI entry
- `scripts/gaps_v1_generator/__init__.py`
- `scripts/gaps_v1_generator/context.py` — load spec, catalogs, build a generator context
- `scripts/gaps_v1_generator/skill_md.py` — compose `SKILL.md` per lane
- `scripts/gaps_v1_generator/manifests.py` — agent-skills.json, plugin.json, gemini-extension.json
- `scripts/gaps_v1_generator/adapters.py` — commands/<process>/<command>.md and .toml
- `scripts/gaps_v1_generator/implementation_map.py` — implementation.v1.yml
- `scripts/gaps_v1_generator/markdown.py` — small Markdown table helpers
- `tests/gaps/v1/test_generator.py`
- `tests/gaps/v1/fixtures/generated/.gitkeep` — placeholder; test outputs go here when needed
- `gaps/examples/v1/benefits-eligibility-review/expected/` — golden generated package directory

**Modified files:**
- `gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml` — promoted to `generative` once the generator demonstrates round-trip
- `scripts/validate-governed-autonomy.sh` — regenerate the pilot package in check-mode
- `gaps/README.md` — note generator capability and the generative pilot

---

### Task 1: Generator scaffold and context loader

**Files:**
- Create: `scripts/gaps_v1_generator/__init__.py`
- Create: `scripts/gaps_v1_generator/context.py`
- Create: `scripts/gaps_v1_generator/markdown.py`

- [ ] **Step 1: Create the package**

```bash
mkdir -p scripts/gaps_v1_generator
touch scripts/gaps_v1_generator/__init__.py
```

- [ ] **Step 2: Write the context loader**

Create `scripts/gaps_v1_generator/context.py`:

```python
"""Load a spec and its catalogs into a structured context for generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from gaps_v1_validator.loader import load_yaml, resolve_catalog_path  # noqa: E402


@dataclass
class GeneratorContext:
    spec: dict[str, Any]
    spec_path: Path
    actions_by_id: dict[str, dict[str, Any]]
    evidence_kinds_by_id: dict[str, dict[str, Any]]
    risk_patterns_by_id: dict[str, dict[str, Any]]
    case_file_items_by_id: dict[str, dict[str, Any]] = field(default_factory=dict)
    gates_by_id: dict[str, dict[str, Any]] = field(default_factory=dict)
    roles_by_id: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def process_id(self) -> str:
        return self.spec["process"]["id"]

    @property
    def process_name(self) -> str:
        return self.spec["process"]["name"]


def build_context(spec_path: Path) -> GeneratorContext:
    spec = load_yaml(spec_path)
    substrate = spec.get("substrate", {}) or {}

    actions = load_yaml(resolve_catalog_path(spec_path, substrate["actionCatalog"])).get("actions", [])
    evidence = load_yaml(resolve_catalog_path(spec_path, substrate["evidenceCatalog"])).get("evidenceKinds", [])
    risk = load_yaml(resolve_catalog_path(spec_path, substrate["riskPatternCatalog"])).get("riskPatterns", [])

    actions_by_id = {entry["id"]: entry for entry in actions}
    for local in spec.get("process", {}).get("localActions", []) or []:
        actions_by_id.setdefault(local["id"], local)

    return GeneratorContext(
        spec=spec,
        spec_path=spec_path,
        actions_by_id=actions_by_id,
        evidence_kinds_by_id={entry["id"]: entry for entry in evidence},
        risk_patterns_by_id={entry["id"]: entry for entry in risk},
        case_file_items_by_id={item["id"]: item for item in spec.get("evidenceModel", {}).get("caseFileItems", []) or []},
        gates_by_id={gate["id"]: gate for gate in spec.get("gates", []) or []},
        roles_by_id={role["id"]: role for role in spec.get("roles", []) or []},
    )
```

- [ ] **Step 3: Write small Markdown helpers**

Create `scripts/gaps_v1_generator/markdown.py`:

```python
"""Small Markdown rendering helpers."""

from __future__ import annotations

from typing import Iterable


def table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return ""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    def fmt_row(cells: list[str]) -> str:
        return "| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells)) + " |"
    separator = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    return "\n".join([fmt_row(headers), separator, *[fmt_row(row) for row in rows]])


def bullet_list(items: Iterable[str], indent: int = 0) -> str:
    prefix = " " * indent + "- "
    return "\n".join(prefix + item for item in items)
```

- [ ] **Step 4: Commit Task 1**

```bash
git add scripts/gaps_v1_generator
git commit -m "Add GAPS v1 generator scaffold and context loader"
```

---

### Task 2: Lane SKILL.md composer

**Files:**
- Create: `scripts/gaps_v1_generator/skill_md.py`

The composer renders one `SKILL.md` per lane. Section order: front-matter, Purpose, Input Quality Gate, Rules, State Loop, Gates, Evidence To Produce, Stop Conditions, Non-claim Language. Content is derived directly from the spec and catalogs.

- [ ] **Step 1: Write the composer**

Create `scripts/gaps_v1_generator/skill_md.py`:

```python
"""Compose SKILL.md content for each lane from a generative-conformance spec."""

from __future__ import annotations

from typing import Any

from .context import GeneratorContext
from .markdown import bullet_list, table


_NON_CLAIM = """## Non-claim language

This skill is a generated artifact of a GAPS v1 process specification. It does not by itself constitute regulatory compliance, certification, legal sufficiency, or runtime execution. The spec is the source of truth; do not edit this file by hand — regenerate from the spec instead.
"""


def _skill_id(process_id: str, lane_id: str) -> str:
    return f"{process_id}-{lane_id.replace('_', '-')}"


def _front_matter(process_id: str, lane: dict[str, Any], skill_id: str) -> str:
    description = lane.get("purpose", "").strip().splitlines()
    description_line = description[0] if description else lane.get("label", "")
    return (
        "---\n"
        f"name: {skill_id}\n"
        f"description: {description_line}\n"
        f"process: {process_id}\n"
        f"lane: {lane['id']}\n"
        "generatedBy: gaps-v1-generator\n"
        "doNotEditByHand: true\n"
        "---\n"
    )


def _input_quality_gate(ctx: GeneratorContext, lane: dict[str, Any]) -> str:
    rows: list[list[str]] = []
    for ev_id in lane.get("evidenceInputs", []) or []:
        item = ctx.case_file_items_by_id.get(ev_id)
        if item is None:
            continue
        shape = item.get("shape", {}) or {}
        required_fields = ", ".join(shape.get("required", []) or []) or "—"
        kind = item.get("kind", "—")
        rows.append([ev_id, kind, required_fields])
    if not rows:
        return "## Input Quality Gate\n\nThis lane declares no evidence inputs. Confirm with the process owner before proceeding.\n"
    body = table(["Evidence id", "Kind", "Required fields"], rows)
    return "## Input Quality Gate\n\nBefore acting in this lane, confirm every declared evidence input is present with the required fields.\n\n" + body + "\n"


def _rules(ctx: GeneratorContext, lane: dict[str, Any]) -> str:
    authority = lane.get("authority", {}) or {}
    allowed = authority.get("allowedActions", []) or []
    prohibited = authority.get("prohibitedActions", []) or []

    def _line(action_id: str) -> str:
        entry = ctx.actions_by_id.get(action_id, {})
        label = entry.get("label", action_id)
        definition = " ".join(entry.get("definition", "").split())
        return f"`{action_id}` — **{label}**. {definition}".rstrip()

    allowed_block = bullet_list(_line(a) for a in allowed) if allowed else "_None declared._"
    prohibited_block = bullet_list(_line(a) for a in prohibited) if prohibited else "_None declared._"
    plane = authority.get("plane", "—")
    tier = authority.get("autonomyTier", "—")
    risk = authority.get("riskTier", "—")

    return (
        "## Rules\n\n"
        f"**Authority plane:** `{plane}`  \n"
        f"**Autonomy tier:** `{tier}`  \n"
        f"**Risk tier:** `{risk}`\n\n"
        "### Allowed actions\n\n"
        f"{allowed_block}\n\n"
        "### Prohibited actions\n\n"
        f"{prohibited_block}\n"
    )


def _state_loop(lane: dict[str, Any]) -> str:
    state_model = lane.get("stateModel") or {}
    states = state_model.get("states") or []
    transitions = state_model.get("transitions") or []
    if not states:
        return "## State Loop\n\nThis lane declares no state model. Confirm with the process owner whether a state loop is intentional.\n"

    state_rows = []
    for state in states:
        flags = []
        if state.get("isInitial"):
            flags.append("initial")
        if state.get("isTerminal"):
            flags.append("terminal")
        state_rows.append([state["id"], state.get("label", state["id"]), ", ".join(flags) or "—"])

    transition_rows = []
    for transition in transitions:
        guard = transition.get("guard") or {}
        guard_summary = "—"
        if guard:
            rules = guard.get("rules") or []
            if rules:
                guard_summary = "; ".join((r.get("when") or "") for r in rules)
        transition_rows.append([
            transition.get("id", "—"),
            transition.get("from", "—"),
            transition.get("to", "—"),
            transition.get("gate", "—"),
            guard_summary,
        ])

    states_table = table(["State", "Label", "Flags"], state_rows)
    transitions_table = table(["Transition", "From", "To", "Gate", "Guard rules"], transition_rows) if transition_rows else ""
    chunks = ["## State Loop\n\n### States\n\n" + states_table + "\n"]
    if transitions_table:
        chunks.append("### Transitions\n\n" + transitions_table + "\n")
    return "\n".join(chunks)


def _gates(ctx: GeneratorContext, lane: dict[str, Any]) -> str:
    state_model = lane.get("stateModel") or {}
    transitions = state_model.get("transitions") or []
    lane_gate_ids = {transition.get("gate") for transition in transitions if transition.get("gate")}
    if not lane_gate_ids:
        return "## Gates\n\nThis lane does not own any gates directly. Refer to upstream lanes for approval gates that apply.\n"
    chunks = ["## Gates\n"]
    for gate_id in sorted(g for g in lane_gate_ids if g):
        gate = ctx.gates_by_id.get(gate_id)
        if not gate:
            continue
        chunks.append(_render_gate(gate))
    return "\n".join(chunks)


def _render_gate(gate: dict[str, Any]) -> str:
    decision = gate.get("decision") or {}
    rules = decision.get("rules") or []
    inputs = decision.get("inputs") or []
    else_clause = decision.get("else") or "(none)"
    rule_rows = []
    for rule in rules:
        effect = rule.get("effect") or {}
        effect_parts = []
        if effect.get("transitionTo"):
            effect_parts.append(f"→ `{effect['transitionTo']}`")
        if effect.get("recordEvidence"):
            recorded = ", ".join(effect["recordEvidence"])
            effect_parts.append(f"record: {recorded}")
        rule_rows.append([
            rule.get("when", "—"),
            rule.get("then", "—"),
            "; ".join(effect_parts) or "—",
        ])
    rules_table = table(["When", "Then", "Effect"], rule_rows) if rule_rows else "_No decision rules declared._"
    inputs_block = ", ".join(inputs) if inputs else "—"
    return (
        f"### Gate `{gate['id']}` — {gate.get('label', gate['id'])}\n\n"
        f"**Type:** `{gate.get('gateType', '—')}`  \n"
        f"**Approval role:** `{gate.get('approvalRole', '—')}`  \n"
        f"**Approval condition:** {gate.get('approvalCondition', '—')}  \n"
        f"**Escalation condition:** {gate.get('escalationCondition', '—')}\n\n"
        f"**Decision inputs:** {inputs_block}\n\n"
        f"{rules_table}\n\n"
        f"**Else:** `{else_clause}`\n"
    )


def _evidence_to_produce(ctx: GeneratorContext, lane: dict[str, Any]) -> str:
    outputs = lane.get("evidenceOutputs", []) or []
    if not outputs:
        return "## Evidence To Produce\n\nThis lane declares no evidence outputs. Confirm with the process owner whether the lane should produce any auditable evidence.\n"
    rows: list[list[str]] = []
    for ev_id in outputs:
        item = ctx.case_file_items_by_id.get(ev_id, {})
        shape = item.get("shape", {}) or {}
        required = ", ".join(shape.get("required", []) or []) or "—"
        rows.append([ev_id, item.get("kind", "—"), required, item.get("retentionPolicy", "—")])
    body = table(["Evidence id", "Kind", "Required fields", "Retention"], rows)
    return "## Evidence To Produce\n\nProduce the following evidence before leaving this lane. Use the spec's `evidenceModel.caseFileItems[]` shape exactly.\n\n" + body + "\n"


def _stop_conditions(ctx: GeneratorContext, lane: dict[str, Any]) -> str:
    state_model = lane.get("stateModel") or {}
    terminals = [state for state in state_model.get("states", []) or [] if state.get("isTerminal")]
    transitions = state_model.get("transitions") or []
    items: list[str] = []
    for terminal in terminals:
        items.append(f"Lane reaches terminal state `{terminal['id']}` ({terminal.get('label', '')}).")
    for transition in transitions:
        guard = transition.get("guard") or {}
        if guard.get("else") == "block":
            items.append(f"Transition `{transition.get('id', '')}` from `{transition.get('from', '')}` is guarded; if no rule allows it, the lane stops and escalates.")
    for gate_id, gate in ctx.gates_by_id.items():
        if gate.get("gateType") == "escalating":
            items.append(f"Gate `{gate_id}` is escalating; reaching it pauses the lane until human approval.")
    if not items:
        return "## Stop Conditions\n\nNo automated stop conditions are declared. Escalate any time the lane lacks evidence, scope, or authority.\n"
    return "## Stop Conditions\n\n" + bullet_list(items) + "\n"


def compose_lane_skill(ctx: GeneratorContext, lane: dict[str, Any]) -> tuple[str, str]:
    """Return (skill_id, skill_md_content) for the lane."""
    skill_id = _skill_id(ctx.process_id, lane["id"])
    sections = [
        _front_matter(ctx.process_id, lane, skill_id),
        f"# {ctx.process_name} — {lane.get('label', lane['id'])}\n",
        f"## Purpose\n\n{lane.get('purpose', '').rstrip()}\n",
        _input_quality_gate(ctx, lane),
        _rules(ctx, lane),
        _state_loop(lane),
        _gates(ctx, lane),
        _evidence_to_produce(ctx, lane),
        _stop_conditions(ctx, lane),
        _NON_CLAIM,
    ]
    return skill_id, "\n".join(section.rstrip() + "\n" for section in sections)
```

- [ ] **Step 2: Commit Task 2**

```bash
git add scripts/gaps_v1_generator/skill_md.py scripts/gaps_v1_generator/markdown.py
git commit -m "Add GAPS v1 lane SKILL.md composer"
```

---

### Task 3: Manifest and adapter composers

**Files:**
- Create: `scripts/gaps_v1_generator/manifests.py`
- Create: `scripts/gaps_v1_generator/adapters.py`

- [ ] **Step 1: Write the manifest composer**

Create `scripts/gaps_v1_generator/manifests.py`:

```python
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
```

- [ ] **Step 2: Write the adapter composer**

Create `scripts/gaps_v1_generator/adapters.py`:

```python
"""Generate per-command adapter files (commands/<process>/<command>.md and .toml)."""

from __future__ import annotations

from typing import Any

from .context import GeneratorContext


def command_md(ctx: GeneratorContext, lane: dict[str, Any], skill_id: str) -> str:
    purpose = (lane.get("purpose") or lane.get("label") or skill_id).strip()
    return (
        f"# /{ctx.process_id}:{lane['id']}\n\n"
        f"**Skill:** `{skill_id}`  \n"
        f"**Purpose:** {purpose}\n\n"
        f"Run this command to invoke the `{skill_id}` skill for the {ctx.process_name} process. The skill follows the rules, state loop, and stop conditions defined by the GAPS v1 spec.\n\n"
        f"_Generated by gaps-v1-generator. Do not edit by hand._\n"
    )


def command_toml(ctx: GeneratorContext, lane: dict[str, Any], skill_id: str) -> str:
    return (
        f"# Generated by gaps-v1-generator. Do not edit by hand.\n"
        f"name = \"/{ctx.process_id}:{lane['id']}\"\n"
        f"skill = \"{skill_id}\"\n"
        f"path = \"skills/{skill_id}\"\n"
    )


def agents_openai_yaml(ctx: GeneratorContext, lane: dict[str, Any], skill_id: str) -> str:
    return (
        f"# Generated by gaps-v1-generator.\n"
        f"name: {skill_id}\n"
        f"description: >\n"
        f"  GAPS-generated skill for the {lane.get('label', lane['id'])} lane of the\n"
        f"  {ctx.process_name} process.\n"
        f"command: /{ctx.process_id}:{lane['id']}\n"
    )
```

- [ ] **Step 3: Commit Task 3**

```bash
git add scripts/gaps_v1_generator/manifests.py scripts/gaps_v1_generator/adapters.py
git commit -m "Add GAPS v1 generator manifest and adapter composers"
```

---

### Task 4: Implementation map composer

**Files:**
- Create: `scripts/gaps_v1_generator/implementation_map.py`

The implementation map declares the binding between the spec and the generated skill package. Phase 5 uses it for round-trip checks. The map declares which states, transitions, and gates each generated skill implements; that lets the round-trip diff compute spec-skill equivalence.

- [ ] **Step 1: Write the composer**

Create `scripts/gaps_v1_generator/implementation_map.py`:

```python
"""Generate implementation.v1.yml binding the spec to the generated skill package."""

from __future__ import annotations

import hashlib
import json
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
```

- [ ] **Step 2: Commit Task 4**

```bash
git add scripts/gaps_v1_generator/implementation_map.py
git commit -m "Add GAPS v1 generator implementation-map composer"
```

---

### Task 5: Generator CLI

**Files:**
- Create: `scripts/generate-gaps-skill-package-v1.py`

- [ ] **Step 1: Write the CLI**

Create `scripts/generate-gaps-skill-package-v1.py`:

```python
#!/usr/bin/env python3
"""Generate a GAPS v1 skill package from a generative-conformance spec."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.dont_write_bytecode = True

from gaps_v1_generator.adapters import agents_openai_yaml, command_md, command_toml  # noqa: E402
from gaps_v1_generator.context import build_context  # noqa: E402
from gaps_v1_generator.implementation_map import render_implementation_map  # noqa: E402
from gaps_v1_generator.manifests import agent_skills_json, claude_plugin_json, gemini_extension_json  # noqa: E402
from gaps_v1_generator.skill_md import compose_lane_skill  # noqa: E402


def _files_for_spec(spec_path: Path) -> list[tuple[str, str]]:
    ctx = build_context(spec_path)
    files: list[tuple[str, str]] = []
    skill_id_for_lane: dict[str, str] = {}

    for lane in ctx.spec.get("lanes", []) or []:
        skill_id, body = compose_lane_skill(ctx, lane)
        skill_id_for_lane[lane["id"]] = skill_id
        files.append((f"skills/{skill_id}/SKILL.md", body))
        files.append((f"skills/{skill_id}/agents/openai.yaml", agents_openai_yaml(ctx, lane, skill_id)))
        files.append((f"commands/{ctx.process_id}/{lane['id']}.md", command_md(ctx, lane, skill_id)))
        files.append((f"commands/{ctx.process_id}/{lane['id']}.toml", command_toml(ctx, lane, skill_id)))

    files.append(("agent-skills.json", agent_skills_json(ctx, skill_id_for_lane)))
    files.append((".claude-plugin/plugin.json", claude_plugin_json(ctx, skill_id_for_lane)))
    files.append(("gemini-extension.json", gemini_extension_json(ctx, skill_id_for_lane)))
    files.append(("implementation.v1.yml", render_implementation_map(ctx, skill_id_for_lane, files)))
    return files


def _write_or_check(target_root: Path, files: list[tuple[str, str]], check: bool) -> int:
    if not check:
        if target_root.exists():
            shutil.rmtree(target_root)
        target_root.mkdir(parents=True, exist_ok=True)
        for relative, body in files:
            path = target_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
            print(f"wrote {path}")
        return 0
    differ = False
    for relative, body in files:
        path = target_root / relative
        if not path.exists():
            print(f"MISSING: {path}", file=sys.stderr)
            differ = True
            continue
        existing = path.read_text(encoding="utf-8")
        if existing != body:
            print(f"DIFFER: {path}", file=sys.stderr)
            differ = True
    return 1 if differ else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to a generative-conformance ga-process.v1.yml")
    parser.add_argument("--output-root", type=Path, default=None,
                        help="Destination root. Default: gaps/generated/<process-id>/")
    parser.add_argument("--check", action="store_true", help="Fail if the generated output would differ from existing files.")
    parser.add_argument("--validate-after", action="store_true", help="Run validate-gaps-v1 on the spec at --level generative before generation.")
    args = parser.parse_args()

    if args.validate_after:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "validate-gaps-v1.py"), str(args.spec), "--level", "generative"],
            cwd=REPO_ROOT,
            check=False,
        )
        if result.returncode != 0:
            print("FAIL: spec does not meet generative conformance; refusing to generate.", file=sys.stderr)
            return 1

    files = _files_for_spec(args.spec)
    output_root = args.output_root or (REPO_ROOT / "gaps" / "generated" / args.spec.parent.name)
    return _write_or_check(output_root, files, args.check)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Commit Task 5**

```bash
chmod +x scripts/generate-gaps-skill-package-v1.py
git add scripts/generate-gaps-skill-package-v1.py
git commit -m "Add GAPS v1 generator CLI"
```

---

### Task 6: Promote benefits-eligibility-review to generative conformance

The pilot reference spec is brought to `generative` conformance. The Phase 3 spec is close: state models exist, gates have decisions, evidence inputs reference shape.required. The remaining gap is that the spec declares `machine-validatable` and lacks `freshness.implementationFingerprint`. The fingerprint is filled in by the generator's first run; conformance gating already accepts the spec once everything resolves.

**Files:**
- Modify: `gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml`

- [ ] **Step 1: Confirm current state**

```bash
python3 scripts/validate-gaps-v1.py gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml --level generative
```

If errors are reported, fix them in the spec before promoting. Likely fixes: every lane's evidenceInputs items have `shape.required` non-empty, every blocking gate has a `decision` block (already true in Phase 3), every transition has a `guard` (already true in Phase 3).

Execution note: the pilot spec did report one generative-conformance error here. `evidence_gathering_lane` transition `t-in-progress-to-complete` lacked a guard. Phase 4 fixed that transition guard before promoting the spec.

- [ ] **Step 2: Update the spec's conformance level**

Replace the line `conformanceLevel: machine-validatable` with `conformanceLevel: generative` in `gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml`.

- [ ] **Step 3: Re-validate**

```bash
python3 scripts/validate-gaps-v1.py gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml
```

Expected: passes at default (which now reads the spec-declared `generative`). If it fails, the spec needs further work — surface every issue and address before continuing.

- [ ] **Step 4: Commit Task 6**

```bash
git add gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml
git commit -m "Promote benefits-eligibility-review spec to generative conformance"
```

---

### Task 7: Generate the pilot package and snapshot it

**Files:**
- Create (via generator): `gaps/examples/v1/benefits-eligibility-review/expected/**`

- [ ] **Step 1: Generate**

```bash
python3 scripts/generate-gaps-skill-package-v1.py gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml --output-root gaps/examples/v1/benefits-eligibility-review/expected --validate-after
```

Expected: a `wrote ...` line for each generated file. Approximately: four `SKILL.md`, four `agents/openai.yaml`, four command `.md`, four command `.toml`, one `agent-skills.json`, one `.claude-plugin/plugin.json`, one `gemini-extension.json`, one `implementation.v1.yml`.

- [ ] **Step 2: Inspect a generated SKILL.md**

Open `gaps/examples/v1/benefits-eligibility-review/expected/skills/benefits-eligibility-review-evidence-gathering-lane/SKILL.md`.

Confirm visually that:

- The Input Quality Gate section lists the lane's actual evidence inputs with required fields.
- The Rules section contains the catalog definitions inlined (not template language).
- The State Loop section shows the lane's actual states and transitions.
- Stop Conditions reference real terminal states.
- Evidence To Produce lists `supporting-evidence` with the right shape.

No edits to the generated file — if anything looks wrong, fix the generator and regenerate.

- [ ] **Step 3: Commit the snapshot**

```bash
git add gaps/examples/v1/benefits-eligibility-review/expected
git commit -m "Snapshot generated package for benefits-eligibility-review pilot"
```

- [ ] **Step 4: Verify --check mode passes**

```bash
python3 scripts/generate-gaps-skill-package-v1.py gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml --output-root gaps/examples/v1/benefits-eligibility-review/expected --check
```

Expected: exit 0 (no DIFFER lines).

- [ ] **Step 5: Verify deterministic regeneration**

```bash
python3 scripts/generate-gaps-skill-package-v1.py gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml --output-root /tmp/gaps-regen
diff -r gaps/examples/v1/benefits-eligibility-review/expected /tmp/gaps-regen
rm -rf /tmp/gaps-regen
```

Expected: `diff` produces no output. If it does, the generator has a nondeterminism (probably an unsorted dict iteration); fix the generator.

---

### Task 8: Generator tests

**Files:**
- Create: `tests/gaps/v1/test_generator.py`

- [ ] **Step 1: Write the tests**

Create `tests/gaps/v1/test_generator.py`:

```python
"""Tests for the GAPS v1 generator."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "generate-gaps-skill-package-v1.py"
PILOT_SPEC = ROOT / "gaps" / "examples" / "v1" / "benefits-eligibility-review" / "ga-process.v1.yml"
EXPECTED_ROOT = ROOT / "gaps" / "examples" / "v1" / "benefits-eligibility-review" / "expected"


class GeneratorTests(unittest.TestCase):
    def test_check_mode_matches_snapshot(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(PILOT_SPEC), "--output-root", str(EXPECTED_ROOT), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_deterministic_regeneration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(PILOT_SPEC), "--output-root", tmp],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            diff = subprocess.run(["diff", "-r", str(EXPECTED_ROOT), tmp], capture_output=True, text=True, check=False)
            self.assertEqual(diff.returncode, 0, f"snapshots diverge:\n{diff.stdout}")

    def test_generator_refuses_non_generative_with_validate_after(self) -> None:
        non_generative = ROOT / "gaps" / "examples" / "v1" / "minimal" / "ga-process.v1.yml"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(non_generative), "--output-root", str(EXPECTED_ROOT) + "-tmp", "--validate-after"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("generative conformance", result.stderr.lower() + result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests**

```bash
python3 -m unittest tests.gaps.v1.test_generator -v
```

Expected: all three tests pass.

- [ ] **Step 3: Commit Task 8**

```bash
git add tests/gaps/v1/test_generator.py
git commit -m "Add GAPS v1 generator tests"
```

---

### Task 9: Wire generator into validation suite and docs

**Files:**
- Modify: `scripts/validate-governed-autonomy.sh`
- Modify: `gaps/README.md`

- [ ] **Step 1: Add generator check to the suite**

Edit `scripts/validate-governed-autonomy.sh` and add before the test discovery line:

```bash
echo "==> Checking GAPS v1 pilot generator output is up to date"
python3 scripts/generate-gaps-skill-package-v1.py gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml --output-root gaps/examples/v1/benefits-eligibility-review/expected --check
```

- [ ] **Step 2: Update `gaps/README.md`**

Append to the v1 incubation section:

```markdown
### v1 generator

A generative-conformance spec drives the generator:

\`\`\`bash
python3 scripts/generate-gaps-skill-package-v1.py gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml --output-root gaps/generated/benefits-eligibility-review --validate-after
\`\`\`

The pilot package lives at `gaps/examples/v1/benefits-eligibility-review/expected/`. The generator produces a deterministic byte-identical package for unchanged input.
```

- [ ] **Step 3: Run the full validation suite**

```bash
./scripts/validate-governed-autonomy.sh
```

Expected: green; final line `All Governed Autonomy validation checks passed.`

- [ ] **Step 4: Commit Task 9**

```bash
git add scripts/validate-governed-autonomy.sh gaps/README.md
git commit -m "Wire GAPS v1 generator into repo validation suite"
```

---

## Self-Review Checklist

- Skill content is derived from spec structure: no template strings for Input Quality Gate, Rules, State Loop, Gates, Stop Conditions, or Evidence To Produce.
- Generator output is deterministic; diff-clean regeneration is enforced by `--check` and by a test.
- A generative-conformance spec drives the pilot; non-generative specs are refused when `--validate-after` is passed.
- Generated `implementation.v1.yml` carries a fingerprint over the rest of the generated files; spec edits that change skill content change the fingerprint.
- The generator does not require human content authoring between spec and package. This is the v1 acceptance test for "rigorous enough for LLMs to construct skills from."

## What Phase 4 does NOT do

- Does not lift a skill package back to a spec (Phase 5).
- Does not round-trip-diff spec and skill content (Phase 5).
- Does not produce a release; v1.0.0 lifts in Phase 5.
- Does not promote the migrated v0.1 ports beyond their current conformance levels (deliberate — those uplifts are human decisions per process).

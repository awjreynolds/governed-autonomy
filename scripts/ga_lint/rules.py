"""Deterministic governance.yml lint rules."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .catalog import ACTION_CATEGORIES, CatalogIndex
from .errors import ValidationIssue
from .loader import resolve_repo_path
from .merge import merge_authority


AUTONOMY_TIERS = [
    "human_only",
    "assist",
    "recommend",
    "draft",
    "execute_with_approval",
    "execute_within_limits",
    "autonomous_with_monitoring",
]
STEP_KINDS = {"execute", "investigate", "decide", "approve", "monitor"}


def _issue(rule: str, path: str, message: str, severity: str = "error") -> ValidationIssue:
    return ValidationIssue(rule=rule, path=path, message=message, severity=severity)  # type: ignore[arg-type]


def _nonnull(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() != "unknown"
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _items(value: Any) -> Iterable[Any]:
    return value if isinstance(value, list) else []


def _refs(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        if ":" in value:
            yield value
        return
    if isinstance(value, list):
        for item in value:
            yield from _refs(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            yield from _refs(item)


def _id(ref: str, prefix: str) -> str:
    return ref.removeprefix(prefix)


def _roles(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {role.get("id"): role for role in _items(doc.get("roles")) if isinstance(role, dict) and role.get("id")}


def _steps(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {step.get("id"): step for step in _items(doc.get("steps")) if isinstance(step, dict) and step.get("id")}


def _evidence(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item.get("id"): item for item in _items((doc.get("evidence") or {}).get("items")) if isinstance(item, dict) and item.get("id")}


def _gates(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [gate for gate in _items(doc.get("gates")) if isinstance(gate, dict)]


def _local_defs(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {key: value for key, value in (doc.get("local_definitions") or {}).items() if isinstance(value, dict)}


def lint(doc: dict[str, Any], governance_path: Path, catalog: CatalogIndex, skills_dir: Path | None = None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    skills_dir = skills_dir or governance_path.parent / "skills"
    authority = doc.get("authority") or {}
    roles = _roles(doc)
    steps = _steps(doc)
    evidence = _evidence(doc)

    # E001
    required = [
        ("process.id", (doc.get("process") or {}).get("id")),
        ("process.name", (doc.get("process") or {}).get("name")),
        ("roles", doc.get("roles")),
        ("authority.default_allowed_actions", authority.get("default_allowed_actions")),
        ("authority.prohibited_actions", authority.get("prohibited_actions")),
        ("evidence.destination", (doc.get("evidence") or {}).get("destination")),
        ("escalation", doc.get("escalation")),
    ]
    for path, value in required:
        if not _nonnull(value):
            issues.append(_issue("E001", path, "core governance field is missing or empty"))

    # E002 / E009
    if not any(_nonnull(role.get("accountable_for")) and str(role.get("accountable_for")).strip().lower() != "nothing" for role in roles.values()):
        issues.append(_issue("E002", "roles", "no non-autonomous accountability owner is declared"))
    for role_id, role in roles.items():
        if role.get("autonomous") is True and _nonnull(role.get("accountable_for")) and str(role.get("accountable_for")).strip().lower() != "nothing":
            issues.append(_issue("E009", f"roles.{role_id}.accountable_for", "autonomous agents cannot own accountability"))

    # E003 refs
    local_defs = _local_defs(doc)
    for ref in sorted(set(_refs(doc))):
        if ref.startswith("catalog:") and not catalog.exists(ref):
            issues.append(_issue("E003a", ref, "catalog reference does not exist"))
        if ref.startswith("local:"):
            key = _id(ref, "local:")
            definition = local_defs.get(key, {})
            if not definition or len(str(definition.get("definition", "")).strip()) < 20:
                issues.append(_issue("E003b", ref, "local reference has no definition of at least 20 characters"))
            if definition.get("category") not in ACTION_CATEGORIES:
                issues.append(_issue("E003b", ref, "local reference category is missing or invalid"))
        if ref.startswith("role:") and _id(ref, "role:") not in roles:
            issues.append(_issue("E003c", ref, "role reference does not resolve"))
        if ref.startswith("step:") and _id(ref, "step:") not in steps:
            issues.append(_issue("E003c", ref, "step reference does not resolve"))
        if ref.startswith("evidence:") and _id(ref, "evidence:") not in evidence:
            issues.append(_issue("E003c", ref, "evidence reference does not resolve"))

    # E004 / E010 / W007
    evidence_producers: dict[str, list[dict[str, Any]]] = {}
    for ev_id, ev in evidence.items():
        producer = ev.get("producer")
        if isinstance(producer, str) and producer.startswith("step:") and _id(producer, "step:") in steps:
            evidence_producers.setdefault(ev_id, []).append(steps[_id(producer, "step:")])
    for index, gate in enumerate(_gates(doc)):
        required_evidence = [_id(ref, "evidence:") for ref in _items(gate.get("requires_evidence")) if isinstance(ref, str) and ref.startswith("evidence:")]
        if not gate.get("blocks_steps"):
            issues.append(_issue("W007", f"gates[{index}].blocks_steps", "gate does not block any steps", "warning"))
        for ev_id in required_evidence:
            producers = evidence_producers.get(ev_id, [])
            if not producers:
                issues.append(_issue("E010", f"gates[{index}].requires_evidence", f"evidence:{ev_id} is required but no step produces it"))
            for producer in producers:
                if producer.get("step_kind") == "execute" and producer.get("requires_role") == gate.get("requires_role"):
                    issues.append(_issue("E004", f"gates[{index}].requires_role", "same role executes evidence-producing work and approves it"))

    # E005 / E011 / E012 / E014 / W004 / W005 / W009
    if not steps:
        issues.append(_issue("E013", "steps", "governance.yml must define at least one step"))
    for step_id, step in steps.items():
        effective = merge_authority(authority, step)
        for action in sorted(set(effective.allowed_actions) & set(effective.prohibited_actions)):
            issues.append(_issue("E005", f"steps.{step_id}.authority", f"{action} is both allowed and prohibited"))
        skill_path = skills_dir / step_id / "SKILL.md"
        if not skill_path.exists():
            issues.append(_issue("E006", f"steps.{step_id}", f"missing skills/{step_id}/SKILL.md"))
        role_ref = step.get("requires_role")
        if not isinstance(role_ref, str) or not role_ref.startswith("role:") or _id(role_ref, "role:") not in roles:
            issues.append(_issue("E012", f"steps.{step_id}.requires_role", "step requires_role is missing or does not resolve"))
        if step.get("step_kind") not in STEP_KINDS:
            issues.append(_issue("E014", f"steps.{step_id}.step_kind", "step_kind is missing or invalid"))
        if len(str(step.get("purpose", "")).strip()) < 20:
            issues.append(_issue("W004", f"steps.{step_id}.purpose", "step purpose is missing or too short", "warning"))
        process_tier = AUTONOMY_TIERS.index(authority.get("default_autonomy_tier", "draft")) if authority.get("default_autonomy_tier") in AUTONOMY_TIERS else 3
        step_tier = AUTONOMY_TIERS.index(effective.autonomy_tier) if effective.autonomy_tier in AUTONOMY_TIERS else process_tier
        justification = (step.get("authority_overrides") or {}).get("justification")
        if step_tier > process_tier and len(str(justification or "").strip()) < 20:
            issues.append(_issue("W005", f"steps.{step_id}.authority_overrides.justification", "more permissive autonomy requires justification", "warning"))
        if effective.autonomy_tier == "human_only":
            role_id = _id(role_ref, "role:") if isinstance(role_ref, str) else ""
            if not role_id or roles.get(role_id, {}).get("autonomous") is True:
                issues.append(_issue("W009", f"steps.{step_id}.requires_role", "human_only step must name a non-autonomous role", "warning"))
        if step.get("step_kind") == "investigate":
            for action in effective.allowed_actions:
                category = catalog.action_category(action)
                if action.startswith("local:"):
                    category = local_defs.get(_id(action, "local:"), {}).get("category")
                if category != "data-plane-read":
                    issues.append(_issue("E011", f"steps.{step_id}.authority.allowed_actions", f"investigate step allows non-read action {action}"))

    # E007 / E008
    if skills_dir.exists():
        for skill_file in skills_dir.glob("*/SKILL.md"):
            step_id = skill_file.parent.name
            if step_id not in steps:
                issues.append(_issue("E007", str(skill_file.relative_to(governance_path.parent)), "skill has no matching step"))
            text = skill_file.read_text(encoding="utf-8")
            if text.startswith("---"):
                frontmatter = text.split("---", 2)[1]
                if "governance:" in frontmatter:
                    if f"step: {step_id}" not in frontmatter and f"step: \"{step_id}\"" not in frontmatter:
                        issues.append(_issue("E008", str(skill_file.relative_to(governance_path.parent)), "frontmatter governance.step does not match directory"))
                    if "process:" not in frontmatter:
                        issues.append(_issue("E008", str(skill_file.relative_to(governance_path.parent)), "frontmatter governance.process is missing"))

    # W001 / W002 / W003 / W008 / W010
    if not _nonnull((doc.get("freshness") or {}).get("drift_policy")):
        issues.append(_issue("W001", "freshness.drift_policy", "drift policy is undefined", "warning"))
    if not _nonnull((doc.get("risk") or {}).get("blast_radius")):
        issues.append(_issue("W002", "risk.blast_radius", "blast radius is undefined", "warning"))
    for ev_id, ev in evidence.items():
        if not _nonnull(ev.get("consumer")):
            issues.append(_issue("W003", f"evidence.{ev_id}.consumer", "evidence has no consumer", "warning"))
    state = doc.get("state") or {}
    canonical = state.get("canonical")
    if canonical and canonical in _items(state.get("projections")):
        issues.append(_issue("W008", "state.projections", "canonical state is also listed as a projection", "warning"))
    for index, escalation in enumerate(_items(doc.get("escalation"))):
        if isinstance(escalation, dict) and not _nonnull(escalation.get("condition")):
            issues.append(_issue("W010", f"escalation[{index}].condition", "escalation condition is undefined", "warning"))

    return issues


def lint_file(path: Path) -> list[ValidationIssue]:
    from .catalog import load_catalogs
    from .loader import find_repo_root, load_yaml

    doc = load_yaml(path)
    return lint(doc, path, load_catalogs(find_repo_root(path)))


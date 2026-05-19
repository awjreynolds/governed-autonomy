# GAPS v1.0.0 Phase 3: Migration and Reference Spec Ports

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a one-shot migrator from GAPS v0.1 specs to v1 (`descriptive` conformance), port the four existing v0.1 reference specs to v1, and add a fresh `benefits-eligibility-review` casework reference spec authored at `machine-validatable` conformance to stress-test the format on a non-software process.

**Architecture:** `scripts/migrate-gaps-v0-to-v1.py` reads a v0.1 spec, builds a best-effort v1 document, and writes it next to the source. The migrator is deterministic: same input always produces same output. Free-text `allowed`/`prohibited` strings are fuzzy-matched against the v1 action catalog (token-set overlap, case-insensitive); unmatched values become `process.localActions[]` entries with a TODO marker. Free-text `approvalCondition`/`escalationCondition` are preserved verbatim — sufficient for `descriptive` conformance, insufficient for `machine-validatable`. Migration output always declares `conformanceLevel: descriptive`. Reference spec ports run the migrator, then have minor hand-edits to set realistic `roles[].accountabilityScope` text and `evidenceModel.caseFileItems[]` derived from each v0.1 spec's structure. The casework spec is authored fresh in v1, not migrated.

**Tech Stack:** Python 3 stdlib, Ruby YAML→JSON bridge, the v1 schema and validator from Phases 1 and 2.

---

## File Structure

**New files:**
- `scripts/migrate-gaps-v0-to-v1.py`
- `scripts/gaps_v1_migrator/__init__.py`
- `scripts/gaps_v1_migrator/match.py` — fuzzy action matcher
- `scripts/gaps_v1_migrator/render.py` — v1 YAML renderer (deterministic key order)
- `scripts/gaps_v1_migrator/translate.py` — v0.1 → v1 translation
- `tests/gaps/v1/test_migrate.py`
- `gaps/examples/v1/gadd/ga-process.v1.yml`
- `gaps/examples/v1/compliance-review/ga-process.v1.yml`
- `gaps/examples/v1/incident-response/ga-process.v1.yml`
- `gaps/examples/v1/procurement-approval/ga-process.v1.yml`
- `gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml`

**Modified files:**
- `scripts/validate-governed-autonomy.sh` — already picks up `gaps/examples/v1/*/ga-process.v1.yml` from Phase 1's loop, but add an explicit migrator check
- `gaps/README.md` — list v1 reference specs

---

### Task 1: Migrator scaffold and fuzzy action matcher

**Files:**
- Create: `scripts/gaps_v1_migrator/__init__.py`
- Create: `scripts/gaps_v1_migrator/match.py`
- Create: `tests/gaps/v1/test_migrate.py` (initial — matcher tests only)

- [ ] **Step 1: Create the package skeleton**

```bash
mkdir -p scripts/gaps_v1_migrator
touch scripts/gaps_v1_migrator/__init__.py
```

- [ ] **Step 2: Write the matcher tests first**

Create `tests/gaps/v1/test_migrate.py`:

```python
"""Tests for the v0.1 → v1 migrator components."""

from __future__ import annotations

import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from gaps_v1_migrator.match import fuzzy_action_match  # noqa: E402


CATALOG = [
    {"id": "draft-artifact", "label": "Draft a reviewable artifact", "definition": "Produce an artifact intended for human review."},
    {"id": "mutate-external-system", "label": "Mutate state in an external system", "definition": "Change state in an external tracker."},
    {"id": "approve-own-work", "label": "Approve own work", "definition": "The producer of an artifact also approves it."},
    {"id": "edit-repository-file-in-boundary", "label": "Edit repository file within approved boundary", "definition": "Modify code, configuration, or documentation files within an approved boundary."},
    {"id": "run-verification", "label": "Run verification commands", "definition": "Execute tests, linters, type checkers, security scanners."},
]


class FuzzyActionMatchTests(unittest.TestCase):
    def test_exact_label_match(self) -> None:
        match, score = fuzzy_action_match("Draft a reviewable artifact", CATALOG)
        self.assertEqual(match, "draft-artifact")
        self.assertGreater(score, 0.5)

    def test_phrase_overlap(self) -> None:
        match, score = fuzzy_action_match("draft research and PRD artifacts", CATALOG)
        self.assertEqual(match, "draft-artifact")

    def test_external_mutation(self) -> None:
        match, _ = fuzzy_action_match("mutate external issues without human approval", CATALOG)
        self.assertEqual(match, "mutate-external-system")

    def test_approve_own_work(self) -> None:
        match, _ = fuzzy_action_match("approve its own work for closure", CATALOG)
        self.assertEqual(match, "approve-own-work")

    def test_run_tests(self) -> None:
        match, _ = fuzzy_action_match("run tests and local verification commands", CATALOG)
        self.assertEqual(match, "run-verification")

    def test_no_match_returns_none(self) -> None:
        match, score = fuzzy_action_match("xylophone purple wombat hatstand", CATALOG)
        self.assertIsNone(match)
        self.assertLess(score, 0.2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test, confirm import error**

```bash
python3 -m unittest tests.gaps.v1.test_migrate -v
```

Expected: ImportError because `scripts/gaps_v1_migrator/match.py` doesn't exist yet.

- [ ] **Step 4: Implement the matcher**

Create `scripts/gaps_v1_migrator/match.py`:

```python
"""Fuzzy match of v0.1 free-text action prose to v1 action catalog ids."""

from __future__ import annotations

import re
from typing import Any, Optional


_STOPWORDS = {
    "a", "an", "the", "of", "to", "in", "on", "for", "with", "without",
    "and", "or", "by", "from", "into", "out", "as", "at", "is", "are", "be",
    "this", "that", "these", "those", "its", "their", "our", "any", "all",
    "no", "not", "may", "must", "should", "would", "can", "do", "does",
    "did", "will", "shall", "if", "when", "while", "than", "then", "so",
    "via", "per", "make", "made", "making",
}


def _normalize_token(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def _tokenize(text: str) -> set[str]:
    return {
        _normalize_token(token)
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token and token not in _STOPWORDS
    }


def fuzzy_action_match(prose: str, catalog: list[dict[str, Any]]) -> tuple[Optional[str], float]:
    """Return (action-id, score) for the best catalog match.

    Score is Jaccard similarity over token sets of (label + definition) versus
    (prose). Returns (None, score) if no catalog entry exceeds 0.18.
    """
    prose_tokens = _tokenize(prose)
    if not prose_tokens:
        return None, 0.0
    best_id: Optional[str] = None
    best_score = 0.0
    for entry in catalog:
        haystack = " ".join([
            entry.get("label", ""),
            entry.get("definition", ""),
            entry.get("id", "").replace("-", " "),
        ])
        catalog_tokens = _tokenize(haystack)
        if not catalog_tokens:
            continue
        intersection = prose_tokens & catalog_tokens
        union = prose_tokens | catalog_tokens
        score = len(intersection) / len(union)
        # Bonus for high recall of prose tokens in the catalog entry.
        recall = len(intersection) / len(prose_tokens)
        score = 0.6 * score + 0.4 * recall
        if score > best_score:
            best_score = score
            best_id = entry.get("id")
    if best_score < 0.18:
        return None, best_score
    return best_id, best_score
```

- [ ] **Step 5: Run the test, confirm it passes**

```bash
python3 -m unittest tests.gaps.v1.test_migrate -v
```

Expected: six matcher tests PASS.

- [ ] **Step 6: Commit Task 1**

```bash
git add scripts/gaps_v1_migrator tests/gaps/v1/test_migrate.py
git commit -m "Add GAPS v1 migrator scaffold and fuzzy action matcher"
```

---

### Task 2: Deterministic YAML renderer

**Files:**
- Create: `scripts/gaps_v1_migrator/render.py`

The migrator must produce stable, diff-friendly output. Python doesn't ship a YAML serializer with comments, so we hand-roll a renderer for the v1 shape. Keys are emitted in a fixed canonical order. Values are scalar or nested with consistent indentation. Multi-line strings use folded scalars (`>`).

- [ ] **Step 1: Write the renderer**

Create `scripts/gaps_v1_migrator/render.py`:

```python
"""Hand-rolled YAML renderer for v1 spec documents.

Stable output: keys emitted in a fixed canonical order at every level;
strings quoted only when necessary; long strings folded.
"""

from __future__ import annotations

import re
from typing import Any


CANONICAL_KEY_ORDER = [
    "gapsVersion", "specStatus", "conformanceLevel",
    "process", "substrate", "roles", "evidenceModel",
    "lanes", "gates", "controlPlaneActions", "projectionPolicy",
    "riskPatterns", "controlAssessment", "freshness", "knownGaps",
    # nested orders
    "id", "name", "label", "purpose", "scope", "includes", "excludes",
    "localActions", "category", "defaultAutonomyTier", "defaultRiskTier",
    "definition", "justification", "examples", "roleAffinity",
    "alwaysProhibitedAt",
    "oscalControlCatalogs", "oscalProfile",
    "actionCatalog", "evidenceCatalog", "riskPatternCatalog",
    "accountabilityScope", "decisionRights", "canApprove",
    "caseFileItems", "kind", "shape", "required", "optional",
    "producer", "consumer", "retentionPolicy",
    "authority", "plane", "autonomyTier", "riskTier", "allowedActions", "prohibitedActions",
    "stateModel", "states", "transitions",
    "isInitial", "isTerminal", "from", "to", "gate", "guard",
    "inputs", "rules", "when", "then", "effect", "transitionTo", "recordEvidence", "else",
    "evidenceInputs", "evidenceOutputs", "autonomousResponsibilities", "skills",
    "gateType", "approvalRole", "approvalCondition", "escalationCondition", "decision",
    "skill", "actions",
    "canonicalStateSource", "pathPattern", "externalSystems",
    "role", "mutationRequiresApproval",
    "patternRef", "mitigations", "evidenceRefs",
    "catalogRefs", "controlImplementations",
    "controlId", "mappingStatus", "implementedBy", "evidence", "statement",
    "reviewedAt", "implementationFingerprint", "algorithm", "value", "driftPolicy",
    "summary", "severity", "plannedResolution",
]

_KEY_INDEX = {key: index for index, key in enumerate(CANONICAL_KEY_ORDER)}


def _key_sort(key: str) -> tuple[int, str]:
    return (_KEY_INDEX.get(key, len(CANONICAL_KEY_ORDER)), key)


_PLAIN_SAFE = re.compile(r"^[A-Za-z_][A-Za-z0-9_./:\-]*$")
_VERSION_SAFE = re.compile(r"^[0-9]+(?:\.[0-9]+)+$")


def _scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return str(value)
    if not isinstance(value, str):
        raise TypeError(f"unsupported scalar {value!r}")
    if value == "":
        return "\"\""
    if "\n" in value or len(value) > 72:
        body = "\n".join("  " + line for line in value.rstrip().splitlines())
        return ">\n" + body
    if (
        (_PLAIN_SAFE.match(value) or _VERSION_SAFE.match(value))
        and value not in {"true", "false", "null", "yes", "no", "on", "off", "~"}
    ):
        return value
    return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\""


def render(data: Any, indent: int = 0) -> str:
    if isinstance(data, dict):
        lines: list[str] = []
        for key in sorted(data.keys(), key=_key_sort):
            value = data[key]
            prefix = " " * indent + f"{key}:"
            if isinstance(value, dict):
                if not value:
                    lines.append(prefix + " {}")
                else:
                    lines.append(prefix)
                    lines.append(render(value, indent + 2).rstrip())
            elif isinstance(value, list):
                if not value:
                    lines.append(prefix + " []")
                else:
                    lines.append(prefix)
                    for item in value:
                        if isinstance(item, dict):
                            rendered = render(item, indent + 4).rstrip().split("\n")
                            first = rendered[0].lstrip()
                            lines.append(" " * (indent + 2) + "- " + first)
                            lines.extend(rendered[1:])
                        else:
                            rendered_scalar = _scalar(item)
                            if rendered_scalar.startswith(">\n") and isinstance(item, str):
                                lines.append(" " * (indent + 2) + "- >")
                                body = "\n".join(" " * (indent + 4) + line.strip() for line in item.rstrip().splitlines())
                                lines.append(body)
                            else:
                                lines.append(" " * (indent + 2) + "- " + rendered_scalar)
            else:
                rendered_scalar = _scalar(value)
                if rendered_scalar.startswith(">\n"):
                    lines.append(prefix + " >")
                    body = "\n".join(" " * (indent + 2) + line.strip() for line in value.rstrip().splitlines())
                    lines.append(body)
                else:
                    lines.append(prefix + " " + rendered_scalar)
        return "\n".join(lines) + "\n"
    if isinstance(data, list):
        return "\n".join(("- " + _scalar(item)) for item in data) + "\n"
    return _scalar(data) + "\n"
```

- [ ] **Step 2: Smoke-test the renderer**

```bash
python3 -c "from gaps_v1_migrator.render import render; print(render({'gapsVersion': '1.0.0', 'process': {'id': 'demo', 'scope': {'includes': ['a', 'b'], 'excludes': []}}}))"
```

Expected output:

```
gapsVersion: 1.0.0
process:
  id: demo
  scope:
    includes:
      - a
      - b
    excludes: []
```

Note: paths under `sys.path` need to include `scripts/`. If the smoke test fails with ImportError, run with `PYTHONPATH=scripts python3 -c ...`.

- [ ] **Step 3: Commit Task 2**

```bash
git add scripts/gaps_v1_migrator/render.py
git commit -m "Add GAPS v1 migrator renderer"
```

---

### Task 3: v0.1 → v1 translator

**Files:**
- Create: `scripts/gaps_v1_migrator/translate.py`

- [ ] **Step 1: Write the translator**

Create `scripts/gaps_v1_migrator/translate.py`:

```python
"""Translate a v0.1 ga-process YAML dict into a v1 dict shape."""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

from .match import fuzzy_action_match


_TERMINAL_HINTS = {"closed", "done", "archived", "approved", "completed", "rejected", "abandoned", "out_of_scope", "not_gadd_work", "duplicate"}


def _slug(text: str) -> str:
    out = []
    for ch in text.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")


def _underscore_slug(text: str) -> str:
    return _slug(text).replace("-", "_")


def _skill_slug(text: str) -> str:
    return _slug(text)


def _resolve_actions(prose_list: list[str], catalog: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    matched: list[str] = []
    unmatched: list[dict[str, Any]] = []
    seen: set[str] = set()
    for prose in prose_list:
        action_id, _score = fuzzy_action_match(prose, catalog)
        if action_id and action_id not in seen:
            matched.append(action_id)
            seen.add(action_id)
            continue
        if action_id:
            continue
        slug = _slug(prose)
        if not slug or slug in seen:
            continue
        unmatched.append({
            "id": slug,
            "label": prose,
            "category": "data-plane-persist",
            "defaultAutonomyTier": "execute_with_approval",
            "defaultRiskTier": "medium",
            "definition": f"TODO: migrated from v0.1 free-text action {prose!r}; review and normalize against the action catalog.",
            "justification": "Auto-generated by migrate-gaps-v0-to-v1; human review required before promoting beyond descriptive conformance.",
        })
        seen.add(slug)
    return matched, unmatched


def _translate_lane(lane_id: str, lane_data: dict[str, Any], catalog: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    authority = lane_data.get("authority", {}) or {}
    allowed, unmatched_allowed = _resolve_actions(authority.get("allowed", []) or [], catalog)
    prohibited, unmatched_prohibited = _resolve_actions(authority.get("prohibited", []) or [], catalog)

    state_model_states = []
    for index, state_name in enumerate(lane_data.get("states", []) or []):
        sid = _underscore_slug(state_name) or f"state_{index}"
        entry = {"id": sid, "label": state_name}
        if index == 0:
            entry["isInitial"] = True
        if index == len(lane_data.get("states", []) or []) - 1:
            entry["isTerminal"] = True
        state_model_states.append(entry)
    state_model = None
    if state_model_states:
        transitions = []
        for index, state in enumerate(state_model_states[:-1]):
            next_state = state_model_states[index + 1]
            transitions.append({
                "id": f"t-{state['id'].replace('_', '-')}-to-{next_state['id'].replace('_', '-')}",
                "from": state["id"],
                "to": next_state["id"],
            })
        state_model = {"states": state_model_states, "transitions": transitions}

    prohibited_set = set(prohibited)
    allowed = [action_id for action_id in allowed if action_id not in prohibited_set]

    lane_v1: dict[str, Any] = {
        "id": lane_id,
        "label": lane_id.replace("_", " ").title(),
        "purpose": lane_data.get("purpose", ""),
        "authority": {
            "plane": authority.get("plane", "data_plane"),
            "autonomyTier": authority.get("autonomyTier", "draft"),
            "riskTier": authority.get("riskTier", "medium"),
            "allowedActions": allowed,
            "prohibitedActions": prohibited,
        },
        "skills": [_skill_slug(skill) for skill in (lane_data.get("skills", []) or []) if _skill_slug(skill)],
    }
    if state_model is not None:
        lane_v1["stateModel"] = state_model
    if lane_data.get("autonomousResponsibilities"):
        resps, _ = _resolve_actions(lane_data["autonomousResponsibilities"], catalog)
        lane_v1["autonomousResponsibilities"] = resps
    return lane_v1, unmatched_allowed + unmatched_prohibited


def _translate_gates(lanes_v0: dict[str, Any]) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []
    for lane_data in lanes_v0.values():
        for gate in lane_data.get("gates", []) or []:
            gid = gate.get("id", _slug(gate.get("approvalCondition", "gate")))
            gates.append({
                "id": gid,
                "label": gate.get("id", gid).replace("_", " ").title(),
                "gateType": gate.get("gateType", "validating"),
                "approvalRole": gate.get("approvalRole", "approver"),
                "approvalCondition": gate.get("approvalCondition", ""),
                "escalationCondition": gate.get("escalationCondition", ""),
            })
    return gates


def _translate_control_mappings(v0: dict[str, Any]) -> dict[str, Any]:
    catalog_refs = [
        "gaps/catalogs/v1/controls/nist-ai-rmf.json",
        "gaps/catalogs/v1/controls/iso-42001-annex-a.json",
        "gaps/catalogs/v1/controls/eu-ai-act-articles.json",
    ]
    implementations: list[dict[str, Any]] = []
    for mapping in v0.get("controlMappings", []) or []:
        status_v0 = mapping.get("implementationStatus", "unreviewed")
        status_v1 = {
            "implemented": "implemented",
            "partial": "partial",
            "planned": "planned",
            "unreviewed": "planned",
            "not_applicable": "not-applicable",
        }.get(status_v0, "planned")
        control_id = str(mapping.get("controlId", "")) or "UNKNOWN"
        source = str(mapping.get("source", ""))
        if control_id == "GOVERN" and "NIST" in source:
            control_id = "GOVERN-1.4"
        elif control_id == "Annex A" and "42001" in source:
            control_id = "A.5.4"
        elif control_id == "Article 26" and "AI Act" in source:
            control_id = "Art.26"
        implementations.append({
            "controlId": control_id,
            "mappingStatus": status_v1,
            "statement": "Migrated from v0.1. Review and refine before declaring machine-validatable conformance.",
        })
    return {
        "catalogRefs": catalog_refs,
        "controlImplementations": implementations,
    }


def _translate_risk_patterns(v0: dict[str, Any]) -> list[dict[str, Any]]:
    patterns_v0 = v0.get("governedAutonomyRiskPatterns", {}) or {}
    rename = {
        "chat_as_control_plane": "chat-as-control-plane",
        "unbounded_delegation": "unbounded-delegation",
        "role_collapse": "role-collapse",
        "evidence_drift": "evidence-drift",
        "approval_theater": "approval-theater",
        "tool_sprawl": "tool-sprawl",
        "accountability_gaps": "accountability-gaps",
        "scope_creep_at_machine_speed": "scope-creep-at-machine-speed",
        "post_hoc_governance": "post-hoc-governance",
    }
    out: list[dict[str, Any]] = []
    for key, body in patterns_v0.items():
        ref = rename.get(key, key.replace("_", "-"))
        mitigation = body.get("mitigation") if isinstance(body, dict) else None
        out.append({
            "patternRef": ref,
            "mitigations": [mitigation] if mitigation else ["Migrated from v0.1; refine before promoting beyond descriptive."],
        })
    return out


def translate(v0: dict[str, Any], action_catalog: list[dict[str, Any]], source_path: Path) -> dict[str, Any]:
    process_v0 = v0.get("process", {}) or {}
    lanes_v0 = v0.get("lanes", {}) or {}

    lanes_v1: list[dict[str, Any]] = []
    extra_local_actions: list[dict[str, Any]] = []
    for lane_id, lane_data in lanes_v0.items():
        lane_v1, unmatched = _translate_lane(lane_id, lane_data, action_catalog)
        lanes_v1.append(lane_v1)
        extra_local_actions.extend(unmatched)

    seen_local: set[str] = set()
    deduped_local: list[dict[str, Any]] = []
    for entry in extra_local_actions:
        if entry["id"] in seen_local:
            continue
        seen_local.add(entry["id"])
        deduped_local.append(entry)

    roles_v1: list[dict[str, Any]] = []
    for role_id, role_data in (v0.get("roles", {}) or {}).items():
        roles_v1.append({
            "id": role_id,
            "label": role_data.get("label", role_id.replace("_", " ").title()),
            "accountabilityScope": f"TODO: migrate accountability scope for {role_id} from v0.1.",
            "decisionRights": [],
        })

    today = _dt.date.today().isoformat()

    v1: dict[str, Any] = {
        "gapsVersion": "1.0.0",
        "specStatus": "draft",
        "conformanceLevel": "descriptive",
        "process": {
            "id": process_v0.get("id", source_path.parent.name),
            "name": process_v0.get("name", source_path.parent.name),
            "purpose": process_v0.get("purpose", ""),
            "scope": {
                "includes": list((process_v0.get("scope", {}) or {}).get("includes", []) or []),
                "excludes": list((process_v0.get("scope", {}) or {}).get("excludes", []) or []),
            },
        },
        "substrate": {
            "oscalControlCatalogs": [
                "gaps/catalogs/v1/controls/nist-ai-rmf.json",
                "gaps/catalogs/v1/controls/iso-42001-annex-a.json",
                "gaps/catalogs/v1/controls/eu-ai-act-articles.json",
            ],
            "actionCatalog": "gaps/catalogs/v1/actions.yml",
            "evidenceCatalog": "gaps/catalogs/v1/evidence-kinds.yml",
            "riskPatternCatalog": "gaps/catalogs/v1/risk-patterns.yml",
        },
        "roles": roles_v1,
        "evidenceModel": {
            "caseFileItems": [
                {
                    "id": "migrated-process-state",
                    "kind": "state-transition-event",
                    "label": "Migrated v0.1 process state placeholder",
                    "producer": "lane:" + (lanes_v1[0]["id"] if lanes_v1 else "unknown"),
                    "consumer": ["role:" + roles_v1[0]["id"]] if roles_v1 else [],
                }
            ],
        },
        "lanes": lanes_v1,
        "gates": _translate_gates(lanes_v0),
        "projectionPolicy": {
            "canonicalStateSource": "repo-local-ledger",
            "pathPattern": (v0.get("canonicalState", {}) or {}).get("pathPattern", "state/**"),
        },
        "riskPatterns": _translate_risk_patterns(v0),
        "controlAssessment": _translate_control_mappings(v0),
        "freshness": {
            "reviewedAt": today,
            "driftPolicy": "Migrated from v0.1. Review and uplift to machine-validatable conformance before relying on this spec.",
        },
        "knownGaps": [
            {
                "id": "migrated-from-v0-1",
                "summary": "Spec was migrated mechanically from v0.1. Many fields are placeholders; uplift before declaring machine-validatable.",
                "severity": "important",
                "plannedResolution": "manual-port-review",
            }
        ],
    }
    if deduped_local:
        v1["process"]["localActions"] = deduped_local
    return v1
```

- [ ] **Step 2: Commit Task 3**

```bash
git add scripts/gaps_v1_migrator/translate.py
git commit -m "Add GAPS v0.1 to v1 translator"
```

---

### Task 4: Migrator CLI

**Files:**
- Create: `scripts/migrate-gaps-v0-to-v1.py`

- [ ] **Step 1: Write the CLI**

Create `scripts/migrate-gaps-v0-to-v1.py`:

```python
#!/usr/bin/env python3
"""Migrate a GAPS v0.1 ga-process YAML to a v1 ga-process YAML."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.dont_write_bytecode = True

from gaps_v1_migrator.render import render  # noqa: E402
from gaps_v1_migrator.translate import translate  # noqa: E402
from gaps_v1_validator.loader import load_yaml  # noqa: E402

ACTION_CATALOG_PATH = REPO_ROOT / "gaps" / "catalogs" / "v1" / "actions.yml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to a v0.1 ga-process.yml file.")
    parser.add_argument("--out", type=Path, default=None, help="Destination path; default writes next to source as ga-process.v1.yml.")
    parser.add_argument("--stdout", action="store_true", help="Write to stdout instead of a file.")
    args = parser.parse_args()

    v0 = load_yaml(args.source)
    catalog = load_yaml(ACTION_CATALOG_PATH).get("actions", [])
    v1 = translate(v0, catalog, args.source.resolve())
    rendered = render(v1)

    if args.stdout:
        sys.stdout.write(rendered)
        return 0
    destination = args.out or (args.source.parent / "ga-process.v1.yml")
    destination.write_text(rendered, encoding="utf-8")
    print(f"wrote {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Extend migrator tests**

Append to `tests/gaps/v1/test_migrate.py`:

```python
class MigratorEndToEndTests(unittest.TestCase):
    def test_migrate_gadd_v0_to_v1_validates_descriptive(self) -> None:
        import subprocess
        import tempfile
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "migrate-gaps-v0-to-v1.py"), str(ROOT / "gaps" / "examples" / "gadd" / "ga-process.yml"), "--stdout"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".v1.yml", dir=ROOT, delete=False) as handle:
            handle.write(result.stdout)
            migrated = Path(handle.name)
        try:
            validate = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate-gaps-v1.py"), str(migrated)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr + validate.stdout)
        finally:
            migrated.unlink(missing_ok=True)

    def test_migrate_deterministic(self) -> None:
        import subprocess
        first = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "migrate-gaps-v0-to-v1.py"), str(ROOT / "gaps" / "examples" / "gadd" / "ga-process.yml"), "--stdout"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        second = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "migrate-gaps-v0-to-v1.py"), str(ROOT / "gaps" / "examples" / "gadd" / "ga-process.yml"), "--stdout"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        # Strip the freshness.reviewedAt date which is today's date — known nondeterminism.
        def normalize(text: str) -> str:
            return "\n".join(line for line in text.splitlines() if "reviewedAt" not in line)
        self.assertEqual(normalize(first.stdout), normalize(second.stdout))
```

- [ ] **Step 3: Run tests**

```bash
chmod +x scripts/migrate-gaps-v0-to-v1.py
python3 -m unittest tests.gaps.v1.test_migrate -v
```

Expected: all tests PASS. If end-to-end validation fails, the translator needs a fix — diagnose by running the migrator with `--stdout` and the validator with the resulting file to see specific issues.

- [ ] **Step 4: Commit Task 4**

```bash
git add scripts/migrate-gaps-v0-to-v1.py tests/gaps/v1/test_migrate.py
git commit -m "Add GAPS v0.1 to v1 migrator CLI"
```

---

### Task 5: Port the four v0.1 reference specs

**Files:**
- Create: `gaps/examples/v1/gadd/ga-process.v1.yml`
- Create: `gaps/examples/v1/compliance-review/ga-process.v1.yml`
- Create: `gaps/examples/v1/incident-response/ga-process.v1.yml`
- Create: `gaps/examples/v1/procurement-approval/ga-process.v1.yml`

- [ ] **Step 1: Create the directories**

```bash
mkdir -p gaps/examples/v1/gadd gaps/examples/v1/compliance-review gaps/examples/v1/incident-response gaps/examples/v1/procurement-approval
```

- [ ] **Step 2: Migrate each spec**

```bash
python3 scripts/migrate-gaps-v0-to-v1.py gaps/examples/gadd/ga-process.yml --out gaps/examples/v1/gadd/ga-process.v1.yml
python3 scripts/migrate-gaps-v0-to-v1.py gaps/examples/compliance-review/ga-process.yml --out gaps/examples/v1/compliance-review/ga-process.v1.yml
python3 scripts/migrate-gaps-v0-to-v1.py gaps/examples/incident-response/ga-process.yml --out gaps/examples/v1/incident-response/ga-process.v1.yml
python3 scripts/migrate-gaps-v0-to-v1.py gaps/examples/procurement-approval/ga-process.yml --out gaps/examples/v1/procurement-approval/ga-process.v1.yml
```

Expected: four `wrote ...` confirmations.

- [ ] **Step 3: Validate each ported spec**

```bash
for spec in gaps/examples/v1/{gadd,compliance-review,incident-response,procurement-approval}/ga-process.v1.yml; do
  python3 scripts/validate-gaps-v1.py "$spec"
done
```

Expected: four `GAPS v1 spec validated: ...` lines. If any fails, the migrator output exposed a translator bug; fix the translator (Task 3) and rerun.

- [ ] **Step 4: Quick manual review of each output**

For each ported file, open and confirm:

- `process.id`, `process.name`, `process.purpose` look correct.
- `roles[].accountabilityScope` contains the placeholder string and is flagged in `knownGaps`.
- `lanes[].authority.allowedActions` and `prohibitedActions` reference catalog ids (kebab-case, lowercase).
- `process.localActions[]` exists where the v0.1 spec used vocabulary not in the universal catalog.
- `riskPatterns[].patternRef` uses kebab-case ids (`chat-as-control-plane`, not `chat_as_control_plane`).
- `controlAssessment.controlImplementations[].mappingStatus` is one of the v1 enum values.

No fix needed in this step — just confirm the structure looks correct.

- [ ] **Step 5: Commit Task 5**

```bash
git add gaps/examples/v1/gadd gaps/examples/v1/compliance-review gaps/examples/v1/incident-response gaps/examples/v1/procurement-approval
git commit -m "Port v0.1 reference specs to v1 at descriptive conformance"
```

---

### Task 6: New `benefits-eligibility-review` reference spec (machine-validatable)

This is the only freshly authored spec in Phase 3. It stresses CMMN-conceptual state modeling more than any existing reference spec: adaptive states, time-limit milestones, multi-authority escalation, and a clear separation between operator and reviewer.

**Files:**
- Create: `gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml`

- [ ] **Step 1: Write the spec**

```yaml
gapsVersion: "1.0.0"
specStatus: draft
conformanceLevel: machine-validatable

process:
  id: benefits-eligibility-review
  name: Benefits eligibility review
  purpose: >
    Governed review of an applicant's eligibility for a publicly funded
    benefit, applied as a generic casework reference spec. The process
    illustrates how GAPS handles adaptive state, time-limit milestones,
    and multi-authority escalation outside of software delivery.
  scope:
    includes:
      - intake of an eligibility request
      - evidence gathering within a defined time limit
      - assessment against published eligibility rules
      - human approval of the eligibility decision
      - communication of outcome to the applicant
    excludes:
      - benefit issuance, payment, or operations
      - appeals after the initial decision
      - policy rule authoring

substrate:
  oscalControlCatalogs:
    - gaps/catalogs/v1/controls/nist-ai-rmf.json
    - gaps/catalogs/v1/controls/iso-42001-annex-a.json
    - gaps/catalogs/v1/controls/eu-ai-act-articles.json
  actionCatalog: gaps/catalogs/v1/actions.yml
  evidenceCatalog: gaps/catalogs/v1/evidence-kinds.yml
  riskPatternCatalog: gaps/catalogs/v1/risk-patterns.yml

roles:
  - id: caseworker
    label: Caseworker
    accountabilityScope: Gathering evidence and drafting the assessment within service standards.
    decisionRights:
      - draft-artifact
      - record-evidence
      - request-clarification
      - request-evidence
      - escalate-to-human
    canApprove: []
  - id: senior_reviewer
    label: Senior reviewer
    accountabilityScope: Quality assurance of caseworker assessment and approval of the eligibility decision.
    decisionRights:
      - approve-gate
      - revoke-approval
    canApprove:
      - assessment_decision_gate
  - id: appeals_authority
    label: Appeals authority
    accountabilityScope: Escalated decisions and policy interpretations that the senior reviewer cannot resolve.
    decisionRights:
      - approve-gate
      - revoke-approval
    canApprove:
      - escalated_review_gate

evidenceModel:
  caseFileItems:
    - id: eligibility-request
      kind: triage-observation
      label: Initial eligibility request
      shape:
        required: [applicantRef, requestedBenefit, receivedAt]
        optional: [submittedThrough, languagePreference]
      producer: external
      consumer:
        - lane:intake_lane
      retentionPolicy: regulatory
    - id: identity-attestation
      kind: external-reference
      label: Verified identity record
      shape:
        required: [system, recordId, verifiedAt]
      producer: external
      consumer:
        - lane:evidence_gathering_lane
      retentionPolicy: regulatory
    - id: supporting-evidence
      kind: artifact-reference
      label: Supporting evidence supplied by applicant
      shape:
        required: [evidenceType, sourcePath, receivedAt]
        optional: [originSystem]
      producer: external
      consumer:
        - lane:evidence_gathering_lane
        - lane:assessment_lane
      retentionPolicy: regulatory
    - id: assessment-draft
      kind: artifact-reference
      label: Caseworker assessment draft
      shape:
        required: [path, contentHash, draftedAt]
      producer: role:caseworker
      consumer:
        - role:senior_reviewer
      retentionPolicy: regulatory
    - id: assessment-approval
      kind: approval-attestation
      label: Senior reviewer approval
      shape:
        required: [role, actorId, gateId, decision, attestedAt]
      producer: role:senior_reviewer
      consumer:
        - lane:decision_communication_lane
      retentionPolicy: regulatory
    - id: escalation-decision
      kind: approval-attestation
      label: Appeals authority decision on escalation
      shape:
        required: [role, actorId, gateId, decision, attestedAt]
      producer: role:appeals_authority
      consumer:
        - lane:decision_communication_lane
      retentionPolicy: regulatory
    - id: time-limit-event
      kind: audit-event
      label: Service standard time-limit breach event
      shape:
        required: [milestoneId, dueAt, observedAt]
      producer: lane:evidence_gathering_lane
      consumer:
        - role:senior_reviewer
      retentionPolicy: regulatory

lanes:
  - id: intake_lane
    label: Intake lane
    purpose: Receive and normalize an eligibility request, confirming identity.
    authority:
      plane: data_plane
      autonomyTier: draft
      riskTier: low
      allowedActions:
        - draft-artifact
        - record-evidence
        - read-external-system-state
        - request-clarification
      prohibitedActions:
        - approve-own-work
        - approve-gate
        - make-binding-policy-interpretation
    stateModel:
      states:
        - id: intake_open
          label: Open
          isInitial: true
        - id: intake_identity_pending
          label: Awaiting identity verification
        - id: intake_ready
          label: Ready for evidence gathering
        - id: intake_rejected
          label: Rejected at intake
          isTerminal: true
      transitions:
        - id: t-open-to-identity-pending
          from: intake_open
          to: intake_identity_pending
          guard:
            inputs: [eligibility-request]
            rules:
              - when: defined(eligibility-request)
                then: allow
            else: block
        - id: t-identity-pending-to-ready
          from: intake_identity_pending
          to: intake_ready
          guard:
            inputs: [identity-attestation]
            rules:
              - when: defined(identity-attestation)
                then: allow
            else: block
        - id: t-identity-pending-to-rejected
          from: intake_identity_pending
          to: intake_rejected
          guard:
            inputs: [identity-attestation]
            rules:
              - when: undefined(identity-attestation)
                then: allow
            else: block
    evidenceInputs:
      - eligibility-request
      - identity-attestation
    evidenceOutputs:
      - eligibility-request
    autonomousResponsibilities:
      - record-evidence
      - read-external-system-state
    skills:
      - benefits-eligibility-intake

  - id: evidence_gathering_lane
    label: Evidence gathering lane
    purpose: Request and collect supporting evidence within the service-standard time limit.
    authority:
      plane: data_plane
      autonomyTier: execute_with_approval
      riskTier: medium
      allowedActions:
        - request-evidence
        - request-clarification
        - record-evidence
        - escalate-to-human
      prohibitedActions:
        - approve-own-work
        - approve-gate
        - declare-final-classification
        - infer-from-missing-evidence
    stateModel:
      states:
        - id: gathering_open
          label: Gathering open
          isInitial: true
        - id: gathering_in_progress
          label: In progress
        - id: gathering_breached
          label: Time-limit breached
        - id: gathering_complete
          label: Complete
          isTerminal: true
        - id: gathering_abandoned
          label: Abandoned
          isTerminal: true
      transitions:
        - id: t-open-to-in-progress
          from: gathering_open
          to: gathering_in_progress
          guard:
            inputs: [supporting-evidence]
            rules:
              - when: defined(supporting-evidence)
                then: allow
            else: block
        - id: t-in-progress-to-breached
          from: gathering_in_progress
          to: gathering_breached
          guard:
            inputs: [time-limit-event]
            rules:
              - when: defined(time-limit-event)
                then: allow
            else: block
        - id: t-in-progress-to-complete
          from: gathering_in_progress
          to: gathering_complete
        - id: t-breached-to-abandoned
          from: gathering_breached
          to: gathering_abandoned
          guard:
            inputs: [escalation-decision]
            rules:
              - when: defined(escalation-decision)
                then: allow
            else: block
    evidenceInputs:
      - supporting-evidence
      - time-limit-event
    evidenceOutputs:
      - supporting-evidence
    autonomousResponsibilities:
      - request-evidence
      - record-evidence
    skills:
      - benefits-eligibility-evidence

  - id: assessment_lane
    label: Assessment lane
    purpose: Draft the eligibility assessment using the gathered evidence.
    authority:
      plane: data_plane
      autonomyTier: draft
      riskTier: medium
      allowedActions:
        - draft-artifact
        - record-evidence
        - escalate-to-human
      prohibitedActions:
        - approve-own-work
        - approve-gate
        - make-binding-policy-interpretation
        - declare-final-classification
    stateModel:
      states:
        - id: assessment_drafting
          label: Drafting
          isInitial: true
        - id: assessment_awaiting_review
          label: Awaiting reviewer
        - id: assessment_complete
          label: Complete
          isTerminal: true
      transitions:
        - id: t-drafting-to-awaiting
          from: assessment_drafting
          to: assessment_awaiting_review
          guard:
            inputs: [assessment-draft]
            rules:
              - when: defined(assessment-draft)
                then: allow
            else: block
        - id: t-awaiting-to-complete
          from: assessment_awaiting_review
          to: assessment_complete
          gate: assessment_decision_gate
          guard:
            inputs: [assessment-approval]
            rules:
              - when: defined(assessment-approval)
                then: allow
            else: block
    evidenceInputs:
      - supporting-evidence
    evidenceOutputs:
      - assessment-draft
    autonomousResponsibilities:
      - draft-artifact
      - record-evidence
    skills:
      - benefits-eligibility-assessment

  - id: decision_communication_lane
    label: Decision communication lane
    purpose: Communicate the approved decision to the applicant.
    authority:
      plane: data_plane
      autonomyTier: execute_with_approval
      riskTier: medium
      allowedActions:
        - dispatch-notification
        - record-evidence
      prohibitedActions:
        - approve-own-work
        - declare-final-classification
        - alter-recorded-evidence
    stateModel:
      states:
        - id: communication_pending
          label: Pending
          isInitial: true
        - id: communication_sent
          label: Sent
          isTerminal: true
      transitions:
        - id: t-pending-to-sent
          from: communication_pending
          to: communication_sent
          guard:
            inputs: [assessment-approval]
            rules:
              - when: defined(assessment-approval)
                then: allow
            else: block
    evidenceInputs:
      - assessment-approval
    evidenceOutputs: []
    autonomousResponsibilities:
      - dispatch-notification
      - record-evidence
    skills:
      - benefits-eligibility-communicate

gates:
  - id: assessment_decision_gate
    label: Senior reviewer decision gate
    gateType: blocking
    approvalRole: senior_reviewer
    approvalCondition: Reviewer confirms the assessment-draft is consistent with the recorded evidence and the published eligibility rules.
    escalationCondition: Reviewer cannot confirm without a policy interpretation that the senior reviewer is not authorized to make.
    decision:
      inputs:
        - assessment-draft
        - supporting-evidence
      rules:
        - when: defined(assessment-draft) and defined(supporting-evidence)
          then: approve
          effect:
            transitionTo: assessment_complete
            recordEvidence:
              - assessment-approval
        - when: undefined(assessment-draft)
          then: escalate
        - when: undefined(supporting-evidence)
          then: escalate
      else: escalate

  - id: escalated_review_gate
    label: Escalated appeals authority gate
    gateType: escalating
    approvalRole: appeals_authority
    approvalCondition: Appeals authority confirms or overrides the senior reviewer's recommendation on a policy-interpretation question.
    escalationCondition: Question requires legal or policy authority beyond the appeals authority's scope.
    decision:
      inputs:
        - assessment-draft
        - supporting-evidence
        - time-limit-event
      rules:
        - when: defined(assessment-draft) and defined(supporting-evidence)
          then: approve
          effect:
            recordEvidence:
              - escalation-decision
        - when: defined(time-limit-event)
          then: reject
          effect:
            transitionTo: gathering_abandoned
            recordEvidence:
              - escalation-decision
      else: escalate

controlPlaneActions:
  - skill: benefits-eligibility-approve
    plane: control_plane
    autonomyTier: human_only
    riskTier: high
    actions:
      - approve-gate
      - revoke-approval

projectionPolicy:
  canonicalStateSource: repo-local-ledger
  pathPattern: "gaps/examples/v1/benefits-eligibility-review/state/**"
  externalSystems:
    - kind: case-management-system
      role: collaboration-surface
      mutationRequiresApproval: true
    - kind: identity-directory
      role: projection-target
      mutationRequiresApproval: true

riskPatterns:
  - patternRef: chat-as-control-plane
    mitigations:
      - Approvals are recorded as approval-attestation evidence on the repo-local ledger.
    evidenceRefs:
      - assessment-approval
      - escalation-decision
  - patternRef: role-collapse
    mitigations:
      - Caseworker, senior reviewer, and appeals authority roles are explicitly separated.
      - approve-own-work appears in prohibitedActions on every lane.
  - patternRef: evidence-drift
    mitigations:
      - Every transition has a guard tied to a typed case file item.
      - All approval-attestation and audit-event evidence kinds use regulatory retention.
    evidenceRefs:
      - time-limit-event
      - assessment-approval
  - patternRef: accountability-gaps
    mitigations:
      - Every gate names an explicit approvalRole resolvable in the roles block.
  - patternRef: scope-creep-at-machine-speed
    mitigations:
      - Caseworker prohibitedActions explicitly include make-binding-policy-interpretation and infer-from-missing-evidence.
  - patternRef: post-hoc-governance
    mitigations:
      - Spec authored before skills exist; skills are bound to lanes only via implementation maps generated from this spec.

controlAssessment:
  catalogRefs:
    - gaps/catalogs/v1/controls/nist-ai-rmf.json
    - gaps/catalogs/v1/controls/iso-42001-annex-a.json
  controlImplementations:
    - controlId: GOVERN-1.4
      mappingStatus: partial
      implementedBy:
        skills:
          - benefits-eligibility-intake
          - benefits-eligibility-evidence
          - benefits-eligibility-assessment
          - benefits-eligibility-communicate
        evidence:
          - assessment-approval
          - escalation-decision
      statement: >
        Reviewer and appeals decisions are recorded as evidence on the
        repo-local ledger, providing transparent traceability of the
        decision pathway.
    - controlId: GOVERN-3.2
      mappingStatus: implemented
      implementedBy:
        skills:
          - benefits-eligibility-intake
          - benefits-eligibility-evidence
          - benefits-eligibility-assessment
      statement: >
        Roles and decision rights for caseworker, senior reviewer, and
        appeals authority are explicit, with prohibitedActions enforcing
        separation of duties.
    - controlId: A.5.4
      mappingStatus: partial
      implementedBy:
        skills:
          - benefits-eligibility-assessment
        evidence:
          - assessment-draft
      statement: >
        Each assessment captures evidence and rationale used to determine
        the impact on the individual applicant.

freshness:
  reviewedAt: "2026-05-18"
  driftPolicy: >
    This reference spec is authored deliberately at machine-validatable
    conformance to stress-test GAPS v1 on a non-software process.
    Promote to generative only when paired with a generated skill package
    and round-trip verification.

knownGaps:
  - id: machine-validatable-not-generative
    summary: This spec is machine-validatable; the state model and gate decisions are not yet exercised against a generated skill package.
    severity: minor
    plannedResolution: phase-4-generator
  - id: no-localActions
    summary: Spec deliberately avoids process.localActions to validate that the universal catalog is sufficient for a casework process.
    severity: minor
    plannedResolution: null
```

- [ ] **Step 2: Validate the spec**

```bash
python3 scripts/validate-gaps-v1.py gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml
```

Expected: success at the spec's declared `machine-validatable` level.

- [ ] **Step 3: Confirm generative-level override fails**

```bash
python3 scripts/validate-gaps-v1.py gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml --level generative
```

Expected: failure with at least one `generative requires ...` issue (since no implementation fingerprint is set; this is intentional for Phase 3).

- [ ] **Step 4: Commit Task 6**

```bash
git add gaps/examples/v1/benefits-eligibility-review
git commit -m "Add benefits-eligibility-review GAPS v1 reference spec"
```

---

### Task 7: Integration and documentation

**Files:**
- Modify: `scripts/validate-governed-autonomy.sh`
- Modify: `gaps/README.md`

- [ ] **Step 1: Update the validation script**

Phase 1 already loops over `gaps/examples/v1/*/ga-process.v1.yml`. Confirm the loop still works with the new ports:

```bash
./scripts/validate-governed-autonomy.sh
```

Expected: every v1 spec validates. If any v1 spec fails at its declared level, fix it before continuing.

Add a migrator smoke test to the script. Edit `scripts/validate-governed-autonomy.sh` and append before the test discovery line:

```bash
echo "==> Smoke-testing v0.1 to v1 migrator"
python3 scripts/migrate-gaps-v0-to-v1.py gaps/examples/gadd/ga-process.yml --stdout > /tmp/gaps-migrate-smoke.yml
python3 scripts/validate-gaps-v1.py /tmp/gaps-migrate-smoke.yml
rm -f /tmp/gaps-migrate-smoke.yml
```

- [ ] **Step 2: Update `gaps/README.md`**

Add to the v1 incubation section (created in Phase 1):

```markdown
### v1 reference specs

The v1 reference set lives under `gaps/examples/v1/`:

- `gadd/` — software-delivery case study, migrated from v0.1 at descriptive conformance.
- `compliance-review/` — adaptive compliance review, migrated from v0.1 at descriptive conformance.
- `incident-response/` — incident handling, migrated from v0.1 at descriptive conformance.
- `procurement-approval/` — procurement approvals, migrated from v0.1 at descriptive conformance.
- `benefits-eligibility-review/` — public-sector casework reference, authored fresh at machine-validatable conformance.
- `minimal/` — schema smoke-test fixture at descriptive conformance.
- `comprehensive/` — validator coverage fixture at machine-validatable conformance.

Migrate a v0.1 spec to v1:

\`\`\`bash
python3 scripts/migrate-gaps-v0-to-v1.py gaps/examples/<process-id>/ga-process.yml
\`\`\`

The migrator always emits `conformanceLevel: descriptive`. Uplift to
`machine-validatable` and `generative` deliberately, recording the
review in `freshness.driftPolicy`.
```

- [ ] **Step 3: Run the full validation suite**

```bash
./scripts/validate-governed-autonomy.sh
```

Expected: green; `All Governed Autonomy validation checks passed.`

- [ ] **Step 4: Commit Task 7**

```bash
git add scripts/validate-governed-autonomy.sh gaps/README.md
git commit -m "Wire v1 migrator into repo validation suite"
```

---

## Self-Review Checklist

- Migrator is deterministic (modulo `reviewedAt` date) — same input always produces same output.
- All four migrated reference specs validate at descriptive conformance.
- `benefits-eligibility-review` validates at machine-validatable conformance with no local actions, exercising the universal action catalog on a casework process.
- v0.1 tooling and v0.1 specs continue to validate unchanged.
- Every migrated spec includes a `knownGaps` entry flagging it as machine-migrated.
- Migrator output prefers safe defaults: placeholder accountability scopes, TODO definitions on local actions, planned mapping status for uncertain control mappings.

## What Phase 3 does NOT do

- Does not generate skill packages from any v1 spec (Phase 4).
- Does not promote any migrated spec beyond `descriptive` (intentional — promotion is a deliberate human review).
- Does not delete v0.1 specs or v0.1 validator (deprecation window continues).
- Does not implement round-trip diff between spec and generated skills (Phase 5).

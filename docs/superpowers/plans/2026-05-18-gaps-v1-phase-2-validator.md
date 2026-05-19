# GAPS v1.0.0 Phase 2: Validator v1

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote `scripts/validate-gaps-v1.py` from structural-schema-only (Phase 1) to a full semantic validator: catalog reference resolution, internal cross-reference integrity, state-machine soundness, gate decision completeness, authority/action consistency, projection policy consistency, OSCAL control reference resolution, and conformance-level gating.

**Architecture:** The validator is reorganized from a single function into a `Validator` class with discrete check methods. Each check is independently testable and produces error messages with a stable structure (`{rule, path, message}`). Catalogs are loaded once from `substrate.*Catalog` paths in the spec. A new `gaps/examples/v1/comprehensive/` fixture exercises every check; targeted invalid-fixtures live under `tests/gaps/v1/fixtures/invalid/`. Conformance level gating means `machine-validatable` and `generative` levels enforce additional requirements over `descriptive`. FEEL-expression subset support stays minimal — string equality, defined/undefined, boolean combinators — sufficient for the `when` expressions in transition guards and gate decisions.

**Tech Stack:** Python 3 stdlib only. Existing Ruby YAML→JSON bridge. JSON Schema 2020-12 subset evaluator from Phase 1 reused via import.

---

## File Structure

**Modified files:**
- `scripts/validate-gaps-v1.py` — major rewrite, now imports a new `gaps_v1_validator` module
- `gaps/examples/v1/minimal/ga-process.v1.yml` — already validates; remains at `descriptive`

**New files:**
- `scripts/gaps_v1_validator/__init__.py` — package marker
- `scripts/gaps_v1_validator/loader.py` — catalog and spec loaders
- `scripts/gaps_v1_validator/schema_check.py` — JSON Schema subset evaluator (lifted from Phase 1)
- `scripts/gaps_v1_validator/cross_refs.py` — internal cross-reference resolution
- `scripts/gaps_v1_validator/catalog_refs.py` — catalog reference resolution
- `scripts/gaps_v1_validator/state_machine.py` — per-lane state-machine soundness
- `scripts/gaps_v1_validator/gate_decisions.py` — gate decision completeness
- `scripts/gaps_v1_validator/feel_subset.py` — FEEL-subset expression parser and evaluator
- `scripts/gaps_v1_validator/authority.py` — authority/action consistency, projection-policy consistency
- `scripts/gaps_v1_validator/conformance.py` — conformance-level gating
- `scripts/gaps_v1_validator/oscal_refs.py` — OSCAL control reference resolution
- `scripts/gaps_v1_validator/errors.py` — error type and aggregation
- `gaps/examples/v1/comprehensive/ga-process.v1.yml` — fixture at `machine-validatable` covering every check positively
- `gaps/examples/v1/comprehensive/expected.txt` — placeholder for golden output (validator success)
- `tests/gaps/v1/fixtures/invalid/__init__.py`
- `tests/gaps/v1/fixtures/invalid/unresolved_action.yml`
- `tests/gaps/v1/fixtures/invalid/unresolved_role.yml`
- `tests/gaps/v1/fixtures/invalid/orphan_state.yml`
- `tests/gaps/v1/fixtures/invalid/duplicate_gate_id.yml`
- `tests/gaps/v1/fixtures/invalid/incomplete_decision.yml`
- `tests/gaps/v1/fixtures/invalid/contradictory_actions.yml`
- `tests/gaps/v1/fixtures/invalid/external_system_unmarked.yml`
- `tests/gaps/v1/fixtures/invalid/oscal_control_not_in_catalog.yml`
- `tests/gaps/v1/fixtures/invalid/generative_without_state_model.yml`
- `tests/gaps/v1/test_cross_refs.py`
- `tests/gaps/v1/test_catalog_refs.py`
- `tests/gaps/v1/test_state_machine.py`
- `tests/gaps/v1/test_gate_decisions.py`
- `tests/gaps/v1/test_feel_subset.py`
- `tests/gaps/v1/test_authority.py`
- `tests/gaps/v1/test_conformance.py`
- `tests/gaps/v1/test_oscal_refs.py`
- `tests/gaps/v1/test_end_to_end.py`

---

### Task 1: Reorganize the validator into a package

**Files:**
- Create: `scripts/gaps_v1_validator/__init__.py`
- Create: `scripts/gaps_v1_validator/errors.py`
- Create: `scripts/gaps_v1_validator/loader.py`
- Create: `scripts/gaps_v1_validator/schema_check.py`
- Modify: `scripts/validate-gaps-v1.py`

- [ ] **Step 1: Create the package skeleton**

```bash
mkdir -p scripts/gaps_v1_validator
touch scripts/gaps_v1_validator/__init__.py
```

- [ ] **Step 2: Write the errors module**

Create `scripts/gaps_v1_validator/errors.py`:

```python
"""Validator error types and aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class ValidationIssue:
    rule: str
    path: str
    message: str

    def format(self) -> str:
        return f"[{self.rule}] {self.path}: {self.message}"


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    def add(self, rule: str, path: str, message: str) -> None:
        self.issues.append(ValidationIssue(rule=rule, path=path, message=message))

    def extend(self, others: Iterable[ValidationIssue]) -> None:
        self.issues.extend(others)

    @property
    def ok(self) -> bool:
        return not self.issues

    def render(self) -> str:
        return "\n".join(issue.format() for issue in self.issues)
```

- [ ] **Step 3: Write the loader module**

Create `scripts/gaps_v1_validator/loader.py`:

```python
"""Load specs, catalogs, and OSCAL control catalogs through the Ruby YAML bridge."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def load_yaml(path: Path) -> Any:
    result = subprocess.run(
        [
            "ruby",
            "-ryaml",
            "-rjson",
            "-e",
            "print YAML.load_file(ARGV[0]).to_json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"failed to load {path}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_catalog_path(spec_path: Path, catalog_ref: str) -> Path:
    """Resolve a catalog path stored in spec.substrate.*. May be repo-relative or absolute."""
    candidate = Path(catalog_ref)
    if candidate.is_absolute():
        return candidate
    repo_root = spec_path
    while repo_root != repo_root.parent and not (repo_root / ".git").exists():
        repo_root = repo_root.parent
    return repo_root / candidate
```

- [ ] **Step 4: Write the schema-check module**

Create `scripts/gaps_v1_validator/schema_check.py`. This lifts the JSON Schema subset evaluator from Phase 1 into a reusable module:

```python
"""JSON Schema 2020-12 subset evaluator used by the v1 validator."""

from __future__ import annotations

import re
from typing import Any

from .errors import ValidationReport


def validate_schema(data: Any, schema: dict[str, Any], report: ValidationReport, root_path: str = "$", rule: str = "schema") -> None:
    def matches_type(value: Any, t: str) -> bool:
        if t == "null":
            return value is None
        if t == "string":
            return isinstance(value, str)
        if t == "boolean":
            return isinstance(value, bool)
        if t == "object":
            return isinstance(value, dict)
        if t == "array":
            return isinstance(value, list)
        if t == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if t == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        return False

    def check(node_data: Any, node_schema: dict[str, Any], path: str) -> None:
        if "const" in node_schema and node_data != node_schema["const"]:
            report.add(rule, path, f"expected const {node_schema['const']!r}, got {node_data!r}")
            return
        if "enum" in node_schema and node_data not in node_schema["enum"]:
            report.add(rule, path, f"value {node_data!r} not in enum")
            return
        node_type = node_schema.get("type")
        if isinstance(node_type, list):
            if not any(matches_type(node_data, t) for t in node_type):
                report.add(rule, path, f"type mismatch (expected one of {node_type})")
                return
            node_type = next((t for t in node_type if matches_type(node_data, t)), None)
        if node_type == "object":
            if not isinstance(node_data, dict):
                report.add(rule, path, "expected object")
                return
            for required_key in node_schema.get("required", []):
                if required_key not in node_data:
                    report.add(rule, path, f"missing required key {required_key!r}")
            properties = node_schema.get("properties", {})
            additional = node_schema.get("additionalProperties", True)
            for key, value in node_data.items():
                if key in properties:
                    check(value, properties[key], f"{path}.{key}")
                elif additional is False:
                    report.add(rule, path, f"unexpected key {key!r}")
                elif isinstance(additional, dict):
                    check(value, additional, f"{path}.{key}")
        elif node_type == "array":
            if not isinstance(node_data, list):
                report.add(rule, path, "expected array")
                return
            if "minItems" in node_schema and len(node_data) < node_schema["minItems"]:
                report.add(rule, path, f"minItems={node_schema['minItems']} but len={len(node_data)}")
            item_schema = node_schema.get("items")
            if isinstance(item_schema, dict):
                for index, item in enumerate(node_data):
                    check(item, item_schema, f"{path}[{index}]")
        elif node_type == "string":
            if not isinstance(node_data, str):
                report.add(rule, path, "expected string")
                return
            if "minLength" in node_schema and len(node_data) < node_schema["minLength"]:
                report.add(rule, path, f"minLength={node_schema['minLength']} but len={len(node_data)}")
            if "pattern" in node_schema and not re.search(node_schema["pattern"], node_data):
                report.add(rule, path, f"does not match pattern {node_schema['pattern']!r}")
        elif node_type == "boolean":
            if not isinstance(node_data, bool):
                report.add(rule, path, "expected boolean")

    check(data, schema, root_path)
```

- [ ] **Step 5: Rewrite the CLI entry point**

Replace `scripts/validate-gaps-v1.py` with this thin dispatcher. (Phase 2 keeps the same CLI shape; new checks come online incrementally as later tasks land.)

```python
#!/usr/bin/env python3
"""Validate a GAPS v1 ga-process YAML against schema and semantic rules."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.dont_write_bytecode = True

from gaps_v1_validator.errors import ValidationReport  # noqa: E402
from gaps_v1_validator.loader import load_json, load_yaml  # noqa: E402
from gaps_v1_validator.schema_check import validate_schema  # noqa: E402

DEFAULT_SCHEMA = REPO_ROOT / "gaps" / "schema" / "v1" / "ga-process.schema.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--level", choices=["descriptive", "machine-validatable", "generative"], default=None,
                        help="Override the conformance level declared in the spec.")
    args = parser.parse_args()

    report = ValidationReport()
    try:
        spec = load_yaml(args.spec)
        schema = load_json(args.schema)
    except (FileNotFoundError, RuntimeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    validate_schema(spec, schema, report)

    # Subsequent tasks register additional checks here.
    from gaps_v1_validator import cross_refs, catalog_refs, state_machine, gate_decisions, authority, conformance, oscal_refs

    cross_refs.check(spec, report)
    catalog_refs.check(spec, args.spec, report)
    state_machine.check(spec, report)
    gate_decisions.check(spec, report)
    authority.check(spec, report)
    oscal_refs.check(spec, args.spec, report)
    conformance.check(spec, args.level, report)

    if not report.ok:
        print(report.render(), file=sys.stderr)
        print(f"FAIL {args.spec}: {len(report.issues)} issue(s)", file=sys.stderr)
        return 1
    print(f"GAPS v1 spec validated: {args.spec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Note: the imports of `cross_refs`, `catalog_refs`, etc. will fail until later tasks create those modules. To unblock incremental commits, **temporarily stub** the missing modules now so the CLI runs schema-only:

Create `scripts/gaps_v1_validator/cross_refs.py`:

```python
"""Stub: filled in by Task 2."""

from .errors import ValidationReport


def check(spec: dict, report: ValidationReport) -> None:
    return
```

Repeat the same stub for `catalog_refs.py`, `state_machine.py`, `gate_decisions.py`, `authority.py`, `conformance.py`, `oscal_refs.py` — adjust signatures to match the imports (`catalog_refs.check(spec, spec_path, report)`, `conformance.check(spec, level, report)`, `oscal_refs.check(spec, spec_path, report)`):

`scripts/gaps_v1_validator/catalog_refs.py`:

```python
from pathlib import Path
from .errors import ValidationReport


def check(spec: dict, spec_path: Path, report: ValidationReport) -> None:
    return
```

`scripts/gaps_v1_validator/state_machine.py`:

```python
from .errors import ValidationReport


def check(spec: dict, report: ValidationReport) -> None:
    return
```

`scripts/gaps_v1_validator/gate_decisions.py`:

```python
from .errors import ValidationReport


def check(spec: dict, report: ValidationReport) -> None:
    return
```

`scripts/gaps_v1_validator/authority.py`:

```python
from .errors import ValidationReport


def check(spec: dict, report: ValidationReport) -> None:
    return
```

`scripts/gaps_v1_validator/conformance.py`:

```python
from .errors import ValidationReport


def check(spec: dict, level: str | None, report: ValidationReport) -> None:
    return
```

`scripts/gaps_v1_validator/oscal_refs.py`:

```python
from pathlib import Path
from .errors import ValidationReport


def check(spec: dict, spec_path: Path, report: ValidationReport) -> None:
    return
```

- [ ] **Step 6: Confirm the Phase 1 minimal fixture still passes**

```bash
python3 scripts/validate-gaps-v1.py gaps/examples/v1/minimal/ga-process.v1.yml
```

Expected: `GAPS v1 spec validated: ...`. No regression.

- [ ] **Step 7: Run the existing v1 schema tests**

```bash
python3 -m unittest tests.gaps.v1.test_validate_gaps_v1 -v
```

Expected: all pass.

- [ ] **Step 8: Commit Task 1**

```bash
git add scripts/gaps_v1_validator scripts/validate-gaps-v1.py
git commit -m "Reorganize GAPS v1 validator into a module package"
```

---

### Task 2: Internal cross-reference resolution

**Files:**
- Modify: `scripts/gaps_v1_validator/cross_refs.py`
- Create: `tests/gaps/v1/test_cross_refs.py`
- Create: `tests/gaps/v1/fixtures/invalid/unresolved_role.yml`
- Create: `tests/gaps/v1/fixtures/invalid/orphan_state.yml`
- Create: `tests/gaps/v1/fixtures/invalid/duplicate_gate_id.yml`

Cross-reference rules:

- Every `gate.approvalRole` resolves to a `roles[].id`.
- Every `role.canApprove[]` element resolves to a `gates[].id`.
- Every `lane.skills[]` element is a non-empty slug (string already validated by schema).
- `gate.id` is unique across all gates.
- `lane.id` and `role.id` are unique within their arrays.
- Per lane: `state.id` is unique within that lane; `transition.from`/`transition.to` resolve to a state within the same lane; `transition.gate` resolves to a top-level gate id when present.
- Every `gate.decision.effect.transitionTo` resolves to a state in some lane (may span lanes when a decision triggers a cross-lane transition; the resolver searches all lanes).
- Every `gate.decision.effect.recordEvidence[]` resolves to an `evidenceModel.caseFileItems[].id`.
- Every `lane.evidenceInputs[]`, `lane.evidenceOutputs[]`, `riskPatterns[].evidenceRefs[]`, `controlAssessment.controlImplementations[].implementedBy.evidence[]` resolves to a case-file-item id.

- [ ] **Step 1: Write the failing tests**

Create `tests/gaps/v1/test_cross_refs.py`:

```python
"""Tests for cross_refs.check."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-gaps-v1.py"
FIXTURES = ROOT / "tests" / "gaps" / "v1" / "fixtures" / "invalid"


def run(spec: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(spec)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class CrossRefsTests(unittest.TestCase):
    def test_unresolved_role_fails(self) -> None:
        result = run(FIXTURES / "unresolved_role.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("approvalRole", result.stderr)
        self.assertIn("does not resolve", result.stderr)

    def test_orphan_state_fails(self) -> None:
        result = run(FIXTURES / "orphan_state.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("transition", result.stderr)
        self.assertIn("does not resolve", result.stderr)

    def test_duplicate_gate_id_fails(self) -> None:
        result = run(FIXTURES / "duplicate_gate_id.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate gate id", result.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Write the invalid fixtures**

The invalid fixtures are minimal-fixture variants with a single rule broken. To keep them readable, build them from the minimal fixture in `gaps/examples/v1/minimal/ga-process.v1.yml`.

Create `tests/gaps/v1/fixtures/invalid/unresolved_role.yml` — a minimal fixture variant with a gate whose approvalRole points to a non-existent role:

```yaml
gapsVersion: "1.0.0"
specStatus: draft
conformanceLevel: descriptive

process:
  id: invalid-unresolved-role
  name: Invalid fixture — unresolved approvalRole
  purpose: Triggers cross-refs rule for unresolved approvalRole.
  scope:
    includes: [test fixture]
    excludes: [any real process]

substrate:
  oscalControlCatalogs:
    - gaps/catalogs/v1/controls/nist-ai-rmf.json
  actionCatalog: gaps/catalogs/v1/actions.yml
  evidenceCatalog: gaps/catalogs/v1/evidence-kinds.yml
  riskPatternCatalog: gaps/catalogs/v1/risk-patterns.yml

roles:
  - id: process_owner
    label: Process owner
    accountabilityScope: Test fixture only.

evidenceModel:
  caseFileItems:
    - id: dummy-evidence
      kind: context-observation
      label: Dummy
      producer: lane:single_lane
      consumer:
        - role:process_owner

lanes:
  - id: single_lane
    label: Single lane
    purpose: Test only.
    authority:
      plane: data_plane
      autonomyTier: draft
      riskTier: low
      allowedActions:
        - draft-artifact
      prohibitedActions:
        - approve-own-work
    skills:
      - test-fixture-skill

gates:
  - id: nonsense_gate
    label: Nonsense gate
    gateType: validating
    approvalRole: nonexistent_role

projectionPolicy:
  canonicalStateSource: repo-local-ledger
  pathPattern: state/**

riskPatterns:
  - patternRef: post-hoc-governance
    mitigations: [N/A]

controlAssessment:
  catalogRefs: []
  controlImplementations: []

freshness:
  reviewedAt: "2026-05-18"
  driftPolicy: Test fixture.

knownGaps: []
```

Create `tests/gaps/v1/fixtures/invalid/orphan_state.yml` — a fixture whose lane has a transition pointing to an unknown state id:

```yaml
gapsVersion: "1.0.0"
specStatus: draft
conformanceLevel: descriptive

process:
  id: invalid-orphan-state
  name: Invalid fixture — orphan transition target
  purpose: Triggers cross-refs rule for unresolved transition target.
  scope:
    includes: [test fixture]
    excludes: [any real process]

substrate:
  oscalControlCatalogs:
    - gaps/catalogs/v1/controls/nist-ai-rmf.json
  actionCatalog: gaps/catalogs/v1/actions.yml
  evidenceCatalog: gaps/catalogs/v1/evidence-kinds.yml
  riskPatternCatalog: gaps/catalogs/v1/risk-patterns.yml

roles:
  - id: process_owner
    label: Process owner
    accountabilityScope: Test fixture only.

evidenceModel:
  caseFileItems:
    - id: dummy-evidence
      kind: context-observation
      label: Dummy
      producer: lane:single_lane
      consumer:
        - role:process_owner

lanes:
  - id: single_lane
    label: Single lane
    purpose: Test only.
    authority:
      plane: data_plane
      autonomyTier: draft
      riskTier: low
      allowedActions:
        - draft-artifact
      prohibitedActions:
        - approve-own-work
    stateModel:
      states:
        - id: open
          label: Open
          isInitial: true
        - id: closed
          label: Closed
          isTerminal: true
      transitions:
        - id: t-open-to-closed
          from: open
          to: nonexistent_state
    skills:
      - test-fixture-skill

gates: []

projectionPolicy:
  canonicalStateSource: repo-local-ledger
  pathPattern: state/**

riskPatterns:
  - patternRef: post-hoc-governance
    mitigations: [N/A]

controlAssessment:
  catalogRefs: []
  controlImplementations: []

freshness:
  reviewedAt: "2026-05-18"
  driftPolicy: Test fixture.

knownGaps: []
```

Create `tests/gaps/v1/fixtures/invalid/duplicate_gate_id.yml`:

```yaml
gapsVersion: "1.0.0"
specStatus: draft
conformanceLevel: descriptive

process:
  id: invalid-duplicate-gate
  name: Invalid fixture — duplicate gate id
  purpose: Triggers cross-refs rule for unique gate ids.
  scope:
    includes: [test fixture]
    excludes: [any real process]

substrate:
  oscalControlCatalogs:
    - gaps/catalogs/v1/controls/nist-ai-rmf.json
  actionCatalog: gaps/catalogs/v1/actions.yml
  evidenceCatalog: gaps/catalogs/v1/evidence-kinds.yml
  riskPatternCatalog: gaps/catalogs/v1/risk-patterns.yml

roles:
  - id: process_owner
    label: Process owner
    accountabilityScope: Test fixture only.

evidenceModel:
  caseFileItems:
    - id: dummy-evidence
      kind: context-observation
      label: Dummy
      producer: lane:single_lane
      consumer:
        - role:process_owner

lanes:
  - id: single_lane
    label: Single lane
    purpose: Test only.
    authority:
      plane: data_plane
      autonomyTier: draft
      riskTier: low
      allowedActions:
        - draft-artifact
      prohibitedActions:
        - approve-own-work
    skills:
      - test-fixture-skill

gates:
  - id: same_id
    label: First
    gateType: validating
    approvalRole: process_owner
  - id: same_id
    label: Second
    gateType: validating
    approvalRole: process_owner

projectionPolicy:
  canonicalStateSource: repo-local-ledger
  pathPattern: state/**

riskPatterns:
  - patternRef: post-hoc-governance
    mitigations: [N/A]

controlAssessment:
  catalogRefs: []
  controlImplementations: []

freshness:
  reviewedAt: "2026-05-18"
  driftPolicy: Test fixture.

knownGaps: []
```

Create `tests/gaps/v1/fixtures/invalid/__init__.py` as an empty file so Python treats it as a package (for any test discovery that walks into it).

```bash
touch tests/gaps/v1/fixtures/invalid/__init__.py
```

- [ ] **Step 3: Run the tests, confirm they fail**

```bash
python3 -m unittest tests.gaps.v1.test_cross_refs -v
```

Expected: tests FAIL because `cross_refs.check` is still a stub.

- [ ] **Step 4: Implement `cross_refs.check`**

Replace `scripts/gaps_v1_validator/cross_refs.py`:

```python
"""Internal cross-reference resolution for GAPS v1 specs."""

from __future__ import annotations

from typing import Any

from .errors import ValidationReport


def _collect_lane_states(lane: dict[str, Any]) -> dict[str, dict[str, Any]]:
    state_model = lane.get("stateModel") or {}
    states = state_model.get("states") or []
    return {state["id"]: state for state in states if "id" in state}


def check(spec: dict[str, Any], report: ValidationReport) -> None:
    role_ids = {role["id"] for role in spec.get("roles", []) if "id" in role}
    role_id_counts: dict[str, int] = {}
    for role in spec.get("roles", []):
        role_id_counts[role["id"]] = role_id_counts.get(role["id"], 0) + 1
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

    case_file_ids = {item["id"] for item in spec.get("evidenceModel", {}).get("caseFileItems", []) if "id" in item}

    all_states: dict[str, str] = {}  # state_id -> owning lane id (first wins)
    for lane in spec.get("lanes", []):
        lane_states = _collect_lane_states(lane)
        state_id_counts: dict[str, int] = {}
        for sid in lane_states.keys():
            state_id_counts[sid] = state_id_counts.get(sid, 0) + 1
        for sid, count in state_id_counts.items():
            if count > 1:
                report.add("cross-refs", f"$.lanes[id={lane.get('id')}].stateModel.states[id={sid}]", f"duplicate state id {sid!r} within lane")
        for sid in lane_states:
            all_states.setdefault(sid, lane.get("id"))
        for transition in lane.get("stateModel", {}).get("transitions", []):
            tpath = f"$.lanes[id={lane.get('id')}].stateModel.transitions[id={transition.get('id')}]"
            for prop in ("from", "to"):
                target = transition.get(prop)
                if target is not None and target not in lane_states:
                    report.add("cross-refs", f"{tpath}.{prop}", f"state {target!r} does not resolve within lane {lane.get('id')!r}")
            gate_on_transition = transition.get("gate")
            if gate_on_transition is not None and gate_on_transition not in gate_id_set:
                report.add("cross-refs", f"{tpath}.gate", f"gate {gate_on_transition!r} does not resolve")

    for role in spec.get("roles", []):
        for index, gate_ref in enumerate(role.get("canApprove", []) or []):
            if gate_ref not in gate_id_set:
                report.add("cross-refs", f"$.roles[id={role.get('id')}].canApprove[{index}]", f"gate {gate_ref!r} does not resolve")

    for gate in spec.get("gates", []):
        role_ref = gate.get("approvalRole")
        if role_ref is not None and role_ref not in role_ids:
            report.add("cross-refs", f"$.gates[id={gate.get('id')}].approvalRole", f"role {role_ref!r} does not resolve")
        decision = gate.get("decision") or {}
        for index, inp in enumerate(decision.get("inputs", []) or []):
            if inp not in case_file_ids:
                report.add("cross-refs", f"$.gates[id={gate.get('id')}].decision.inputs[{index}]", f"case file item {inp!r} does not resolve")
        for rule_index, rule in enumerate(decision.get("rules", []) or []):
            effect = rule.get("effect") or {}
            transition_to = effect.get("transitionTo")
            if transition_to is not None and transition_to not in all_states:
                report.add("cross-refs", f"$.gates[id={gate.get('id')}].decision.rules[{rule_index}].effect.transitionTo", f"state {transition_to!r} does not resolve")
            for ev_index, ev in enumerate(effect.get("recordEvidence", []) or []):
                if ev not in case_file_ids:
                    report.add("cross-refs", f"$.gates[id={gate.get('id')}].decision.rules[{rule_index}].effect.recordEvidence[{ev_index}]", f"case file item {ev!r} does not resolve")

    for lane in spec.get("lanes", []):
        for prop in ("evidenceInputs", "evidenceOutputs"):
            for index, ev in enumerate(lane.get(prop, []) or []):
                if ev not in case_file_ids:
                    report.add("cross-refs", f"$.lanes[id={lane.get('id')}].{prop}[{index}]", f"case file item {ev!r} does not resolve")

    for index, pattern in enumerate(spec.get("riskPatterns", []) or []):
        for ev_index, ev in enumerate(pattern.get("evidenceRefs", []) or []):
            if ev not in case_file_ids:
                report.add("cross-refs", f"$.riskPatterns[{index}].evidenceRefs[{ev_index}]", f"case file item {ev!r} does not resolve")

    for index, impl in enumerate(spec.get("controlAssessment", {}).get("controlImplementations", []) or []):
        ev_refs = (impl.get("implementedBy") or {}).get("evidence", []) or []
        for ev_index, ev in enumerate(ev_refs):
            if ev not in case_file_ids:
                report.add("cross-refs", f"$.controlAssessment.controlImplementations[{index}].implementedBy.evidence[{ev_index}]", f"case file item {ev!r} does not resolve")
```

- [ ] **Step 5: Run the tests, confirm they pass**

```bash
python3 -m unittest tests.gaps.v1.test_cross_refs -v
```

Expected: all three tests PASS.

- [ ] **Step 6: Confirm the minimal fixture still validates**

```bash
python3 scripts/validate-gaps-v1.py gaps/examples/v1/minimal/ga-process.v1.yml
```

Expected: success.

- [ ] **Step 7: Commit Task 2**

```bash
git add scripts/gaps_v1_validator/cross_refs.py tests/gaps/v1/test_cross_refs.py tests/gaps/v1/fixtures/invalid
git commit -m "Add GAPS v1 internal cross-reference resolution"
```

---

### Task 3: Catalog reference resolution

**Files:**
- Modify: `scripts/gaps_v1_validator/catalog_refs.py`
- Create: `tests/gaps/v1/test_catalog_refs.py`
- Create: `tests/gaps/v1/fixtures/invalid/unresolved_action.yml`

Rules:

- Every action id appearing in `lane.authority.allowedActions`, `lane.authority.prohibitedActions`, `role.decisionRights`, `lane.autonomousResponsibilities`, `controlPlaneActions[].actions` resolves to an action catalog id OR a `process.localActions[].id`.
- An action id may not appear in both `allowedActions` and `prohibitedActions` for the same lane.
- Every `evidenceModel.caseFileItems[].kind` resolves to an evidence-kinds catalog id.
- Every `riskPatterns[].patternRef` resolves to a risk-patterns catalog id.
- `process.localActions[].id` must not collide with a universal action catalog id.

- [ ] **Step 1: Write the failing test**

Create `tests/gaps/v1/test_catalog_refs.py`:

```python
"""Tests for catalog_refs.check."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-gaps-v1.py"
FIXTURES = ROOT / "tests" / "gaps" / "v1" / "fixtures" / "invalid"


def run(spec: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(spec)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class CatalogRefsTests(unittest.TestCase):
    def test_unresolved_action_fails(self) -> None:
        result = run(FIXTURES / "unresolved_action.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not-a-real-action", result.stderr)
        self.assertIn("action catalog", result.stderr)

    def test_action_in_allowed_and_prohibited_fails(self) -> None:
        result = run(FIXTURES / "contradictory_actions.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("both allowed and prohibited", result.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Write the invalid fixtures**

`tests/gaps/v1/fixtures/invalid/unresolved_action.yml`:

```yaml
gapsVersion: "1.0.0"
specStatus: draft
conformanceLevel: descriptive

process:
  id: invalid-unresolved-action
  name: Invalid fixture — action not in catalog
  purpose: Triggers catalog-refs rule for unresolved action.
  scope:
    includes: [test fixture]
    excludes: [any real process]

substrate:
  oscalControlCatalogs:
    - gaps/catalogs/v1/controls/nist-ai-rmf.json
  actionCatalog: gaps/catalogs/v1/actions.yml
  evidenceCatalog: gaps/catalogs/v1/evidence-kinds.yml
  riskPatternCatalog: gaps/catalogs/v1/risk-patterns.yml

roles:
  - id: process_owner
    label: Process owner
    accountabilityScope: Test fixture only.

evidenceModel:
  caseFileItems:
    - id: dummy-evidence
      kind: context-observation
      label: Dummy
      producer: lane:single_lane
      consumer:
        - role:process_owner

lanes:
  - id: single_lane
    label: Single lane
    purpose: Test only.
    authority:
      plane: data_plane
      autonomyTier: draft
      riskTier: low
      allowedActions:
        - not-a-real-action
      prohibitedActions:
        - approve-own-work
    skills:
      - test-fixture-skill

gates: []

projectionPolicy:
  canonicalStateSource: repo-local-ledger
  pathPattern: state/**

riskPatterns:
  - patternRef: post-hoc-governance
    mitigations: [N/A]

controlAssessment:
  catalogRefs: []
  controlImplementations: []

freshness:
  reviewedAt: "2026-05-18"
  driftPolicy: Test fixture.

knownGaps: []
```

`tests/gaps/v1/fixtures/invalid/contradictory_actions.yml` — same shape, but allowedActions includes `draft-artifact` and prohibitedActions also includes `draft-artifact`:

```yaml
gapsVersion: "1.0.0"
specStatus: draft
conformanceLevel: descriptive

process:
  id: invalid-contradictory-actions
  name: Invalid fixture — same action allowed and prohibited
  purpose: Triggers catalog-refs rule for contradictory authority.
  scope:
    includes: [test fixture]
    excludes: [any real process]

substrate:
  oscalControlCatalogs:
    - gaps/catalogs/v1/controls/nist-ai-rmf.json
  actionCatalog: gaps/catalogs/v1/actions.yml
  evidenceCatalog: gaps/catalogs/v1/evidence-kinds.yml
  riskPatternCatalog: gaps/catalogs/v1/risk-patterns.yml

roles:
  - id: process_owner
    label: Process owner
    accountabilityScope: Test fixture only.

evidenceModel:
  caseFileItems:
    - id: dummy-evidence
      kind: context-observation
      label: Dummy
      producer: lane:single_lane
      consumer:
        - role:process_owner

lanes:
  - id: single_lane
    label: Single lane
    purpose: Test only.
    authority:
      plane: data_plane
      autonomyTier: draft
      riskTier: low
      allowedActions:
        - draft-artifact
      prohibitedActions:
        - draft-artifact
    skills:
      - test-fixture-skill

gates: []

projectionPolicy:
  canonicalStateSource: repo-local-ledger
  pathPattern: state/**

riskPatterns:
  - patternRef: post-hoc-governance
    mitigations: [N/A]

controlAssessment:
  catalogRefs: []
  controlImplementations: []

freshness:
  reviewedAt: "2026-05-18"
  driftPolicy: Test fixture.

knownGaps: []
```

- [ ] **Step 3: Run the tests, confirm they fail**

```bash
python3 -m unittest tests.gaps.v1.test_catalog_refs -v
```

Expected: tests FAIL because `catalog_refs.check` is still a stub.

- [ ] **Step 4: Implement `catalog_refs.check`**

Replace `scripts/gaps_v1_validator/catalog_refs.py`:

```python
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
    local_actions_decl = {entry["id"] for entry in spec.get("process", {}).get("localActions", []) or [] if "id" in entry}
    for local_id in local_actions_decl:
        if local_id in universal_actions:
            report.add("catalog-refs", f"$.process.localActions[id={local_id}]", f"local action {local_id!r} collides with universal catalog id")
    resolvable_actions = universal_actions | local_actions_decl

    evidence_kinds = _load_evidence_kind_ids(spec, spec_path, report)
    risk_patterns = _load_risk_pattern_ids(spec, spec_path, report)

    for lane in spec.get("lanes", []):
        authority = lane.get("authority", {})
        allowed = list(authority.get("allowedActions", []) or [])
        prohibited = list(authority.get("prohibitedActions", []) or [])
        overlap = set(allowed) & set(prohibited)
        for action_id in sorted(overlap):
            report.add("catalog-refs", f"$.lanes[id={lane.get('id')}].authority", f"action {action_id!r} is both allowed and prohibited")
        for index, action_id in enumerate(allowed):
            if action_id not in resolvable_actions:
                report.add("catalog-refs", f"$.lanes[id={lane.get('id')}].authority.allowedActions[{index}]", f"action {action_id!r} not in action catalog")
        for index, action_id in enumerate(prohibited):
            if action_id not in resolvable_actions:
                report.add("catalog-refs", f"$.lanes[id={lane.get('id')}].authority.prohibitedActions[{index}]", f"action {action_id!r} not in action catalog")
        for index, action_id in enumerate(lane.get("autonomousResponsibilities", []) or []):
            if action_id not in resolvable_actions:
                report.add("catalog-refs", f"$.lanes[id={lane.get('id')}].autonomousResponsibilities[{index}]", f"action {action_id!r} not in action catalog")

    for role in spec.get("roles", []):
        for index, action_id in enumerate(role.get("decisionRights", []) or []):
            if action_id not in resolvable_actions:
                report.add("catalog-refs", f"$.roles[id={role.get('id')}].decisionRights[{index}]", f"action {action_id!r} not in action catalog")

    for index, item in enumerate(spec.get("controlPlaneActions", []) or []):
        for ai, action_id in enumerate(item.get("actions", []) or []):
            if action_id not in resolvable_actions:
                report.add("catalog-refs", f"$.controlPlaneActions[{index}].actions[{ai}]", f"action {action_id!r} not in action catalog")

    for index, item in enumerate(spec.get("evidenceModel", {}).get("caseFileItems", []) or []):
        kind = item.get("kind")
        if kind is not None and kind not in evidence_kinds:
            report.add("catalog-refs", f"$.evidenceModel.caseFileItems[{index}].kind", f"evidence kind {kind!r} not in evidence-kinds catalog")

    for index, pattern in enumerate(spec.get("riskPatterns", []) or []):
        ref = pattern.get("patternRef")
        if ref is not None and ref not in risk_patterns:
            report.add("catalog-refs", f"$.riskPatterns[{index}].patternRef", f"risk pattern {ref!r} not in risk-patterns catalog")
```

- [ ] **Step 5: Run the tests, confirm they pass**

```bash
python3 -m unittest tests.gaps.v1.test_catalog_refs -v
python3 scripts/validate-gaps-v1.py gaps/examples/v1/minimal/ga-process.v1.yml
```

Expected: tests PASS; minimal fixture still validates.

- [ ] **Step 6: Commit Task 3**

```bash
git add scripts/gaps_v1_validator/catalog_refs.py tests/gaps/v1/test_catalog_refs.py tests/gaps/v1/fixtures/invalid/unresolved_action.yml tests/gaps/v1/fixtures/invalid/contradictory_actions.yml
git commit -m "Add GAPS v1 catalog reference resolution"
```

---

### Task 4: State-machine soundness

**Files:**
- Modify: `scripts/gaps_v1_validator/state_machine.py`
- Create: `tests/gaps/v1/test_state_machine.py`

Rules per lane with a `stateModel`:

- Exactly one state is `isInitial: true`.
- At least one state is `isTerminal: true`.
- Every state is reachable from the initial state via the lane's transitions.
- No transition originates from a `isTerminal: true` state.
- Every non-terminal state has at least one outgoing transition.
- Transition ids are unique within the lane.

- [ ] **Step 1: Write the failing test**

Create `tests/gaps/v1/test_state_machine.py`:

```python
"""Tests for state_machine.check."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-gaps-v1.py"
MINIMAL = (ROOT / "gaps" / "examples" / "v1" / "minimal" / "ga-process.v1.yml").read_text()


def run(content: str) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as handle:
        handle.write(content)
        path = Path(handle.name)
    try:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        path.unlink(missing_ok=True)


def with_state_model(states_block: str, transitions_block: str) -> str:
    lane_extension = textwrap.dedent(
        f"""\
            stateModel:
              states:
        {states_block}
              transitions:
        {transitions_block}
        """
    )
    return MINIMAL.replace(
        "    skills:\n      - minimal-example-draft\n",
        lane_extension + "    skills:\n      - minimal-example-draft\n",
    )


class StateMachineTests(unittest.TestCase):
    def test_unreachable_state_fails(self) -> None:
        content = with_state_model(
            states_block="        - {id: open, label: Open, isInitial: true}\n        - {id: detached, label: Detached, isTerminal: true}\n        - {id: closed, label: Closed, isTerminal: true}",
            transitions_block="        - {id: t1, from: open, to: closed}",
        )
        result = run(content)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("detached", result.stderr)
        self.assertIn("unreachable", result.stderr)

    def test_no_initial_state_fails(self) -> None:
        content = with_state_model(
            states_block="        - {id: open, label: Open}\n        - {id: closed, label: Closed, isTerminal: true}",
            transitions_block="        - {id: t1, from: open, to: closed}",
        )
        result = run(content)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("isInitial", result.stderr)

    def test_two_initial_states_fails(self) -> None:
        content = with_state_model(
            states_block="        - {id: a, label: A, isInitial: true}\n        - {id: b, label: B, isInitial: true, isTerminal: true}",
            transitions_block="        - {id: t1, from: a, to: b}",
        )
        result = run(content)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one initial state", result.stderr)

    def test_no_terminal_state_fails(self) -> None:
        content = with_state_model(
            states_block="        - {id: open, label: Open, isInitial: true}",
            transitions_block="        - {id: t1, from: open, to: open}",
        )
        result = run(content)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("at least one terminal state", result.stderr)

    def test_terminal_with_outgoing_transition_fails(self) -> None:
        content = with_state_model(
            states_block="        - {id: open, label: Open, isInitial: true}\n        - {id: closed, label: Closed, isTerminal: true}",
            transitions_block="        - {id: t1, from: open, to: closed}\n        - {id: t2, from: closed, to: open}",
        )
        result = run(content)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("terminal state", result.stderr)
        self.assertIn("outgoing", result.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests, confirm they fail**

```bash
python3 -m unittest tests.gaps.v1.test_state_machine -v
```

Expected: all five tests FAIL.

- [ ] **Step 3: Implement `state_machine.check`**

Replace `scripts/gaps_v1_validator/state_machine.py`:

```python
"""Per-lane state machine soundness for GAPS v1 specs."""

from __future__ import annotations

from collections import deque
from typing import Any

from .errors import ValidationReport


def check(spec: dict[str, Any], report: ValidationReport) -> None:
    for lane in spec.get("lanes", []):
        state_model = lane.get("stateModel")
        if not state_model:
            continue
        lane_id = lane.get("id")
        path = f"$.lanes[id={lane_id}].stateModel"
        states: list[dict[str, Any]] = state_model.get("states") or []
        transitions: list[dict[str, Any]] = state_model.get("transitions") or []

        initial_states = [s["id"] for s in states if s.get("isInitial")]
        terminal_states = {s["id"] for s in states if s.get("isTerminal")}
        all_state_ids = {s["id"] for s in states if "id" in s}

        if len(initial_states) != 1:
            report.add("state-machine", path, f"expected exactly one initial state (isInitial: true); found {len(initial_states)}")
        if not terminal_states:
            report.add("state-machine", path, "expected at least one terminal state (isTerminal: true); found none")

        transition_ids: dict[str, int] = {}
        for transition in transitions:
            tid = transition.get("id")
            if tid is None:
                continue
            transition_ids[tid] = transition_ids.get(tid, 0) + 1
        for tid, count in transition_ids.items():
            if count > 1:
                report.add("state-machine", f"{path}.transitions[id={tid}]", f"duplicate transition id {tid!r} within lane")

        for transition in transitions:
            src = transition.get("from")
            if src in terminal_states:
                report.add("state-machine", f"{path}.transitions[id={transition.get('id')}]", f"terminal state {src!r} has outgoing transition")

        if initial_states:
            adjacency: dict[str, list[str]] = {sid: [] for sid in all_state_ids}
            for transition in transitions:
                src = transition.get("from")
                dst = transition.get("to")
                if src in adjacency and dst is not None:
                    adjacency[src].append(dst)
            queue: deque[str] = deque([initial_states[0]])
            reached: set[str] = set()
            while queue:
                node = queue.popleft()
                if node in reached:
                    continue
                reached.add(node)
                for neighbour in adjacency.get(node, []):
                    if neighbour not in reached:
                        queue.append(neighbour)
            for sid in sorted(all_state_ids - reached):
                report.add("state-machine", f"{path}.states[id={sid}]", f"state {sid!r} is unreachable from initial state")

        for sid in all_state_ids:
            if sid in terminal_states:
                continue
            has_outgoing = any(t.get("from") == sid for t in transitions)
            if not has_outgoing:
                report.add("state-machine", f"{path}.states[id={sid}]", f"non-terminal state {sid!r} has no outgoing transition")
```

- [ ] **Step 4: Run the tests, confirm they pass**

```bash
python3 -m unittest tests.gaps.v1.test_state_machine -v
python3 scripts/validate-gaps-v1.py gaps/examples/v1/minimal/ga-process.v1.yml
```

Expected: tests PASS; minimal fixture still validates (it has no `stateModel` block, so no state-machine checks fire).

- [ ] **Step 5: Commit Task 4**

```bash
git add scripts/gaps_v1_validator/state_machine.py tests/gaps/v1/test_state_machine.py
git commit -m "Add GAPS v1 state-machine soundness checks"
```

---

### Task 5: FEEL-subset expression evaluator

**Files:**
- Create: `scripts/gaps_v1_validator/feel_subset.py`
- Create: `tests/gaps/v1/test_feel_subset.py`

The FEEL subset supports expressions used in `transition.guard.rules[].when` and `gate.decision.rules[].when`. Grammar:

```
expr      := orExpr
orExpr    := andExpr ("or" andExpr)*
andExpr   := notExpr ("and" notExpr)*
notExpr   := "not" notExpr | primary
primary   := "(" expr ")" | comparison | predicate | "true" | "false"
predicate := "defined(" ident ")" | "undefined(" ident ")"
comparison:= ident op literal | ident op ident
op        := "==" | "!=" | ">" | "<" | ">=" | "<="
literal   := string | number | "true" | "false" | "null"
ident     := /[a-zA-Z_][a-zA-Z0-9_.-]*/
string    := "..." | '...'
number    := /-?[0-9]+(\.[0-9]+)?/
```

For Phase 2 the evaluator is used to (a) parse expressions and surface syntax errors, (b) check that referenced idents are declared in the `inputs` list. Actual evaluation (taking concrete evidence values and computing approve/escalate/reject) lives in Phase 4's generator and Phase 5's round-trip tooling.

- [ ] **Step 1: Write the failing test**

Create `tests/gaps/v1/test_feel_subset.py`:

```python
"""Tests for feel_subset parser."""

from __future__ import annotations

import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from gaps_v1_validator.feel_subset import parse, FeelParseError, idents_used  # noqa: E402


class FeelSubsetTests(unittest.TestCase):
    def test_parse_simple_comparison(self) -> None:
        node = parse("status == \"open\"")
        self.assertEqual(node.kind, "comparison")

    def test_parse_defined(self) -> None:
        node = parse("defined(approval_attestation)")
        self.assertEqual(node.kind, "predicate")

    def test_parse_boolean_combinator(self) -> None:
        node = parse("defined(prd) and prd.approved == true")
        self.assertEqual(node.kind, "and")

    def test_parse_not(self) -> None:
        node = parse("not undefined(x)")
        self.assertEqual(node.kind, "not")

    def test_parse_syntax_error(self) -> None:
        with self.assertRaises(FeelParseError):
            parse("status ==")

    def test_idents_used_extracts_top_level_names(self) -> None:
        names = idents_used(parse("status == \"open\" and defined(prd) and budget > 1000"))
        self.assertEqual({"status", "prd", "budget"}, names)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test, confirm it fails**

```bash
python3 -m unittest tests.gaps.v1.test_feel_subset -v
```

Expected: ImportError, then test failures once import is unblocked.

- [ ] **Step 3: Implement `feel_subset.py`**

Create `scripts/gaps_v1_validator/feel_subset.py`:

```python
"""Tiny FEEL-subset parser used by transition guards and gate decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class FeelParseError(Exception):
    pass


@dataclass
class Node:
    kind: str
    children: list["Node"]
    value: Optional[str] = None


_TOKENS = ("(", ")", "==", "!=", ">=", "<=", ">", "<")
_KEYWORDS = {"and", "or", "not", "true", "false", "null", "defined", "undefined"}


def _tokenize(expr: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch.isspace():
            i += 1
            continue
        if ch in ('"', "'"):
            quote = ch
            j = i + 1
            while j < len(expr) and expr[j] != quote:
                j += 1
            if j >= len(expr):
                raise FeelParseError(f"unterminated string at {i}")
            tokens.append(expr[i:j + 1])
            i = j + 1
            continue
        for token in _TOKENS:
            if expr.startswith(token, i):
                tokens.append(token)
                i += len(token)
                break
        else:
            j = i
            while j < len(expr) and (expr[j].isalnum() or expr[j] in "._-"):
                j += 1
            if j == i:
                raise FeelParseError(f"unexpected character {ch!r} at {i}")
            tokens.append(expr[i:j])
            i = j
    return tokens


class _Parser:
    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Optional[str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self) -> str:
        if self.pos >= len(self.tokens):
            raise FeelParseError("unexpected end of input")
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def parse_expr(self) -> Node:
        node = self.parse_or()
        if self.pos < len(self.tokens):
            raise FeelParseError(f"trailing tokens: {self.tokens[self.pos:]}")
        return node

    def parse_or(self) -> Node:
        left = self.parse_and()
        while self.peek() == "or":
            self.consume()
            right = self.parse_and()
            left = Node(kind="or", children=[left, right])
        return left

    def parse_and(self) -> Node:
        left = self.parse_not()
        while self.peek() == "and":
            self.consume()
            right = self.parse_not()
            left = Node(kind="and", children=[left, right])
        return left

    def parse_not(self) -> Node:
        if self.peek() == "not":
            self.consume()
            inner = self.parse_not()
            return Node(kind="not", children=[inner])
        return self.parse_primary()

    def parse_primary(self) -> Node:
        token = self.peek()
        if token is None:
            raise FeelParseError("unexpected end of input")
        if token == "(":
            self.consume()
            inner = self.parse_or()
            if self.peek() != ")":
                raise FeelParseError("expected ')'")
            self.consume()
            return inner
        if token in ("true", "false", "null"):
            self.consume()
            return Node(kind="literal", children=[], value=token)
        if token in ("defined", "undefined"):
            self.consume()
            if self.peek() != "(":
                raise FeelParseError(f"expected '(' after {token}")
            self.consume()
            ident_token = self.consume()
            if self.peek() != ")":
                raise FeelParseError(f"expected ')' after {token}({ident_token})")
            self.consume()
            return Node(kind="predicate", children=[], value=f"{token}({ident_token})")
        # comparison: ident op literal-or-ident
        left = self.consume()
        op = self.peek()
        if op not in ("==", "!=", ">", "<", ">=", "<="):
            raise FeelParseError(f"expected comparison operator after {left!r}, got {op!r}")
        self.consume()
        right = self.consume()
        return Node(kind="comparison", children=[Node("ident", [], left), Node("operand", [], right)], value=op)


def parse(expr: str) -> Node:
    parser = _Parser(_tokenize(expr))
    return parser.parse_expr()


def idents_used(node: Node) -> set[str]:
    names: set[str] = set()

    def walk(n: Node) -> None:
        if n.kind == "predicate" and n.value:
            inside = n.value[n.value.index("(") + 1: n.value.rindex(")")]
            names.add(inside.split(".")[0])
            return
        if n.kind == "comparison":
            ident_child = n.children[0]
            operand_child = n.children[1]
            names.add(ident_child.value.split(".")[0])
            if not _is_literal(operand_child.value):
                names.add(operand_child.value.split(".")[0])
            return
        for child in n.children:
            walk(child)

    def _is_literal(token: Optional[str]) -> bool:
        if token is None:
            return True
        if token in ("true", "false", "null"):
            return True
        if token[0] in ("'", '"'):
            return True
        try:
            float(token)
            return True
        except ValueError:
            return False

    walk(node)
    return names
```

- [ ] **Step 4: Run the test, confirm it passes**

```bash
python3 -m unittest tests.gaps.v1.test_feel_subset -v
```

Expected: all six tests PASS.

- [ ] **Step 5: Commit Task 5**

```bash
git add scripts/gaps_v1_validator/feel_subset.py tests/gaps/v1/test_feel_subset.py
git commit -m "Add GAPS v1 FEEL-subset parser"
```

---

### Task 6: Gate decision completeness

**Files:**
- Modify: `scripts/gaps_v1_validator/gate_decisions.py`
- Create: `tests/gaps/v1/test_gate_decisions.py`
- Create: `tests/gaps/v1/fixtures/invalid/incomplete_decision.yml`

Rules per gate that has a `decision` block:

- `decision.rules[*].when` is parseable by the FEEL subset.
- Every identifier used in a `when` expression is declared in `decision.inputs[]`.
- If `else` is absent, the rules must collectively cover all paths. For Phase 2, "cover all paths" is approximated by requiring that for every input identifier referenced, at least one rule covers both `defined(...)` and `undefined(...)` cases, OR an `else` clause is provided. A spec author can satisfy completeness either way.
- `gateType: blocking` requires that at least one rule's `then` is `approve` and at least one is `escalate` or `reject` (otherwise the gate cannot block).
- `decision.effect.transitionTo` and `decision.effect.recordEvidence[]` are already cross-resolved by `cross_refs.check`; this check does not duplicate that.

Same rules apply to `transition.guard` blocks: identifiers in `when` must be declared in `guard.inputs[]`; `else` or full coverage required.

- [ ] **Step 1: Write the failing test**

Create `tests/gaps/v1/test_gate_decisions.py`:

```python
"""Tests for gate_decisions.check."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-gaps-v1.py"
FIXTURES = ROOT / "tests" / "gaps" / "v1" / "fixtures" / "invalid"


def run(spec: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(spec)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class GateDecisionsTests(unittest.TestCase):
    def test_incomplete_decision_fails(self) -> None:
        result = run(FIXTURES / "incomplete_decision.yml")
        self.assertNotEqual(result.returncode, 0)
        combined = result.stderr + result.stdout
        self.assertTrue(
            "undeclared input" in combined.lower() or "missing else" in combined.lower(),
            combined,
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Write the invalid fixture**

`tests/gaps/v1/fixtures/invalid/incomplete_decision.yml` — a gate with a `when` that references an identifier not in its `inputs`:

```yaml
gapsVersion: "1.0.0"
specStatus: draft
conformanceLevel: descriptive

process:
  id: invalid-incomplete-decision
  name: Invalid fixture — incomplete gate decision
  purpose: Triggers gate-decisions rule.
  scope:
    includes: [test fixture]
    excludes: [any real process]

substrate:
  oscalControlCatalogs:
    - gaps/catalogs/v1/controls/nist-ai-rmf.json
  actionCatalog: gaps/catalogs/v1/actions.yml
  evidenceCatalog: gaps/catalogs/v1/evidence-kinds.yml
  riskPatternCatalog: gaps/catalogs/v1/risk-patterns.yml

roles:
  - id: approver
    label: Approver
    accountabilityScope: Test fixture only.

evidenceModel:
  caseFileItems:
    - id: prd
      kind: artifact-reference
      label: PRD
      producer: lane:single_lane
      consumer:
        - role:approver

lanes:
  - id: single_lane
    label: Single lane
    purpose: Test only.
    authority:
      plane: data_plane
      autonomyTier: draft
      riskTier: low
      allowedActions:
        - draft-artifact
      prohibitedActions:
        - approve-own-work
    skills:
      - test-fixture-skill

gates:
  - id: prd_gate
    label: PRD gate
    gateType: blocking
    approvalRole: approver
    decision:
      inputs:
        - prd
      rules:
        - when: undeclared_thing == "yes"
          then: approve

projectionPolicy:
  canonicalStateSource: repo-local-ledger
  pathPattern: state/**

riskPatterns:
  - patternRef: approval-theater
    mitigations: [N/A]

controlAssessment:
  catalogRefs: []
  controlImplementations: []

freshness:
  reviewedAt: "2026-05-18"
  driftPolicy: Test fixture.

knownGaps: []
```

- [ ] **Step 3: Run the test, confirm it fails**

```bash
python3 -m unittest tests.gaps.v1.test_gate_decisions -v
```

Expected: failure due to stub `gate_decisions.check`.

- [ ] **Step 4: Implement `gate_decisions.check`**

Replace `scripts/gaps_v1_validator/gate_decisions.py`:

```python
"""Gate decision and transition guard completeness checks."""

from __future__ import annotations

from typing import Any

from .errors import ValidationReport
from .feel_subset import FeelParseError, idents_used, parse


def _check_rules(rules: list[dict[str, Any]], inputs: list[str], where: str, report: ValidationReport, valid_thens: set[str]) -> None:
    declared = set(inputs)
    for index, rule in enumerate(rules):
        expr = rule.get("when")
        if not isinstance(expr, str):
            report.add("gate-decisions", f"{where}.rules[{index}].when", "missing or non-string expression")
            continue
        try:
            node = parse(expr)
        except FeelParseError as error:
            report.add("gate-decisions", f"{where}.rules[{index}].when", f"FEEL parse error: {error}")
            continue
        used = idents_used(node)
        for ident in sorted(used - declared):
            report.add("gate-decisions", f"{where}.rules[{index}].when", f"undeclared input {ident!r} (not in {where}.inputs)")
        then = rule.get("then")
        if then is not None and then not in valid_thens:
            report.add("gate-decisions", f"{where}.rules[{index}].then", f"value {then!r} not in {sorted(valid_thens)}")


def check(spec: dict[str, Any], report: ValidationReport) -> None:
    for gate in spec.get("gates", []):
        decision = gate.get("decision")
        if not decision:
            continue
        where = f"$.gates[id={gate.get('id')}].decision"
        inputs = list(decision.get("inputs", []) or [])
        rules = list(decision.get("rules", []) or [])
        else_clause = decision.get("else")
        if not rules:
            report.add("gate-decisions", where, "decision has no rules")
            continue
        _check_rules(rules, inputs, where, report, valid_thens={"approve", "escalate", "reject"})
        if else_clause is None:
            covered_idents: set[str] = set()
            for rule in rules:
                try:
                    covered_idents |= idents_used(parse(rule.get("when") or ""))
                except FeelParseError:
                    continue
            if set(inputs) - covered_idents:
                report.add(
                    "gate-decisions",
                    where,
                    "missing else clause and rules do not reference all declared inputs; provide an else or extend rule coverage",
                )
        if gate.get("gateType") == "blocking":
            outcomes = {rule.get("then") for rule in rules}
            if "approve" not in outcomes:
                report.add("gate-decisions", where, "blocking gate must have at least one rule with then: approve")
            if not (outcomes & {"escalate", "reject"}):
                report.add("gate-decisions", where, "blocking gate must have at least one rule with then: escalate or then: reject")

    for lane in spec.get("lanes", []):
        state_model = lane.get("stateModel") or {}
        for transition in state_model.get("transitions", []) or []:
            guard = transition.get("guard")
            if not guard:
                continue
            where = f"$.lanes[id={lane.get('id')}].stateModel.transitions[id={transition.get('id')}].guard"
            inputs = list(guard.get("inputs", []) or [])
            rules = list(guard.get("rules", []) or [])
            if not rules:
                report.add("gate-decisions", where, "guard has no rules")
                continue
            _check_rules(rules, inputs, where, report, valid_thens={"allow", "block"})
            if guard.get("else") is None:
                covered: set[str] = set()
                for rule in rules:
                    try:
                        covered |= idents_used(parse(rule.get("when") or ""))
                    except FeelParseError:
                        continue
                if set(inputs) - covered:
                    report.add("gate-decisions", where, "missing else clause and rules do not reference all declared inputs")
```

- [ ] **Step 5: Run the test, confirm it passes**

```bash
python3 -m unittest tests.gaps.v1.test_gate_decisions -v
python3 scripts/validate-gaps-v1.py gaps/examples/v1/minimal/ga-process.v1.yml
```

Expected: tests PASS; minimal fixture still validates.

- [ ] **Step 6: Commit Task 6**

```bash
git add scripts/gaps_v1_validator/gate_decisions.py tests/gaps/v1/test_gate_decisions.py tests/gaps/v1/fixtures/invalid/incomplete_decision.yml
git commit -m "Add GAPS v1 gate decision and guard completeness checks"
```

---

### Task 7: Authority and projection-policy consistency

**Files:**
- Modify: `scripts/gaps_v1_validator/authority.py`
- Create: `tests/gaps/v1/test_authority.py`
- Create: `tests/gaps/v1/fixtures/invalid/external_system_unmarked.yml`

Rules:

- For every action in `lane.authority.allowedActions` that is a universal catalog action with `alwaysProhibitedAt[]` including the lane's `authority.autonomyTier`, surface an error.
- A `data_plane` lane's `allowedActions` may not contain a `control-plane` category action (per the universal action catalog).
- A `control_plane` lane is permitted to contain both data-plane and control-plane actions.
- `controlPlaneActions[].plane` must equal `control_plane` (schema-enforced) and the actions referenced must include at least one with category `control-plane`.
- `projectionPolicy.externalSystems[]`: if any external system has `role: system-of-record`, `canonicalStateSource` must equal `external-system` or `hybrid`.
- If `canonicalStateSource: repo-local-ledger`, no external system may be `role: system-of-record`.
- Every external system must have `mutationRequiresApproval: true` unless `role: system-of-record`.

- [ ] **Step 1: Write the failing test**

Create `tests/gaps/v1/test_authority.py`:

```python
"""Tests for authority.check."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-gaps-v1.py"
FIXTURES = ROOT / "tests" / "gaps" / "v1" / "fixtures" / "invalid"


def run(spec: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(spec)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class AuthorityTests(unittest.TestCase):
    def test_external_system_unmarked_fails(self) -> None:
        result = run(FIXTURES / "external_system_unmarked.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mutationRequiresApproval", result.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Write the invalid fixture**

`tests/gaps/v1/fixtures/invalid/external_system_unmarked.yml`:

```yaml
gapsVersion: "1.0.0"
specStatus: draft
conformanceLevel: descriptive

process:
  id: invalid-external-system-unmarked
  name: Invalid fixture — external system without approval gate
  purpose: Triggers authority rule for unmarked external system.
  scope:
    includes: [test fixture]
    excludes: [any real process]

substrate:
  oscalControlCatalogs:
    - gaps/catalogs/v1/controls/nist-ai-rmf.json
  actionCatalog: gaps/catalogs/v1/actions.yml
  evidenceCatalog: gaps/catalogs/v1/evidence-kinds.yml
  riskPatternCatalog: gaps/catalogs/v1/risk-patterns.yml

roles:
  - id: process_owner
    label: Process owner
    accountabilityScope: Test fixture only.

evidenceModel:
  caseFileItems:
    - id: dummy-evidence
      kind: context-observation
      label: Dummy
      producer: lane:single_lane
      consumer:
        - role:process_owner

lanes:
  - id: single_lane
    label: Single lane
    purpose: Test only.
    authority:
      plane: data_plane
      autonomyTier: draft
      riskTier: low
      allowedActions:
        - draft-artifact
      prohibitedActions:
        - approve-own-work
    skills:
      - test-fixture-skill

gates: []

projectionPolicy:
  canonicalStateSource: repo-local-ledger
  pathPattern: state/**
  externalSystems:
    - kind: jira
      role: projection-target
      mutationRequiresApproval: false

riskPatterns:
  - patternRef: tool-sprawl
    mitigations: [N/A]

controlAssessment:
  catalogRefs: []
  controlImplementations: []

freshness:
  reviewedAt: "2026-05-18"
  driftPolicy: Test fixture.

knownGaps: []
```

- [ ] **Step 3: Run the test, confirm it fails**

```bash
python3 -m unittest tests.gaps.v1.test_authority -v
```

Expected: failure.

- [ ] **Step 4: Implement `authority.check`**

Replace `scripts/gaps_v1_validator/authority.py`:

```python
"""Authority and projection-policy consistency checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationReport
from .loader import load_yaml, resolve_catalog_path


def _load_action_catalog(spec: dict[str, Any], spec_path: Path) -> dict[str, dict[str, Any]]:
    ref = spec.get("substrate", {}).get("actionCatalog")
    if not ref:
        return {}
    try:
        data = load_yaml(resolve_catalog_path(spec_path, ref))
    except (FileNotFoundError, RuntimeError):
        return {}
    return {entry["id"]: entry for entry in data.get("actions", []) if "id" in entry}


def check(spec: dict[str, Any], report: ValidationReport, spec_path: Path | None = None) -> None:
    """Compatibility shim: spec_path optional so the dispatcher's call signature stays simple."""
    catalog = _load_action_catalog(spec, spec_path) if spec_path is not None else {}

    for lane in spec.get("lanes", []):
        authority = lane.get("authority", {}) or {}
        plane = authority.get("plane")
        tier = authority.get("autonomyTier")
        path = f"$.lanes[id={lane.get('id')}].authority"
        for action_id in authority.get("allowedActions", []) or []:
            entry = catalog.get(action_id)
            if not entry:
                continue
            forbidden_tiers = set(entry.get("alwaysProhibitedAt", []) or [])
            if tier in forbidden_tiers:
                report.add("authority", path, f"action {action_id!r} is alwaysProhibitedAt autonomyTier {tier!r}")
            category = entry.get("category")
            if plane == "data_plane" and category == "control-plane":
                report.add("authority", path, f"action {action_id!r} has category control-plane but lane plane is data_plane")
            if category == "prohibited-anti-pattern":
                report.add("authority", path, f"prohibited-anti-pattern action {action_id!r} must not appear in allowedActions")

    canonical = spec.get("projectionPolicy", {}).get("canonicalStateSource")
    external_systems = spec.get("projectionPolicy", {}).get("externalSystems") or []
    for index, system in enumerate(external_systems):
        spath = f"$.projectionPolicy.externalSystems[{index}]"
        role = system.get("role")
        approval = system.get("mutationRequiresApproval")
        if role != "system-of-record" and approval is not True:
            report.add("authority", spath, "mutationRequiresApproval must be true unless role is system-of-record")
        if role == "system-of-record" and canonical == "repo-local-ledger":
            report.add("authority", spath, "external system declared system-of-record but canonicalStateSource is repo-local-ledger")

    for index, control_plane_item in enumerate(spec.get("controlPlaneActions", []) or []):
        actions = control_plane_item.get("actions") or []
        any_control_plane = False
        for action_id in actions:
            entry = catalog.get(action_id)
            if entry and entry.get("category") == "control-plane":
                any_control_plane = True
                break
        if actions and not any_control_plane:
            report.add(
                "authority",
                f"$.controlPlaneActions[{index}]",
                "controlPlaneActions entry must include at least one action of category control-plane",
            )
```

Note the signature accepts an optional `spec_path` so we can keep the dispatcher's call symmetric. Update the dispatcher to pass it.

- [ ] **Step 5: Update the dispatcher**

In `scripts/validate-gaps-v1.py`, change the `authority.check` call:

```python
authority.check(spec, report, args.spec)
```

- [ ] **Step 6: Run the test, confirm it passes**

```bash
python3 -m unittest tests.gaps.v1.test_authority -v
python3 scripts/validate-gaps-v1.py gaps/examples/v1/minimal/ga-process.v1.yml
```

Expected: tests PASS; minimal fixture still validates.

- [ ] **Step 7: Commit Task 7**

```bash
git add scripts/gaps_v1_validator/authority.py scripts/validate-gaps-v1.py tests/gaps/v1/test_authority.py tests/gaps/v1/fixtures/invalid/external_system_unmarked.yml
git commit -m "Add GAPS v1 authority and projection-policy consistency checks"
```

---

### Task 8: OSCAL control reference resolution

**Files:**
- Modify: `scripts/gaps_v1_validator/oscal_refs.py`
- Create: `tests/gaps/v1/test_oscal_refs.py`
- Create: `tests/gaps/v1/fixtures/invalid/oscal_control_not_in_catalog.yml`

Rules:

- Every `controlAssessment.catalogRefs[]` is a path resolvable from the repo root and validates against the OSCAL catalog meta-schema (Phase 1 schema).
- Every `controlAssessment.controlImplementations[].controlId` resolves to a control id in one of the referenced OSCAL catalogs.
- `controlAssessment.catalogRefs[]` must be a subset of `substrate.oscalControlCatalogs[]`.

- [ ] **Step 1: Write the failing test**

Create `tests/gaps/v1/test_oscal_refs.py`:

```python
"""Tests for oscal_refs.check."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-gaps-v1.py"
FIXTURES = ROOT / "tests" / "gaps" / "v1" / "fixtures" / "invalid"


def run(spec: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(spec)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class OscalRefsTests(unittest.TestCase):
    def test_unknown_control_id_fails(self) -> None:
        result = run(FIXTURES / "oscal_control_not_in_catalog.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BOGUS-1.1", result.stderr)
        self.assertIn("not in any referenced catalog", result.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Write the invalid fixture**

`tests/gaps/v1/fixtures/invalid/oscal_control_not_in_catalog.yml`:

```yaml
gapsVersion: "1.0.0"
specStatus: draft
conformanceLevel: descriptive

process:
  id: invalid-oscal-control
  name: Invalid fixture — controlId not in catalog
  purpose: Triggers oscal-refs rule.
  scope:
    includes: [test fixture]
    excludes: [any real process]

substrate:
  oscalControlCatalogs:
    - gaps/catalogs/v1/controls/nist-ai-rmf.json
  actionCatalog: gaps/catalogs/v1/actions.yml
  evidenceCatalog: gaps/catalogs/v1/evidence-kinds.yml
  riskPatternCatalog: gaps/catalogs/v1/risk-patterns.yml

roles:
  - id: process_owner
    label: Process owner
    accountabilityScope: Test fixture only.

evidenceModel:
  caseFileItems:
    - id: dummy-evidence
      kind: context-observation
      label: Dummy
      producer: lane:single_lane
      consumer:
        - role:process_owner

lanes:
  - id: single_lane
    label: Single lane
    purpose: Test only.
    authority:
      plane: data_plane
      autonomyTier: draft
      riskTier: low
      allowedActions:
        - draft-artifact
      prohibitedActions:
        - approve-own-work
    skills:
      - test-fixture-skill

gates: []

projectionPolicy:
  canonicalStateSource: repo-local-ledger
  pathPattern: state/**

riskPatterns:
  - patternRef: post-hoc-governance
    mitigations: [N/A]

controlAssessment:
  catalogRefs:
    - gaps/catalogs/v1/controls/nist-ai-rmf.json
  controlImplementations:
    - controlId: BOGUS-1.1
      mappingStatus: planned

freshness:
  reviewedAt: "2026-05-18"
  driftPolicy: Test fixture.

knownGaps: []
```

- [ ] **Step 3: Run the test, confirm it fails**

```bash
python3 -m unittest tests.gaps.v1.test_oscal_refs -v
```

Expected: failure.

- [ ] **Step 4: Implement `oscal_refs.check`**

Replace `scripts/gaps_v1_validator/oscal_refs.py`:

```python
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
            report.add("oscal-refs", f"$.controlAssessment.catalogRefs", f"unable to load {ref}: {error}")
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
```

- [ ] **Step 5: Run the test, confirm it passes**

```bash
python3 -m unittest tests.gaps.v1.test_oscal_refs -v
python3 scripts/validate-gaps-v1.py gaps/examples/v1/minimal/ga-process.v1.yml
```

Expected: tests PASS; minimal fixture still validates (it has empty `controlAssessment`).

- [ ] **Step 6: Commit Task 8**

```bash
git add scripts/gaps_v1_validator/oscal_refs.py tests/gaps/v1/test_oscal_refs.py tests/gaps/v1/fixtures/invalid/oscal_control_not_in_catalog.yml
git commit -m "Add GAPS v1 OSCAL control reference resolution"
```

---

### Task 9: Conformance-level gating

**Files:**
- Modify: `scripts/gaps_v1_validator/conformance.py`
- Create: `tests/gaps/v1/test_conformance.py`
- Create: `tests/gaps/v1/fixtures/invalid/generative_without_state_model.yml`

Rules:

- `descriptive` — no additional requirements beyond schema and cross-references.
- `machine-validatable` — every lane that uses any action must have non-empty `allowedActions` AND `prohibitedActions`; every gate must have non-empty `approvalCondition` and `escalationCondition` text.
- `generative` — every lane must have a `stateModel` with non-empty `states` and `transitions`; every transition must have a `guard`; every blocking gate must have a `decision` block; every `evidenceModel.caseFileItems[]` referenced as `evidenceInputs` must have a `shape.required[]` populated.

The validator's `--level` flag overrides the spec's declared level for testing.

- [ ] **Step 1: Write the failing test**

Create `tests/gaps/v1/test_conformance.py`:

```python
"""Tests for conformance.check."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-gaps-v1.py"
FIXTURES = ROOT / "tests" / "gaps" / "v1" / "fixtures" / "invalid"
MINIMAL = ROOT / "gaps" / "examples" / "v1" / "minimal" / "ga-process.v1.yml"


def run(spec: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(spec), *extra],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ConformanceTests(unittest.TestCase):
    def test_minimal_descriptive_passes(self) -> None:
        result = run(MINIMAL)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_minimal_with_generative_override_fails(self) -> None:
        result = run(MINIMAL, "--level", "generative")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stateModel", result.stderr)

    def test_explicit_generative_without_state_model_fails(self) -> None:
        result = run(FIXTURES / "generative_without_state_model.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("generative", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Write the invalid fixture**

`tests/gaps/v1/fixtures/invalid/generative_without_state_model.yml` — same as minimal but declares `conformanceLevel: generative`:

```yaml
gapsVersion: "1.0.0"
specStatus: draft
conformanceLevel: generative

process:
  id: invalid-generative-no-state-model
  name: Invalid fixture — generative without stateModel
  purpose: Triggers conformance rule.
  scope:
    includes: [test fixture]
    excludes: [any real process]

substrate:
  oscalControlCatalogs:
    - gaps/catalogs/v1/controls/nist-ai-rmf.json
  actionCatalog: gaps/catalogs/v1/actions.yml
  evidenceCatalog: gaps/catalogs/v1/evidence-kinds.yml
  riskPatternCatalog: gaps/catalogs/v1/risk-patterns.yml

roles:
  - id: process_owner
    label: Process owner
    accountabilityScope: Test fixture only.

evidenceModel:
  caseFileItems:
    - id: dummy-evidence
      kind: context-observation
      label: Dummy
      producer: lane:single_lane
      consumer:
        - role:process_owner

lanes:
  - id: single_lane
    label: Single lane
    purpose: Test only.
    authority:
      plane: data_plane
      autonomyTier: draft
      riskTier: low
      allowedActions:
        - draft-artifact
      prohibitedActions:
        - approve-own-work
    skills:
      - test-fixture-skill

gates: []

projectionPolicy:
  canonicalStateSource: repo-local-ledger
  pathPattern: state/**

riskPatterns:
  - patternRef: post-hoc-governance
    mitigations: [N/A]

controlAssessment:
  catalogRefs: []
  controlImplementations: []

freshness:
  reviewedAt: "2026-05-18"
  driftPolicy: Test fixture.

knownGaps: []
```

- [ ] **Step 3: Run the test, confirm it fails**

```bash
python3 -m unittest tests.gaps.v1.test_conformance -v
```

Expected: failure on all three tests since stub.

- [ ] **Step 4: Implement `conformance.check`**

Replace `scripts/gaps_v1_validator/conformance.py`:

```python
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
    case_file_items = {item["id"]: item for item in spec.get("evidenceModel", {}).get("caseFileItems", []) or [] if "id" in item}
    for lane in spec.get("lanes", []) or []:
        lane_id = lane.get("id")
        path = f"$.lanes[id={lane_id}]"
        state_model = lane.get("stateModel") or {}
        states = state_model.get("states") or []
        transitions = state_model.get("transitions") or []
        if not states or not transitions:
            report.add("conformance", f"{path}.stateModel", "generative requires non-empty stateModel.states and stateModel.transitions")
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
```

- [ ] **Step 5: Run the test, confirm it passes**

```bash
python3 -m unittest tests.gaps.v1.test_conformance -v
python3 scripts/validate-gaps-v1.py gaps/examples/v1/minimal/ga-process.v1.yml
python3 scripts/validate-gaps-v1.py gaps/examples/v1/minimal/ga-process.v1.yml --level generative
```

Expected: tests PASS; minimal fixture validates at default (descriptive), fails at `--level generative`.

- [ ] **Step 6: Commit Task 9**

```bash
git add scripts/gaps_v1_validator/conformance.py tests/gaps/v1/test_conformance.py tests/gaps/v1/fixtures/invalid/generative_without_state_model.yml
git commit -m "Add GAPS v1 conformance-level gating"
```

---

### Task 10: Comprehensive positive fixture and end-to-end test

**Files:**
- Create: `gaps/examples/v1/comprehensive/ga-process.v1.yml`
- Create: `tests/gaps/v1/test_end_to_end.py`

The comprehensive fixture exercises every validator check positively. It uses two lanes, multiple gates with decision blocks, a state model with transitions and guards, control-plane actions, an external system with `mutationRequiresApproval`, and one control implementation pointing at a real NIST AI RMF control. Conformance level: `machine-validatable`.

- [ ] **Step 1: Write the comprehensive fixture**

Create `gaps/examples/v1/comprehensive/ga-process.v1.yml`:

```yaml
gapsVersion: "1.0.0"
specStatus: draft
conformanceLevel: machine-validatable

process:
  id: comprehensive-example
  name: Comprehensive GAPS v1 fixture
  purpose: Exercises every Phase 2 validator check positively.
  scope:
    includes:
      - validator integration coverage
    excludes:
      - any real process

substrate:
  oscalControlCatalogs:
    - gaps/catalogs/v1/controls/nist-ai-rmf.json
  actionCatalog: gaps/catalogs/v1/actions.yml
  evidenceCatalog: gaps/catalogs/v1/evidence-kinds.yml
  riskPatternCatalog: gaps/catalogs/v1/risk-patterns.yml

roles:
  - id: operator
    label: Operator
    accountabilityScope: Drafting and verification within the comprehensive fixture.
    decisionRights:
      - draft-artifact
      - run-verification
    canApprove: []
  - id: approver
    label: Approver
    accountabilityScope: Approving the prd_gate and closure_gate.
    decisionRights:
      - approve-gate
      - approve-closure
    canApprove:
      - prd_gate
      - closure_gate

evidenceModel:
  caseFileItems:
    - id: prd-artifact
      kind: artifact-reference
      label: PRD artifact
      shape:
        required: [path, contentHash]
        optional: [author]
      producer: lane:product_lane
      consumer:
        - role:approver
    - id: prd-approval
      kind: approval-attestation
      label: PRD approval
      shape:
        required: [role, actorId, gateId, decision, attestedAt]
      producer: role:approver
      consumer:
        - lane:implementation_lane
    - id: verification-report
      kind: verification-finding
      label: Verification report
      shape:
        required: [reviewer, finding, severity]
      producer: lane:implementation_lane
      consumer:
        - role:approver
    - id: closure-attestation
      kind: approval-attestation
      label: Closure approval
      shape:
        required: [role, actorId, gateId, decision, attestedAt]
      producer: role:approver
      consumer:
        - lane:implementation_lane

lanes:
  - id: product_lane
    label: Product lane
    purpose: Draft and refine the PRD.
    authority:
      plane: data_plane
      autonomyTier: draft
      riskTier: low
      allowedActions:
        - draft-artifact
        - read-repo-evidence
        - record-evidence
      prohibitedActions:
        - approve-own-work
        - approve-gate
    stateModel:
      states:
        - id: product_open
          label: Open
          isInitial: true
        - id: product_ready
          label: Ready for approval
        - id: product_approved
          label: Approved
          isTerminal: true
      transitions:
        - id: t-open-to-ready
          from: product_open
          to: product_ready
          guard:
            inputs: [prd-artifact]
            rules:
              - when: defined(prd-artifact)
                then: allow
            else: block
        - id: t-ready-to-approved
          from: product_ready
          to: product_approved
          gate: prd_gate
          guard:
            inputs: [prd-approval]
            rules:
              - when: defined(prd-approval)
                then: allow
            else: block
    evidenceInputs: []
    evidenceOutputs:
      - prd-artifact
    autonomousResponsibilities:
      - draft-artifact
      - record-evidence
    skills:
      - comprehensive-product

  - id: implementation_lane
    label: Implementation lane
    purpose: Implement and verify approved scope, request closure.
    authority:
      plane: data_plane
      autonomyTier: execute_with_approval
      riskTier: medium
      allowedActions:
        - edit-repository-file-in-boundary
        - run-verification
        - record-evidence
      prohibitedActions:
        - approve-own-work
        - approve-closure
        - close-unverified-work
    stateModel:
      states:
        - id: impl_blocked
          label: Blocked on approval
          isInitial: true
        - id: impl_in_progress
          label: In progress
        - id: impl_verified
          label: Verified
        - id: impl_closed
          label: Closed
          isTerminal: true
      transitions:
        - id: t-blocked-to-in-progress
          from: impl_blocked
          to: impl_in_progress
          guard:
            inputs: [prd-approval]
            rules:
              - when: defined(prd-approval)
                then: allow
            else: block
        - id: t-in-progress-to-verified
          from: impl_in_progress
          to: impl_verified
          guard:
            inputs: [verification-report]
            rules:
              - when: defined(verification-report)
                then: allow
            else: block
        - id: t-verified-to-closed
          from: impl_verified
          to: impl_closed
          gate: closure_gate
          guard:
            inputs: [closure-attestation]
            rules:
              - when: defined(closure-attestation)
                then: allow
            else: block
    evidenceInputs:
      - prd-approval
    evidenceOutputs:
      - verification-report
    autonomousResponsibilities:
      - edit-repository-file-in-boundary
      - run-verification
      - record-evidence
    skills:
      - comprehensive-implementation

gates:
  - id: prd_gate
    label: PRD approval gate
    gateType: blocking
    approvalRole: approver
    approvalCondition: PRD artifact recorded and reviewable.
    escalationCondition: PRD scope, users, or acceptance criteria unclear.
    decision:
      inputs:
        - prd-artifact
      rules:
        - when: defined(prd-artifact)
          then: approve
          effect:
            transitionTo: product_approved
            recordEvidence:
              - prd-approval
        - when: undefined(prd-artifact)
          then: escalate
      else: escalate

  - id: closure_gate
    label: Closure approval gate
    gateType: blocking
    approvalRole: approver
    approvalCondition: Verification report shows no blocking findings.
    escalationCondition: Verification incomplete or findings unaddressed.
    decision:
      inputs:
        - verification-report
      rules:
        - when: defined(verification-report)
          then: approve
          effect:
            transitionTo: impl_closed
            recordEvidence:
              - closure-attestation
        - when: undefined(verification-report)
          then: escalate
      else: escalate

controlPlaneActions:
  - skill: comprehensive-approver
    plane: control_plane
    autonomyTier: human_only
    riskTier: high
    actions:
      - approve-gate
      - approve-closure

projectionPolicy:
  canonicalStateSource: repo-local-ledger
  pathPattern: "gaps/examples/v1/comprehensive/state/**"
  externalSystems:
    - kind: github-issues
      role: collaboration-surface
      mutationRequiresApproval: true

riskPatterns:
  - patternRef: chat-as-control-plane
    mitigations:
      - Canonical state lives in repo-local ledger.
    evidenceRefs:
      - prd-approval
      - closure-attestation
  - patternRef: role-collapse
    mitigations:
      - Operator and approver roles are explicitly separated.
      - approve-own-work appears in prohibitedActions on every lane.

controlAssessment:
  catalogRefs:
    - gaps/catalogs/v1/controls/nist-ai-rmf.json
  controlImplementations:
    - controlId: GOVERN-1.4
      mappingStatus: partial
      implementedBy:
        skills:
          - comprehensive-product
          - comprehensive-implementation
        evidence:
          - prd-approval
          - closure-attestation
      statement: >
        Gate decisions and approvals are recorded as evidence on the
        repo-local ledger, providing transparent traceability of the risk
        management process.

freshness:
  reviewedAt: "2026-05-18"
  driftPolicy: >
    Update this fixture only when the v1 schema or validator semantics
    change. The fixture is the golden positive example for Phase 2.

knownGaps:
  - id: not-yet-generative
    summary: This fixture is at machine-validatable conformance, not generative.
    severity: minor
    plannedResolution: phase-4-generator
```

- [ ] **Step 2: Run the validator against the fixture**

```bash
python3 scripts/validate-gaps-v1.py gaps/examples/v1/comprehensive/ga-process.v1.yml
```

Expected: `GAPS v1 spec validated: gaps/examples/v1/comprehensive/ga-process.v1.yml`. If any issue surfaces, fix the fixture (the validator is the source of truth for Phase 2).

- [ ] **Step 3: Write the end-to-end test**

Create `tests/gaps/v1/test_end_to_end.py`:

```python
"""End-to-end validator coverage on the comprehensive fixture."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-gaps-v1.py"
COMPREHENSIVE = ROOT / "gaps" / "examples" / "v1" / "comprehensive" / "ga-process.v1.yml"


class EndToEndTests(unittest.TestCase):
    def test_comprehensive_fixture_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(COMPREHENSIVE)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_comprehensive_fixture_passes_at_machine_validatable(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(COMPREHENSIVE), "--level", "machine-validatable"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_comprehensive_fixture_fails_at_generative(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(COMPREHENSIVE), "--level", "generative"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        # This fixture is intentionally not generative because evidenceModel
        # case file items used as evidenceInputs do not all have shape.required
        # in a way generative requires across both lanes. Expect failure.
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run the test**

```bash
python3 -m unittest tests.gaps.v1.test_end_to_end -v
```

Expected: all three tests PASS. If the third test passes (i.e., the fixture happens to satisfy generative requirements), adjust the fixture to deliberately keep one generative requirement unmet (e.g., remove `shape.required` from one input case-file item). The goal is a fixture that proves the difference between machine-validatable and generative levels.

- [ ] **Step 5: Run all v1 tests**

```bash
python3 -m unittest discover tests.gaps.v1 -v
```

Expected: every test passes.

- [ ] **Step 6: Run the full repo validation suite**

```bash
./scripts/validate-governed-autonomy.sh
```

Expected: green; final line `All Governed Autonomy validation checks passed.` Note: the comprehensive fixture is added under `gaps/examples/v1/comprehensive/` and is picked up automatically by the loop in `validate-governed-autonomy.sh`.

- [ ] **Step 7: Commit Task 10**

```bash
git add gaps/examples/v1/comprehensive tests/gaps/v1/test_end_to_end.py
git commit -m "Add GAPS v1 comprehensive validator fixture and end-to-end coverage"
```

---

## Self-Review Checklist

- Every Phase 2 rule has at least one negative fixture + test and at least one positive case in the comprehensive fixture.
- The validator never crashes on missing optional blocks (`stateModel`, `decision`, `controlPlaneActions`, etc.); it skips checks that don't apply.
- Cross-references resolved at descriptive level; conformance gating layered on top without rejecting otherwise valid descriptive specs.
- `--level` override allows testing stricter levels without editing the spec.
- v0.1 reference specs continue to validate via the v0.1 path; Phase 2 changes nothing in `scripts/validate-gaps.py`.
- The FEEL subset is intentionally limited; evaluator returns parse trees only — actual condition evaluation is Phase 4/5.

## What Phase 2 does NOT do

- Does not produce skill packages from specs (Phase 4).
- Does not migrate v0.1 specs to v1 (Phase 3).
- Does not validate that the implementation map (Phase 3 artifact) binds correctly to a real skill package (Phase 5 round-trip check).
- Does not evaluate FEEL expressions against runtime evidence (Phase 5 round-trip).

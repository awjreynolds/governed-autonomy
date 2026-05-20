# GADD Contract Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first GADD parity layer: default, self-contained tests that verify the checked-in GADD reference package has the expected command surface and high-risk skill contracts.

**Architecture:** Add a small `tests/gadd_parity` test package with declarative YAML fixtures and focused Python helpers. The tests inspect `reference-packages/gadd` only; they do not execute agents and do not require `/Users/awjre/Work/gadd`. Wire the new tests into `validate-governed-autonomy.sh` after the existing GA lint/enforce tests.

**Tech Stack:** Python `unittest`, standard library `json`/`re`/`pathlib`, existing `scripts.ga_lint.loader.load_yaml` for YAML fixture loading, shell validation script.

---

## File Structure

- Create `tests/gadd_parity/__init__.py`
  - Marks the new parity suite as a test package.
- Create `tests/gadd_parity/fixtures/expected-commands.yml`
  - Declares the 15 `/gadd:*` commands and their expected skill paths.
- Create `tests/gadd_parity/fixtures/required-skill-contracts.yml`
  - Declares high-risk command contracts for `/gadd:next`, `/gadd:approve`, `/gadd:implement`, `/gadd:verify`, and `/gadd:close`.
- Create `tests/gadd_parity/parity.py`
  - Loads manifests, command adapters, skills, frontmatter, sections, and contracts.
  - Returns lists of errors rather than raising early so tests can show all drift.
- Create `tests/gadd_parity/test_contract_parity.py`
  - Unit tests for manifest parity, adapter parity, skill existence/frontmatter/heading checks, and high-risk contract phrases.
- Modify `scripts/validate-governed-autonomy.sh`
  - Adds `python3 -m unittest discover tests/gadd_parity`.

Do not modify `reference-packages/gadd` in this first PR. If parity fails, fix the test contract only when the contract is wrong; otherwise report the drift.

## Task 1: Add Declarative Parity Fixtures

**Files:**
- Create: `tests/gadd_parity/__init__.py`
- Create: `tests/gadd_parity/fixtures/expected-commands.yml`
- Create: `tests/gadd_parity/fixtures/required-skill-contracts.yml`

- [ ] **Step 1: Create the package marker**

Create `tests/gadd_parity/__init__.py` with:

```python
"""GADD parity tests."""
```

- [ ] **Step 2: Add the expected command fixture**

Create `tests/gadd_parity/fixtures/expected-commands.yml` with:

```yaml
commands:
  - command: /gadd:setup
    skill: gadd-setup
    path: skills/gadd-setup
  - command: /gadd:next
    skill: gadd-next
    path: skills/gadd-next
  - command: /gadd:triage
    skill: gadd-triage
    path: skills/gadd-triage
  - command: /gadd:research
    skill: gadd-research
    path: skills/gadd-research
  - command: /gadd:scope
    skill: gadd-scope
    path: skills/gadd-scope
  - command: /gadd:elaborate
    skill: gadd-elaborate
    path: skills/gadd-elaborate
  - command: /gadd:refine
    skill: gadd-refine
    path: skills/gadd-refine
  - command: /gadd:approve
    skill: gadd-approve
    path: skills/gadd-approve
  - command: /gadd:design
    skill: gadd-design
    path: skills/gadd-design
  - command: /gadd:plan
    skill: gadd-plan
    path: skills/gadd-plan
  - command: /gadd:decompose
    skill: gadd-decompose
    path: skills/gadd-decompose
  - command: /gadd:implement
    skill: gadd-implement
    path: skills/gadd-implement
  - command: /gadd:verify
    skill: gadd-verify
    path: skills/gadd-verify
  - command: /gadd:close
    skill: gadd-close
    path: skills/gadd-close
  - command: /gadd:archive
    skill: gadd-archive
    path: skills/gadd-archive
```

- [ ] **Step 3: Add high-risk skill contracts**

Create `tests/gadd_parity/fixtures/required-skill-contracts.yml` with:

```yaml
contracts:
  /gadd:next:
    required_phrases:
      - "/gadd:research"
      - "/gadd:scope"
      - "/gadd:elaborate"
      - "/gadd:refine"
      - "/gadd:design"
      - "/gadd:plan"
      - "/gadd:decompose"
      - "/gadd:implement"
      - "/gadd:verify"
      - "/gadd:close"
      - "/gadd:archive"
      - "next command"
  /gadd:approve:
    required_phrases:
      - "Approve exactly one PRD, SDD, or plan gate"
      - "exactly one approval gate is active"
      - "approved PRD"
      - "approved SDD"
      - "approved plan"
  /gadd:implement:
    required_sections:
      - "Built-in TDD Loop"
    required_phrases:
      - "approved boundary"
      - "Do not close external Work Item projections"
      - "Do not archive Work Items"
      - "documentation impact"
  /gadd:verify:
    required_phrases:
      - "verification.md"
      - "Work Item closure"
      - "human-approved closure"
  /gadd:close:
    required_phrases:
      - "verification.md"
      - "closure.status"
      - "/gadd:archive"
      - "human confirmation"
```

- [ ] **Step 4: Run the targeted discovery command**

Run:

```bash
python3 -m unittest discover tests/gadd_parity
```

Expected: `NO TESTS RAN` with exit code 5. This confirms the new package path exists before helper code and test modules are added.

- [ ] **Step 5: Commit the fixture scaffolding**

```bash
git add tests/gadd_parity
git commit -m "Add GADD parity contract fixtures"
```

## Task 2: Implement Parity Helpers

**Files:**
- Create: `tests/gadd_parity/parity.py`

- [ ] **Step 1: Confirm helpers are absent before implementation**

Run:

```bash
python3 -m unittest discover tests/gadd_parity
```

Expected: `NO TESTS RAN` with exit code 5. Task 3 adds the tests that exercise these helpers.

- [ ] **Step 2: Implement fixture and manifest loading**

Create `tests/gadd_parity/parity.py` with:

```python
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from scripts.ga_lint.loader import load_yaml


FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)


def load_fixture(path: Path) -> dict[str, Any]:
    data = load_yaml(path)
    if not isinstance(data, dict):
        raise AssertionError(f"{path}: fixture must be a mapping")
    return data


def load_manifest(package_root: Path) -> dict[str, Any]:
    path = package_root / "agent-skills.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path}: manifest must be a mapping")
    return data


def manifest_commands(package_root: Path) -> dict[str, dict[str, Any]]:
    manifest = load_manifest(package_root)
    commands = manifest.get("commands")
    if not isinstance(commands, list):
        raise AssertionError(f"{package_root / 'agent-skills.json'}: commands must be a list")
    result: dict[str, dict[str, Any]] = {}
    for item in commands:
        if not isinstance(item, dict):
            continue
        command = item.get("command")
        if isinstance(command, str):
            result[command] = item
    return result
```

- [ ] **Step 3: Implement frontmatter and section helpers**

Append to `tests/gadd_parity/parity.py`:

```python
def skill_path(package_root: Path, manifest_entry: dict[str, Any]) -> Path:
    path_value = manifest_entry.get("path")
    if not isinstance(path_value, str) or not path_value:
        raise AssertionError(f"manifest entry missing path: {manifest_entry}")
    return package_root / path_value / "SKILL.md"


def command_adapter_path(package_root: Path, command: str) -> Path:
    namespace, name = command.removeprefix("/").split(":", 1)
    return package_root / "commands" / namespace / f"{name}.md"


def frontmatter(content: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def section_text(content: str, heading: str) -> str | None:
    lines = content.splitlines()
    heading_line = f"## {heading}"
    start: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == heading_line:
            start = index + 1
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def contains_case_insensitive(content: str, phrase: str) -> bool:
    return phrase.lower() in content.lower()
```

- [ ] **Step 4: Implement contract validators**

Append to `tests/gadd_parity/parity.py`:

```python
def validate_expected_commands(package_root: Path, expected_commands: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    actual = manifest_commands(package_root)
    actual_gadd = {command: entry for command, entry in actual.items() if command.startswith("/gadd:")}
    expected_by_command = {item["command"]: item for item in expected_commands}

    if set(actual_gadd) != set(expected_by_command):
        missing = sorted(set(expected_by_command) - set(actual_gadd))
        extra = sorted(set(actual_gadd) - set(expected_by_command))
        if missing:
            errors.append(f"missing commands: {', '.join(missing)}")
        if extra:
            errors.append(f"extra commands: {', '.join(extra)}")

    for command, expected in expected_by_command.items():
        entry = actual.get(command)
        if entry is None:
            continue
        for key in ("skill", "path"):
            if entry.get(key) != expected[key]:
                errors.append(f"{command}: expected {key}={expected[key]!r}, got {entry.get(key)!r}")
    return errors


def validate_command_adapter(package_root: Path, command: str, entry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    path = command_adapter_path(package_root, command)
    if not path.is_file():
        return [f"{command}: adapter missing at {path}"]
    content = path.read_text(encoding="utf-8")
    skill = str(entry.get("skill") or "")
    skill_path_value = str(entry.get("path") or "")
    if command not in content:
        errors.append(f"{command}: adapter does not mention command")
    if skill and skill not in content:
        errors.append(f"{command}: adapter does not mention skill {skill}")
    if skill_path_value and f"{skill_path_value}/SKILL.md" not in content:
        errors.append(f"{command}: adapter does not mention canonical skill file")
    return errors


def validate_skill_surface(package_root: Path, command: str, entry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    path = skill_path(package_root, entry)
    if not path.is_file():
        return [f"{command}: skill missing at {path}"]
    content = path.read_text(encoding="utf-8")
    data = frontmatter(content)
    expected_name = str(entry.get("skill") or "")
    if data.get("name") != expected_name:
        errors.append(f"{command}: frontmatter name must be {expected_name!r}")
    if f"# {command}" not in content:
        errors.append(f"{command}: skill heading missing")
    return errors


def validate_skill_contract(package_root: Path, command: str, contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    entry = manifest_commands(package_root).get(command)
    if entry is None:
        return [f"{command}: missing from manifest"]
    path = skill_path(package_root, entry)
    if not path.is_file():
        return [f"{command}: skill missing at {path}"]
    content = path.read_text(encoding="utf-8")

    for section in contract.get("required_sections") or []:
        if not isinstance(section, str):
            errors.append(f"{command}: required section must be a string")
            continue
        if section_text(content, section) is None:
            errors.append(f"{command}: missing section {section!r}")

    for phrase in contract.get("required_phrases") or []:
        if not isinstance(phrase, str):
            errors.append(f"{command}: required phrase must be a string")
            continue
        if not contains_case_insensitive(content, phrase):
            errors.append(f"{command}: missing phrase {phrase!r}")

    return errors
```

- [ ] **Step 5: Run helper import check**

Run:

```bash
python3 -m unittest discover tests/gadd_parity
```

Expected: still fail or report zero tests until Task 3 adds tests, but it must not fail because `tests.gadd_parity.parity` cannot import.

- [ ] **Step 6: Commit helper implementation**

```bash
git add tests/gadd_parity/parity.py
git commit -m "Add GADD parity helper checks"
```

## Task 3: Add Default Contract Parity Tests

**Files:**
- Create: `tests/gadd_parity/test_contract_parity.py`

- [ ] **Step 1: Write the parity test module**

Create `tests/gadd_parity/test_contract_parity.py` with:

```python
from __future__ import annotations

import unittest
from pathlib import Path

from tests.gadd_parity.parity import (
    load_fixture,
    manifest_commands,
    validate_command_adapter,
    validate_expected_commands,
    validate_skill_contract,
    validate_skill_surface,
)


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "reference-packages" / "gadd"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class GaddContractParityTests(unittest.TestCase):
    def expected_commands(self) -> list[dict[str, str]]:
        data = load_fixture(FIXTURES / "expected-commands.yml")
        commands = data.get("commands")
        self.assertIsInstance(commands, list)
        return commands

    def contracts(self) -> dict[str, dict]:
        data = load_fixture(FIXTURES / "required-skill-contracts.yml")
        contracts = data.get("contracts")
        self.assertIsInstance(contracts, dict)
        return contracts

    def assert_no_errors(self, errors: list[str]) -> None:
        self.assertEqual([], errors, "\n".join(errors))

    def test_reference_package_has_expected_gadd_command_manifest(self) -> None:
        self.assert_no_errors(validate_expected_commands(PACKAGE_ROOT, self.expected_commands()))

    def test_reference_package_command_adapters_match_manifest(self) -> None:
        commands = manifest_commands(PACKAGE_ROOT)
        errors: list[str] = []
        for item in self.expected_commands():
            command = item["command"]
            errors.extend(validate_command_adapter(PACKAGE_ROOT, command, commands[command]))
        self.assert_no_errors(errors)

    def test_reference_package_skills_match_manifest_surface(self) -> None:
        commands = manifest_commands(PACKAGE_ROOT)
        errors: list[str] = []
        for item in self.expected_commands():
            command = item["command"]
            errors.extend(validate_skill_surface(PACKAGE_ROOT, command, commands[command]))
        self.assert_no_errors(errors)

    def test_high_risk_command_contracts_are_present(self) -> None:
        errors: list[str] = []
        for command, contract in self.contracts().items():
            errors.extend(validate_skill_contract(PACKAGE_ROOT, command, contract))
        self.assert_no_errors(errors)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new tests**

Run:

```bash
python3 -m unittest discover tests/gadd_parity
```

Expected: pass. If this fails on a required phrase, inspect `reference-packages/gadd/skills/<skill>/SKILL.md`. Adjust `required-skill-contracts.yml` only when the phrase is too brittle but the obligation is present under different wording.

- [ ] **Step 3: Run adjacent GADD reference sanity check**

Run:

```bash
python3 -m unittest discover tests/gadd_parity
python3 -m unittest discover tests/ga_lint
python3 -m unittest discover tests/ga_enforce
```

Expected: pass. This verifies the new test suite does not interfere with existing GA lint/enforce tests.

- [ ] **Step 4: Commit the default parity tests**

```bash
git add tests/gadd_parity/test_contract_parity.py tests/gadd_parity/fixtures
git commit -m "Add GADD contract parity tests"
```

## Task 4: Wire Parity Into Governed Autonomy Validation

**Files:**
- Modify: `scripts/validate-governed-autonomy.sh`

- [ ] **Step 1: Inspect the validation script**

Run:

```bash
sed -n '1,120p' scripts/validate-governed-autonomy.sh
```

Expected: see existing `ga-lint` and `ga-enforce` test sections.

- [ ] **Step 2: Add the parity suite after ga-enforce tests**

Modify `scripts/validate-governed-autonomy.sh` so the relevant section reads:

```bash
echo "==> Running ga-lint tests"
python3 -m unittest discover tests/ga_lint -v

echo "==> Running ga-enforce tests"
python3 -m unittest discover tests/ga_enforce -v

echo "==> Running GADD parity tests"
python3 -m unittest discover tests/gadd_parity -v
```

Keep the rest of the script unchanged.

- [ ] **Step 3: Run the validation script**

Run:

```bash
./scripts/validate-governed-autonomy.sh
```

Expected: pass, with a new `==> Running GADD parity tests` section.

- [ ] **Step 4: Commit validation wiring**

```bash
git add scripts/validate-governed-autonomy.sh
git commit -m "Run GADD parity in validation"
```

## Task 5: Final Verification And PR

**Files:**
- No new files.

- [ ] **Step 1: Run focused parity tests**

Run:

```bash
python3 -m unittest discover tests/gadd_parity
```

Expected: all tests pass.

- [ ] **Step 2: Run existing GA test suites**

Run:

```bash
python3 -m unittest discover tests/ga_lint
python3 -m unittest discover tests/ga_enforce
```

Expected: both pass.

- [ ] **Step 3: Run full validation**

Run:

```bash
./scripts/validate-governed-autonomy.sh
```

Expected: `All Governed Autonomy validation checks passed.`

- [ ] **Step 4: Inspect final diff**

Run:

```bash
git status --short
git log --oneline -5
```

Expected: clean working tree after commits, with the three implementation commits visible.

- [ ] **Step 5: Open PR**

Use title:

```text
Add GADD contract parity tests
```

PR body:

```markdown
## Summary
- add self-contained GADD command and skill-contract parity fixtures
- validate the checked-in GADD reference package command adapters, skill frontmatter, headings, and high-risk behavioral obligations
- run the new parity suite from governed-autonomy validation

## Verification
- python3 -m unittest discover tests/gadd_parity
- python3 -m unittest discover tests/ga_lint
- python3 -m unittest discover tests/ga_enforce
- ./scripts/validate-governed-autonomy.sh
```

## Self-Review

- Spec coverage: this plan implements the first PR only from `2026-05-20-gadd-parity-harness-design.md`. Cross-repo verification and structured fixture output parity are intentionally left for separate plans.
- Default CI remains self-contained: all tests inspect `reference-packages/gadd` only.
- No live GitHub checks are introduced.
- No sibling checkout is required.
- Byte-for-byte Markdown equality is not introduced.

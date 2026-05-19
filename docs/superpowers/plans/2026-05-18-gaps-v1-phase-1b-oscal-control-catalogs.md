# GAPS v1.0.0 Phase 1b: OSCAL Control Catalogs

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship three OSCAL control catalogs (NIST AI RMF, ISO/IEC 42001 Annex A, EU AI Act articles) as JSON files generated from compact human-readable YAML sources, plus an OSCAL meta-schema and a builder script. Extend `scripts/validate-catalogs.py` from Phase 1a to validate OSCAL catalogs.

**Architecture:** Sources live at `gaps/catalogs/v1/controls/sources/*.yml` — compact lists of control id + title plus catalog metadata. `scripts/build-oscal-catalogs.py` expands sources to OSCAL Catalog Model JSON with deterministic UUIDv5 ids derived from a stable namespace plus control id. Sources are the canonical edit surface; JSON outputs are regenerated and committed. The builder's `--check` mode detects source-JSON drift in CI. The Phase 1a catalog validator is extended to additionally validate every OSCAL JSON file against the OSCAL meta-schema, assert unique catalog UUIDs, and assert unique control ids per catalog.

**Tech Stack:** Python 3 stdlib, the YAML→JSON bridge from Phase 1a, the JSON Schema subset evaluator from Phase 1a.

---

## File Structure

**New files:**
- `gaps/schema/v1/oscal-catalog.schema.json`
- `gaps/catalogs/v1/controls/sources/nist-ai-rmf.yml`
- `gaps/catalogs/v1/controls/sources/iso-42001-annex-a.yml`
- `gaps/catalogs/v1/controls/sources/eu-ai-act-articles.yml`
- `gaps/catalogs/v1/controls/nist-ai-rmf.json` (generated)
- `gaps/catalogs/v1/controls/iso-42001-annex-a.json` (generated)
- `gaps/catalogs/v1/controls/eu-ai-act-articles.json` (generated)
- `scripts/build-oscal-catalogs.py`
- `tests/gaps/v1/test_build_oscal_catalogs.py`

**Modified files:**
- `scripts/validate-catalogs.py` — add OSCAL validation
- `tests/gaps/v1/test_validate_catalogs.py` — add OSCAL assertions
- `scripts/validate-governed-autonomy.sh` — invoke `build-oscal-catalogs.py --check`
- `gaps/README.md` — extend v1 incubation section

---

### Task 1: OSCAL meta-schema and builder script

**Files:**
- Create: `gaps/schema/v1/oscal-catalog.schema.json`
- Create: `scripts/build-oscal-catalogs.py`

- [ ] **Step 1: Create the OSCAL meta-schema**

Create `gaps/schema/v1/oscal-catalog.schema.json`. This is a strict subset of the NIST OSCAL Catalog Model — sufficient for control reference + structured statement text, intentionally minimal.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/awjreynolds/governed-autonomy/gaps/schema/v1/oscal-catalog.schema.json",
  "title": "GAPS v1 OSCAL Catalog Subset",
  "type": "object",
  "additionalProperties": true,
  "required": ["catalog"],
  "properties": {
    "catalog": {
      "type": "object",
      "additionalProperties": true,
      "required": ["uuid", "metadata", "groups"],
      "properties": {
        "uuid": { "type": "string", "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$" },
        "metadata": {
          "type": "object",
          "additionalProperties": true,
          "required": ["title", "version", "oscal-version"],
          "properties": {
            "title": { "type": "string" },
            "version": { "type": "string" },
            "oscal-version": { "type": "string", "const": "1.1.2" },
            "published": { "type": "string" },
            "last-modified": { "type": "string" }
          }
        },
        "groups": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "object",
            "additionalProperties": true,
            "required": ["id", "title", "controls"],
            "properties": {
              "id": { "type": "string" },
              "title": { "type": "string" },
              "controls": {
                "type": "array",
                "items": {
                  "type": "object",
                  "additionalProperties": true,
                  "required": ["id", "title"],
                  "properties": {
                    "id": { "type": "string" },
                    "title": { "type": "string" },
                    "parts": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": true,
                        "required": ["name", "prose"],
                        "properties": {
                          "name": { "type": "string" },
                          "prose": { "type": "string" }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

- [ ] **Step 2: Write the builder script**

Create `scripts/build-oscal-catalogs.py`:

```python
#!/usr/bin/env python3
"""Expand compact control-source YAML files into OSCAL Catalog Model JSON.

Source files live at `gaps/catalogs/v1/controls/sources/*.yml`.
Outputs live at `gaps/catalogs/v1/controls/*.json`.

Idempotent: re-running produces byte-identical output for unchanged sources
because all UUIDs are derived deterministically via UUIDv5 from a stable
namespace plus control id.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCES_DIR = ROOT / "gaps" / "catalogs" / "v1" / "controls" / "sources"
OUTPUT_DIR = ROOT / "gaps" / "catalogs" / "v1" / "controls"
NAMESPACE_UUID = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
OSCAL_VERSION = "1.1.2"

sys.dont_write_bytecode = True


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
        raise SystemExit(f"failed to load {path}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def stable_uuid(seed: str, key: str) -> str:
    return str(uuid.uuid5(NAMESPACE_UUID, f"{seed}:{key}"))


def build_catalog(source: dict[str, Any]) -> dict[str, Any]:
    seed = source["catalogUuidSeed"]
    catalog_uuid = stable_uuid(seed, "catalog")
    groups: list[dict[str, Any]] = []
    for group in source["groups"]:
        controls = []
        for control in group["controls"]:
            controls.append({
                "id": control["id"],
                "title": control["title"],
            })
        groups.append({
            "id": group["id"],
            "title": group["title"],
            "controls": controls,
        })
    return {
        "catalog": {
            "uuid": catalog_uuid,
            "metadata": {
                "title": source["catalogTitle"],
                "version": source["catalogVersion"],
                "oscal-version": OSCAL_VERSION,
            },
            "groups": groups,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if regenerated JSON differs from committed JSON.",
    )
    args = parser.parse_args()
    sources = sorted(SOURCES_DIR.glob("*.yml"))
    if not sources:
        print("no sources found", file=sys.stderr)
        return 1
    differ = False
    for source_path in sources:
        source = load_yaml(source_path)
        catalog = build_catalog(source)
        output_path = OUTPUT_DIR / (source_path.stem + ".json")
        rendered = json.dumps(catalog, indent=2, sort_keys=False) + "\n"
        if args.check:
            if not output_path.exists():
                print(f"MISSING: {output_path}", file=sys.stderr)
                differ = True
                continue
            if output_path.read_text(encoding="utf-8") != rendered:
                print(f"DIFFER: {output_path}", file=sys.stderr)
                differ = True
            continue
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(f"wrote {output_path}")
    return 1 if differ else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

The builder explicitly does NOT include `last-modified` in metadata. That keeps output deterministic — same input always yields byte-identical JSON. The OSCAL spec allows omitting `last-modified`; the meta-schema in Phase 1a marks it optional.

- [ ] **Step 3: Commit Task 1**

```bash
chmod +x scripts/build-oscal-catalogs.py
git add gaps/schema/v1/oscal-catalog.schema.json scripts/build-oscal-catalogs.py
git commit -m "Add GAPS v1 OSCAL meta-schema and builder script"
```

---

### Task 2: NIST AI RMF source and generated catalog

**Files:**
- Create: `gaps/catalogs/v1/controls/sources/nist-ai-rmf.yml`
- Generate: `gaps/catalogs/v1/controls/nist-ai-rmf.json`

- [ ] **Step 1: Write the NIST AI RMF source**

Each entry maps to one OSCAL control. NIST AI RMF 1.0 organizes guidance into four functions (Govern, Map, Measure, Manage) with categories and subcategories. Subcategory IDs follow NIST's pattern (`GOVERN-1.1`, etc.).

Create `gaps/catalogs/v1/controls/sources/nist-ai-rmf.yml`:

```yaml
catalogTitle: NIST AI Risk Management Framework 1.0
catalogVersion: "1.0"
catalogUuidSeed: nist-ai-rmf
namespace: gaps.governed-autonomy.dev
groups:
  - id: govern
    title: GOVERN
    controls:
      - id: GOVERN-1.1
        title: Legal and regulatory requirements involving AI are understood, managed, and documented.
      - id: GOVERN-1.2
        title: The characteristics of trustworthy AI are integrated into organizational policies, processes, and procedures.
      - id: GOVERN-1.3
        title: Processes, procedures, and practices are in place to determine the needed level of risk management activities based on the organization's risk tolerance.
      - id: GOVERN-1.4
        title: The risk management process and its outcomes are established through transparent policies, procedures, and other controls.
      - id: GOVERN-1.5
        title: Ongoing monitoring and periodic review of the risk management process and its outcomes are planned.
      - id: GOVERN-1.6
        title: Mechanisms are in place to inventory AI systems and are resourced according to organizational risk priorities.
      - id: GOVERN-1.7
        title: Processes and procedures are in place for decommissioning and phasing out AI systems safely.
      - id: GOVERN-2.1
        title: Roles, responsibilities, and lines of communication related to mapping, measuring, and managing AI risks are documented.
      - id: GOVERN-2.2
        title: The organization's personnel and partners receive AI risk management training.
      - id: GOVERN-2.3
        title: Executive leadership is responsible for decisions about risks associated with AI system development and deployment.
      - id: GOVERN-3.1
        title: Decision-making related to mapping, measuring, and managing AI risks throughout the lifecycle is informed by a diverse team.
      - id: GOVERN-3.2
        title: Policies and procedures are in place to define and differentiate roles and responsibilities for human-AI configurations.
      - id: GOVERN-4.1
        title: Organizational policies and practices are in place to foster a critical thinking and safety-first mindset.
      - id: GOVERN-4.2
        title: Organizational teams document the risks and potential impacts of the AI technology they design, develop, deploy, evaluate, or acquire.
      - id: GOVERN-4.3
        title: Organizational practices are in place to enable AI testing, identification of incidents, and information sharing.
      - id: GOVERN-5.1
        title: Organizational policies and practices are in place to collect, consider, prioritize, and integrate feedback.
      - id: GOVERN-5.2
        title: Mechanisms are established to enable AI actors to regularly incorporate adjudicated feedback from relevant stakeholders into system design and implementation.
      - id: GOVERN-6.1
        title: Policies and procedures are in place to address AI risks and benefits arising from third-party software and data.
      - id: GOVERN-6.2
        title: Contingency processes are in place to handle failures or incidents in third-party data or AI systems deemed to be high-risk.
  - id: map
    title: MAP
    controls:
      - id: MAP-1.1
        title: Intended purposes, potentially beneficial uses, context-specific laws, norms and expectations, and prospective settings in which the AI system will be deployed are understood and documented.
      - id: MAP-1.2
        title: Interdisciplinary AI actors, competencies, skills, and capacities for establishing context reflect demographic diversity and broad domain and user experience expertise.
      - id: MAP-1.3
        title: The organization's mission and relevant goals for AI technology are understood and documented.
      - id: MAP-1.4
        title: The business value or context of business use has been clearly defined.
      - id: MAP-1.5
        title: Organizational risk tolerances are determined and documented.
      - id: MAP-1.6
        title: System requirements are elicited from and understood by relevant AI actors.
      - id: MAP-2.1
        title: The specific tasks and methods used to implement the tasks that the AI system will support are defined.
      - id: MAP-2.2
        title: Information about the AI system's knowledge limits and how system output may be utilized and overseen by humans is documented.
      - id: MAP-2.3
        title: Scientific integrity and TEVV considerations are identified and documented.
      - id: MAP-3.1
        title: Potential benefits of intended AI system functionality and performance are examined and documented.
      - id: MAP-3.2
        title: Potential costs of the AI system, including non-monetary costs, are characterized.
      - id: MAP-3.3
        title: Targeted application scope is specified and documented.
      - id: MAP-3.4
        title: Processes for operator and practitioner proficiency with AI system performance and trustworthiness are defined, assessed, and documented.
      - id: MAP-3.5
        title: Processes for human oversight are defined, assessed, and documented.
      - id: MAP-4.1
        title: Approaches for mapping AI technology and legal risks are followed.
      - id: MAP-4.2
        title: Internal risk controls for components of the AI system, including third-party AI technologies, are identified and documented.
      - id: MAP-5.1
        title: Likelihood and magnitude of each identified impact are identified and documented.
      - id: MAP-5.2
        title: Practices and personnel for supporting regular engagement with relevant AI actors and integrating feedback about positive, negative, and unanticipated impacts are in place.
  - id: measure
    title: MEASURE
    controls:
      - id: MEASURE-1.1
        title: Approaches and metrics for measurement of AI risks enumerated during the MAP function are selected for implementation starting with the most significant AI risks.
      - id: MEASURE-1.2
        title: Appropriateness of AI metrics and effectiveness of existing controls is regularly assessed and updated.
      - id: MEASURE-1.3
        title: Internal experts who did not serve as front-line developers for the system and/or independent assessors are involved in regular assessments and updates.
      - id: MEASURE-2.1
        title: Test sets, metrics, and details about the tools used during TEVV are documented.
      - id: MEASURE-2.2
        title: Evaluations involving human subjects meet applicable requirements and are representative of the relevant population.
      - id: MEASURE-2.3
        title: AI system performance or assurance criteria are measured qualitatively or quantitatively and demonstrated for conditions similar to deployment setting(s).
      - id: MEASURE-2.4
        title: The functionality and behavior of the AI system and its components is monitored when in production.
      - id: MEASURE-2.5
        title: The AI system to be deployed is demonstrated to be valid and reliable.
      - id: MEASURE-2.6
        title: The AI system is evaluated regularly for safety risks.
      - id: MEASURE-2.7
        title: AI system security and resilience are evaluated and documented.
      - id: MEASURE-2.8
        title: Risks associated with transparency and accountability are examined and documented.
      - id: MEASURE-2.9
        title: The AI model is explained, validated, and documented.
      - id: MEASURE-2.10
        title: Privacy risk of the AI system is examined and documented.
      - id: MEASURE-2.11
        title: Fairness and bias of the AI system are evaluated and results are documented.
      - id: MEASURE-2.12
        title: Environmental impact and sustainability of AI model training and management activities are assessed.
      - id: MEASURE-2.13
        title: Effectiveness of the employed TEVV metrics and processes is evaluated and documented.
      - id: MEASURE-3.1
        title: Approaches, personnel, and documentation are in place to regularly identify and track existing, unanticipated, and emergent AI risks.
      - id: MEASURE-3.2
        title: Risk tracking approaches are considered for settings where AI risks are difficult to assess.
      - id: MEASURE-3.3
        title: Feedback processes for end users and impacted communities are integrated into system evaluation metrics.
      - id: MEASURE-4.1
        title: Measurement approaches for identifying AI risks are connected to deployment context and informed through consultation with domain experts.
      - id: MEASURE-4.2
        title: Measurement results regarding AI system trustworthiness are informed by input from domain experts and relevant AI actors to validate whether the system is performing consistently.
      - id: MEASURE-4.3
        title: Measurable performance improvements based on consultations with relevant AI actors are identified and documented.
  - id: manage
    title: MANAGE
    controls:
      - id: MANAGE-1.1
        title: A determination is made as to whether the AI system achieves its intended purposes and stated objectives.
      - id: MANAGE-1.2
        title: Treatment of documented AI risks is prioritized based on impact, likelihood, and available resources or methods.
      - id: MANAGE-1.3
        title: Responses to the AI risks deemed high priority are developed, planned, and documented.
      - id: MANAGE-1.4
        title: Negative residual risks to both downstream acquirers of AI systems and end users are documented.
      - id: MANAGE-2.1
        title: Resources required to manage AI risks are taken into account.
      - id: MANAGE-2.2
        title: Mechanisms are in place and applied to sustain the value of deployed AI systems.
      - id: MANAGE-2.3
        title: Procedures are followed to respond to and recover from a previously unknown risk when it is identified.
      - id: MANAGE-2.4
        title: Mechanisms are in place and applied, and responsibilities are assigned to supersede, disengage, or deactivate AI systems that demonstrate performance or outcomes inconsistent with intended use.
      - id: MANAGE-3.1
        title: AI risks and benefits from third-party resources are regularly monitored and risk controls are applied and documented.
      - id: MANAGE-3.2
        title: Pre-trained models which are used for development are monitored as part of AI system regular monitoring and maintenance.
      - id: MANAGE-4.1
        title: Post-deployment AI system monitoring plans are implemented.
      - id: MANAGE-4.2
        title: Measurable continuous improvement activities are integrated into AI system updates and include regular engagement with interested parties.
      - id: MANAGE-4.3
        title: Incidents and errors are communicated to relevant AI actors, including affected communities.
```

- [ ] **Step 2: Generate and verify**

```bash
python3 scripts/build-oscal-catalogs.py
python3 -c "import json; d=json.load(open('gaps/catalogs/v1/controls/nist-ai-rmf.json')); print(d['catalog']['metadata']['title']); print('groups:', [g['id'] for g in d['catalog']['groups']]); print('total controls:', sum(len(g['controls']) for g in d['catalog']['groups']))"
```

Expected:

```
NIST AI Risk Management Framework 1.0
groups: ['govern', 'map', 'measure', 'manage']
total controls: 72
```

- [ ] **Step 3: Commit Task 2**

```bash
git add gaps/catalogs/v1/controls/sources/nist-ai-rmf.yml gaps/catalogs/v1/controls/nist-ai-rmf.json
git commit -m "Add NIST AI RMF OSCAL control catalog"
```

---

### Task 3: ISO/IEC 42001 Annex A source and generated catalog

**Files:**
- Create: `gaps/catalogs/v1/controls/sources/iso-42001-annex-a.yml`
- Generate: `gaps/catalogs/v1/controls/iso-42001-annex-a.json`

- [ ] **Step 1: Write the source**

```yaml
catalogTitle: ISO/IEC 42001 Annex A Controls
catalogVersion: "1.0"
catalogUuidSeed: iso-42001-annex-a
namespace: gaps.governed-autonomy.dev
groups:
  - id: A2-policies
    title: A.2 Policies related to AI
    controls:
      - id: A.2.2
        title: AI policy.
      - id: A.2.3
        title: Alignment with other organizational policies.
      - id: A.2.4
        title: Review of the AI policy.
  - id: A3-internal-organization
    title: A.3 Internal organization
    controls:
      - id: A.3.2
        title: AI roles and responsibilities.
      - id: A.3.3
        title: Reporting of concerns.
  - id: A4-resources
    title: A.4 Resources for AI systems
    controls:
      - id: A.4.2
        title: Resource documentation.
      - id: A.4.3
        title: Data resources.
      - id: A.4.4
        title: Tooling resources.
      - id: A.4.5
        title: System and computing resources.
      - id: A.4.6
        title: Human resources.
  - id: A5-impact-assessment
    title: A.5 Assessing impacts of AI systems
    controls:
      - id: A.5.2
        title: AI system impact assessment process.
      - id: A.5.3
        title: Documentation of AI system impact assessments.
      - id: A.5.4
        title: Assessing AI system impact on individuals or groups of individuals.
      - id: A.5.5
        title: Assessing societal impacts of AI systems.
  - id: A6-system-lifecycle
    title: A.6 AI system life cycle
    controls:
      - id: A.6.1.2
        title: Objectives for responsible development of AI systems.
      - id: A.6.1.3
        title: Processes for responsible AI system design and development.
      - id: A.6.2.2
        title: AI system requirements and specification.
      - id: A.6.2.3
        title: Documentation of AI system design and development.
      - id: A.6.2.4
        title: AI system verification and validation.
      - id: A.6.2.5
        title: AI system deployment.
      - id: A.6.2.6
        title: AI system operation and monitoring.
      - id: A.6.2.7
        title: AI system technical documentation.
      - id: A.6.2.8
        title: AI system event logs.
  - id: A7-data
    title: A.7 Data for AI systems
    controls:
      - id: A.7.2
        title: Data for development and enhancement of AI system.
      - id: A.7.3
        title: Acquisition of data.
      - id: A.7.4
        title: Quality of data for AI systems.
      - id: A.7.5
        title: Data provenance.
      - id: A.7.6
        title: Data preparation.
  - id: A8-information
    title: A.8 Information for interested parties of AI systems
    controls:
      - id: A.8.2
        title: System documentation and information for users.
      - id: A.8.3
        title: External reporting.
      - id: A.8.4
        title: Communication of incidents.
      - id: A.8.5
        title: Information for interested parties.
  - id: A9-ai-use
    title: A.9 Use of AI systems
    controls:
      - id: A.9.2
        title: Processes for responsible use of AI systems.
      - id: A.9.3
        title: Objectives for responsible use of AI systems.
      - id: A.9.4
        title: Intended use of AI systems.
  - id: A10-third-parties
    title: A.10 Third-party and customer relationships
    controls:
      - id: A.10.2
        title: Allocation of responsibilities.
      - id: A.10.3
        title: Suppliers.
      - id: A.10.4
        title: Customers.
```

- [ ] **Step 2: Generate and verify**

```bash
python3 scripts/build-oscal-catalogs.py
python3 -c "import json; d=json.load(open('gaps/catalogs/v1/controls/iso-42001-annex-a.json')); print('total controls:', sum(len(g['controls']) for g in d['catalog']['groups']))"
```

Expected: `total controls: 38`.

- [ ] **Step 3: Commit Task 3**

```bash
git add gaps/catalogs/v1/controls/sources/iso-42001-annex-a.yml gaps/catalogs/v1/controls/iso-42001-annex-a.json
git commit -m "Add ISO/IEC 42001 Annex A OSCAL control catalog"
```

---

### Task 4: EU AI Act articles source and generated catalog

**Files:**
- Create: `gaps/catalogs/v1/controls/sources/eu-ai-act-articles.yml`
- Generate: `gaps/catalogs/v1/controls/eu-ai-act-articles.json`

- [ ] **Step 1: Write the source**

```yaml
catalogTitle: EU AI Act — selected articles for deployer/provider obligations
catalogVersion: "1.0"
catalogUuidSeed: eu-ai-act-articles
namespace: gaps.governed-autonomy.dev
groups:
  - id: high-risk-obligations
    title: Chapter III — High-risk AI systems
    controls:
      - id: Art.9
        title: Risk management system.
      - id: Art.10
        title: Data and data governance.
      - id: Art.11
        title: Technical documentation.
      - id: Art.12
        title: Record-keeping.
      - id: Art.13
        title: Transparency and provision of information to deployers.
      - id: Art.14
        title: Human oversight.
      - id: Art.15
        title: Accuracy, robustness, and cybersecurity.
      - id: Art.16
        title: Obligations of providers of high-risk AI systems.
      - id: Art.17
        title: Quality management system.
      - id: Art.18
        title: Documentation keeping.
      - id: Art.19
        title: Automatically generated logs.
      - id: Art.20
        title: Corrective actions and duty of information.
      - id: Art.26
        title: Obligations of deployers of high-risk AI systems.
      - id: Art.27
        title: Fundamental rights impact assessment for high-risk AI systems.
  - id: transparency
    title: Chapter IV — Transparency obligations
    controls:
      - id: Art.50
        title: Transparency obligations for providers and deployers of certain AI systems.
  - id: gpai
    title: Chapter V — General-purpose AI models
    controls:
      - id: Art.53
        title: Obligations for providers of general-purpose AI models.
      - id: Art.55
        title: Obligations for providers of general-purpose AI models with systemic risk.
  - id: governance
    title: Chapter VII — Governance
    controls:
      - id: Art.66
        title: Tasks of the AI Office.
  - id: post-market
    title: Chapter IX — Post-market monitoring
    controls:
      - id: Art.72
        title: Post-market monitoring by providers.
      - id: Art.73
        title: Reporting of serious incidents.
```

- [ ] **Step 2: Generate and verify**

```bash
python3 scripts/build-oscal-catalogs.py
python3 -c "import json; d=json.load(open('gaps/catalogs/v1/controls/eu-ai-act-articles.json')); print('total controls:', sum(len(g['controls']) for g in d['catalog']['groups']))"
```

Expected: `total controls: 20`.

- [ ] **Step 3: Commit Task 4**

```bash
git add gaps/catalogs/v1/controls/sources/eu-ai-act-articles.yml gaps/catalogs/v1/controls/eu-ai-act-articles.json
git commit -m "Add EU AI Act OSCAL control catalog"
```

---

### Task 5: Builder tests and idempotency check

**Files:**
- Create: `tests/gaps/v1/test_build_oscal_catalogs.py`

- [ ] **Step 1: Write the tests**

Create `tests/gaps/v1/test_build_oscal_catalogs.py`:

```python
"""Tests for scripts/build-oscal-catalogs.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "build-oscal-catalogs.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class BuildOscalCatalogsTests(unittest.TestCase):
    def test_check_mode_passes_for_committed_outputs(self) -> None:
        result = run("--check")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_rebuild_is_byte_identical(self) -> None:
        existing = {
            path.name: path.read_text(encoding="utf-8")
            for path in (ROOT / "gaps" / "catalogs" / "v1" / "controls").glob("*.json")
        }
        self.assertGreater(len(existing), 0, "expected committed OSCAL JSON files")
        result = run()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        for name, prior in existing.items():
            current = (ROOT / "gaps" / "catalogs" / "v1" / "controls" / name).read_text(encoding="utf-8")
            self.assertEqual(prior, current, f"{name} changed on rebuild")

    def test_uuids_are_stable_across_runs(self) -> None:
        first_uuids = {}
        for path in (ROOT / "gaps" / "catalogs" / "v1" / "controls").glob("*.json"):
            first_uuids[path.name] = json.loads(path.read_text(encoding="utf-8"))["catalog"]["uuid"]
        result = run()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        second_uuids = {}
        for path in (ROOT / "gaps" / "catalogs" / "v1" / "controls").glob("*.json"):
            second_uuids[path.name] = json.loads(path.read_text(encoding="utf-8"))["catalog"]["uuid"]
        self.assertEqual(first_uuids, second_uuids)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests**

```bash
python3 -m unittest tests.gaps.v1.test_build_oscal_catalogs -v
```

Expected: all three tests PASS.

- [ ] **Step 3: Commit Task 5**

```bash
git add tests/gaps/v1/test_build_oscal_catalogs.py
git commit -m "Add OSCAL catalog builder tests"
```

---

### Task 6: Extend `validate-catalogs.py` to cover OSCAL

**Files:**
- Modify: `scripts/validate-catalogs.py`
- Modify: `tests/gaps/v1/test_validate_catalogs.py`

The extension adds:

- Load the OSCAL meta-schema.
- For every `*.json` under `gaps/catalogs/v1/controls/`, validate against the OSCAL meta-schema.
- Assert every OSCAL catalog's UUID is unique across the set.
- Assert every control id is unique within its catalog.

- [ ] **Step 1: Add the failing test first**

Append to `tests/gaps/v1/test_validate_catalogs.py`:

```python
class OscalCatalogValidationTests(unittest.TestCase):
    def test_oscal_catalogs_are_validated(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("validated", result.stdout)

    def test_duplicate_control_id_fails(self) -> None:
        catalog_path = ROOT / "gaps" / "catalogs" / "v1" / "controls" / "nist-ai-rmf.json"
        original = catalog_path.read_text(encoding="utf-8")
        broken_payload = json.loads(original)
        first_group = broken_payload["catalog"]["groups"][0]
        # Duplicate the first control id within the first group.
        duplicate = dict(first_group["controls"][0])
        first_group["controls"].append(duplicate)
        catalog_path.write_text(json.dumps(broken_payload, indent=2) + "\n", encoding="utf-8")
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate control id", result.stderr.lower())
        finally:
            catalog_path.write_text(original, encoding="utf-8")
```

- [ ] **Step 2: Run the test, confirm new tests fail**

```bash
python3 -m unittest tests.gaps.v1.test_validate_catalogs -v
```

Expected: existing tests still pass; the new `OscalCatalogValidationTests.test_duplicate_control_id_fails` fails because the validator does not yet check OSCAL files.

- [ ] **Step 3: Extend `scripts/validate-catalogs.py`**

In `scripts/validate-catalogs.py`, change the docstring's "Phase 1a scope" wording to "Validates GAPS-native catalogs and OSCAL control catalogs."

Then add this block at the end of the `validate()` function (after the action-category coverage check):

```python
    oscal_schema_path = schemas_root / "oscal-catalog.schema.json"
    controls_dir = catalogs_root / "controls"
    if oscal_schema_path.exists() and controls_dir.exists():
        oscal_schema = load_json(oscal_schema_path)
        seen_uuids: dict[str, Path] = {}
        for path in sorted(controls_dir.glob("*.json")):
            catalog = load_json(path)
            validate_against_schema(catalog, oscal_schema, str(path))
            catalog_uuid = catalog["catalog"]["uuid"]
            if catalog_uuid in seen_uuids:
                raise ValidationError(
                    f"OSCAL catalog UUID collision: {seen_uuids[catalog_uuid]} and {path}"
                )
            seen_uuids[catalog_uuid] = path

            control_ids_per_catalog: dict[str, str] = {}
            for group in catalog["catalog"]["groups"]:
                for control in group["controls"]:
                    cid = control["id"]
                    if cid in control_ids_per_catalog:
                        raise ValidationError(f"{path}: duplicate control id {cid!r}")
                    control_ids_per_catalog[cid] = group["id"]
```

The `if oscal_schema_path.exists() and controls_dir.exists()` guard means the validator stays compatible with the Phase 1a state (where these did not yet exist). After Phase 1b lands, both paths are present and the block runs.

- [ ] **Step 4: Run the tests, confirm they pass**

```bash
python3 -m unittest tests.gaps.v1.test_validate_catalogs -v
```

Expected: every test passes, including the new OSCAL tests.

- [ ] **Step 5: Smoke-test the validator**

```bash
python3 scripts/validate-catalogs.py
```

Expected: `GAPS v1 catalogs validated`.

- [ ] **Step 6: Commit Task 6**

```bash
git add scripts/validate-catalogs.py tests/gaps/v1/test_validate_catalogs.py
git commit -m "Extend GAPS v1 catalog validator to cover OSCAL catalogs"
```

---

### Task 7: Wire the OSCAL build check into the validation suite

**Files:**
- Modify: `scripts/validate-governed-autonomy.sh`
- Modify: `gaps/README.md`

- [ ] **Step 1: Update `scripts/validate-governed-autonomy.sh`**

Replace the file with:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Validating GAPS v0.1 reference specs"
python3 scripts/retired GAPS v0 validator

echo "==> Validating GAPS v0.1 GADD implementation map"
python3 scripts/retired implementation validator

echo "==> Checking GAPS v1 OSCAL catalogs are up to date with sources"
python3 scripts/build-oscal-catalogs.py --check

echo "==> Validating GAPS v1 catalogs"
python3 scripts/validate-catalogs.py

echo "==> Validating GAPS v1 reference specs"
for spec in gaps/examples/v1/*/ga-process.v1.yml; do
  [ -e "$spec" ] || continue
  python3 scripts/validate-gaps-v1.py "$spec"
done

echo "==> Running test suites"
python3 -m unittest discover tests/gaps -v

echo "All Governed Autonomy validation checks passed."
```

- [ ] **Step 2: Run the suite**

```bash
./scripts/validate-governed-autonomy.sh
```

Expected: every check passes; final line `All Governed Autonomy validation checks passed.`

- [ ] **Step 3: Update `gaps/README.md`**

In the v1 incubation section added in Phase 1a, replace the "OSCAL control catalogs follow in Phase 1b" sentence with:

```markdown
- `gaps/catalogs/v1/controls/` — OSCAL control catalogs (NIST AI RMF,
  ISO/IEC 42001 Annex A, EU AI Act) generated from compact YAML sources
  via `scripts/build-oscal-catalogs.py`.
```

And add this paragraph at the end of the section:

```markdown
OSCAL JSON files are generated from compact YAML sources under
`gaps/catalogs/v1/controls/sources/`. Regenerate after editing a source:

\`\`\`bash
python3 scripts/build-oscal-catalogs.py
\`\`\`

CI runs `python3 scripts/build-oscal-catalogs.py --check` to detect drift
between sources and committed JSON.
```

- [ ] **Step 4: Final commit**

```bash
git add scripts/validate-governed-autonomy.sh gaps/README.md
git commit -m "Wire OSCAL catalog drift check into validation suite"
```

- [ ] **Step 5: Confirm**

```bash
./scripts/validate-governed-autonomy.sh
```

Expected: green; `All Governed Autonomy validation checks passed.`

---

## Self-Review Checklist

- All three OSCAL catalogs build deterministically and are byte-identical on rerun.
- The OSCAL meta-schema is permissive enough to accept the generator's output but strict enough to catch obvious errors.
- The builder's `--check` mode detects drift; CI invokes it.
- Catalog UUIDs are stable across runs (UUIDv5 over a namespace plus catalog seed).
- Catalog validator now runs the OSCAL block when both the OSCAL meta-schema and the controls directory exist; remains compatible with Phase 1a's state where they did not.
- Phase 1a's minimal fixture, which references `gaps/catalogs/v1/controls/nist-ai-rmf.json` in its `substrate.oscalControlCatalogs[]`, now points at a real file. The spec still does not have to validate against OSCAL content; Phase 2 does that.

## What Phase 1b does NOT do

- Does not enforce that a spec's `controlAssessment.controlImplementations[].controlId` resolves to a control in the referenced OSCAL catalog — that lands in Phase 2.
- Does not add OSCAL Profile, Component Definition, or Assessment Results catalogs. Phase 5 may revisit if useful for round-trip; v1.0.0 ships catalog-only OSCAL adoption.
- Does not embed full statement prose (`control.parts[]`) on every control. Sources carry id + title; controls without `parts` validate against the meta-schema (`parts` is optional).
- Does not localize control titles or descriptions to other languages.

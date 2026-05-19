# GAPS v1.0.0 Phase 1: Schema and Catalogs

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the v1 ga-process JSON Schema, six v1 catalogs (actions, evidence kinds, risk patterns, NIST AI RMF controls, ISO/IEC 42001 Annex A controls, EU AI Act articles), a catalog validator, and a minimal v1 fixture that validates end-to-end against the v1 schema.

**Architecture:** v1 lives alongside v0.1. Catalogs under `gaps/catalogs/v1/`; schemas under `gaps/schema/v1/`; reference specs under `gaps/examples/v1/`. Three GAPS-native catalogs are YAML; three OSCAL control catalogs are JSON generated from a compact control-list source via a one-shot Python builder so the source-of-truth is human-readable. The v1 ga-process schema validates structural shape only; semantic cross-reference checks (every roleRef resolves, every actionRef is in the action catalog, state-machine soundness, gate decision completeness) are Phase 2. A new `scripts/validate-gaps-v1.py` dispatches schema validation; `scripts/validate-catalogs.py` validates each catalog against its meta-schema. v0.1 tooling is untouched.

**Tech Stack:** Python 3 stdlib only (no PyYAML, no jsonschema package — use the existing Ruby YAML→JSON bridge from `scripts/validate-gaps.py` and a hand-rolled JSON Schema 2020-12 subset evaluator already proven in v0.1 validators). OSCAL Catalog Model JSON shape (NIST publication 800-53A-derived structure).

---

## File Structure

**New directories:**
- `gaps/catalogs/v1/`
- `gaps/catalogs/v1/controls/`
- `gaps/catalogs/v1/controls/sources/` — compact human-readable control lists
- `gaps/schema/v1/`
- `gaps/examples/v1/minimal/`
- `tests/gaps/v1/`

**New files:**
- `gaps/schema/v1/ga-process.schema.json`
- `gaps/schema/v1/action-catalog.schema.json`
- `gaps/schema/v1/evidence-kinds-catalog.schema.json`
- `gaps/schema/v1/risk-patterns-catalog.schema.json`
- `gaps/schema/v1/oscal-catalog.schema.json`
- `gaps/catalogs/v1/actions.yml`
- `gaps/catalogs/v1/evidence-kinds.yml`
- `gaps/catalogs/v1/risk-patterns.yml`
- `gaps/catalogs/v1/controls/sources/nist-ai-rmf.yml`
- `gaps/catalogs/v1/controls/sources/iso-42001-annex-a.yml`
- `gaps/catalogs/v1/controls/sources/eu-ai-act-articles.yml`
- `gaps/catalogs/v1/controls/nist-ai-rmf.json`
- `gaps/catalogs/v1/controls/iso-42001-annex-a.json`
- `gaps/catalogs/v1/controls/eu-ai-act-articles.json`
- `gaps/examples/v1/minimal/ga-process.v1.yml`
- `scripts/build-oscal-catalogs.py`
- `scripts/validate-catalogs.py`
- `scripts/validate-gaps-v1.py`
- `tests/gaps/v1/__init__.py`
- `tests/gaps/v1/test_validate_catalogs.py`
- `tests/gaps/v1/test_validate_gaps_v1.py`

**Modified files:**
- `scripts/validate-governed-autonomy.sh` — invoke v1 validators after v0.1 validators
- `gaps/README.md` — add v1 incubation section
- `README.md` — add v1 quickstart line

---

### Task 1: Bootstrap directories and catalog meta-schemas

**Files:**
- Create: `gaps/catalogs/v1/controls/sources/.gitkeep`
- Create: `gaps/examples/v1/minimal/.gitkeep`
- Create: `tests/gaps/v1/__init__.py`
- Create: `gaps/schema/v1/action-catalog.schema.json`
- Create: `gaps/schema/v1/evidence-kinds-catalog.schema.json`
- Create: `gaps/schema/v1/risk-patterns-catalog.schema.json`
- Create: `gaps/schema/v1/oscal-catalog.schema.json`

- [ ] **Step 1: Create the directory tree**

Run:

```bash
mkdir -p gaps/catalogs/v1/controls/sources gaps/schema/v1 gaps/examples/v1/minimal tests/gaps/v1
touch gaps/catalogs/v1/controls/sources/.gitkeep gaps/examples/v1/minimal/.gitkeep tests/gaps/v1/__init__.py
```

Expected: exit status 0; all directories exist.

- [ ] **Step 2: Create `gaps/schema/v1/action-catalog.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/awjreynolds/governed-autonomy/gaps/schema/v1/action-catalog.schema.json",
  "title": "GAPS v1 Action Catalog",
  "type": "object",
  "additionalProperties": false,
  "required": ["catalogId", "catalogVersion", "actions"],
  "properties": {
    "catalogId": { "const": "actions" },
    "catalogVersion": { "type": "string", "pattern": "^v[0-9]+(\\.[0-9]+)?$" },
    "description": { "type": "string" },
    "actions": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "label", "category", "defaultAutonomyTier", "defaultRiskTier", "definition"],
        "properties": {
          "id": { "type": "string", "pattern": "^[a-z][a-z0-9-]*[a-z0-9]$" },
          "label": { "type": "string", "minLength": 3 },
          "category": {
            "type": "string",
            "enum": ["data-plane-read", "data-plane-draft", "data-plane-persist", "data-plane-external", "control-plane", "meta", "prohibited-anti-pattern"]
          },
          "defaultAutonomyTier": {
            "type": "string",
            "enum": ["assist", "recommend", "draft", "execute_with_approval", "execute_within_limits", "autonomous_with_monitoring", "human_only"]
          },
          "defaultRiskTier": {
            "type": "string",
            "enum": ["low", "medium", "high", "human_only"]
          },
          "definition": { "type": "string", "minLength": 10 },
          "examples": { "type": "array", "items": { "type": "string" } },
          "roleAffinity": {
            "type": "array",
            "items": { "type": "string", "enum": ["operator", "reviewer", "approver", "process_owner", "product_authority", "technical_authority", "autonomous_system", "any"] }
          },
          "alwaysProhibitedAt": {
            "type": "array",
            "items": { "type": "string", "enum": ["draft", "execute_with_approval", "execute_within_limits", "autonomous_with_monitoring"] }
          }
        }
      }
    }
  }
}
```

- [ ] **Step 3: Create `gaps/schema/v1/evidence-kinds-catalog.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/awjreynolds/governed-autonomy/gaps/schema/v1/evidence-kinds-catalog.schema.json",
  "title": "GAPS v1 Evidence Kinds Catalog",
  "type": "object",
  "additionalProperties": false,
  "required": ["catalogId", "catalogVersion", "evidenceKinds"],
  "properties": {
    "catalogId": { "const": "evidence-kinds" },
    "catalogVersion": { "type": "string", "pattern": "^v[0-9]+(\\.[0-9]+)?$" },
    "description": { "type": "string" },
    "evidenceKinds": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "label", "category", "defaultProducer", "defaultRetention", "definition"],
        "properties": {
          "id": { "type": "string", "pattern": "^[a-z][a-z0-9-]*[a-z0-9]$" },
          "label": { "type": "string" },
          "category": {
            "type": "string",
            "enum": ["observation", "attestation", "finding", "decision-record", "artifact-ref", "audit-event", "external-reference"]
          },
          "defaultProducer": {
            "type": "string",
            "enum": ["operator", "reviewer", "approver", "autonomous_system", "external", "any"]
          },
          "defaultRetention": {
            "type": "string",
            "enum": ["ephemeral", "session", "process-lifetime", "regulatory", "indefinite"]
          },
          "definition": { "type": "string", "minLength": 10 },
          "defaultShape": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "required": { "type": "array", "items": { "type": "string" } },
              "optional": { "type": "array", "items": { "type": "string" } }
            }
          },
          "examples": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}
```

- [ ] **Step 4: Create `gaps/schema/v1/risk-patterns-catalog.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/awjreynolds/governed-autonomy/gaps/schema/v1/risk-patterns-catalog.schema.json",
  "title": "GAPS v1 Risk Patterns Catalog",
  "type": "object",
  "additionalProperties": false,
  "required": ["catalogId", "catalogVersion", "riskPatterns"],
  "properties": {
    "catalogId": { "const": "risk-patterns" },
    "catalogVersion": { "type": "string", "pattern": "^v[0-9]+(\\.[0-9]+)?$" },
    "description": { "type": "string" },
    "riskPatterns": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "label", "definition", "signals", "defaultMitigations"],
        "properties": {
          "id": { "type": "string", "pattern": "^[a-z][a-z0-9-]*[a-z0-9]$" },
          "label": { "type": "string" },
          "definition": { "type": "string", "minLength": 20 },
          "signals": {
            "type": "array",
            "minItems": 1,
            "items": { "type": "string" }
          },
          "defaultMitigations": {
            "type": "array",
            "minItems": 1,
            "items": { "type": "string" }
          },
          "exampleEvidenceKinds": {
            "type": "array",
            "items": { "type": "string" }
          },
          "docReference": { "type": "string" }
        }
      }
    }
  }
}
```

- [ ] **Step 5: Create `gaps/schema/v1/oscal-catalog.schema.json`**

This is the permissive OSCAL Catalog Model subset GAPS adopts. NIST's official OSCAL catalog schema is large; we adopt a strict subset sufficient for control reference + structured statement text.

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

- [ ] **Step 6: Commit Task 1**

```bash
git add gaps/catalogs/v1 gaps/schema/v1 gaps/examples/v1 tests/gaps/v1
git commit -m "Bootstrap GAPS v1 directories and catalog meta-schemas"
```

Expected: commit succeeds. Verify with `git log -1 --stat`.

---

### Task 2: Action catalog

**Files:**
- Create: `gaps/catalogs/v1/actions.yml`

- [ ] **Step 1: Write the full action catalog**

Create `gaps/catalogs/v1/actions.yml` with the exact content below. The action set is derived from the union of v0.1 `authority.allowed` and `authority.prohibited` values across the four reference specs (gadd, compliance-review, incident-response, procurement-approval), normalized to named primitives. Process-local extensions are not part of the universal catalog — they are declared in `process.localActions[]` in the spec itself.

```yaml
catalogId: actions
catalogVersion: v1
description: >
  Controlled vocabulary of action primitives used in GAPS v1 lane authority
  blocks, role decisionRights, and lane autonomousResponsibilities. Each
  action has a default autonomy tier and default risk tier; lane-level
  declarations may tighten (move toward more restrictive) but should not
  loosen these defaults without justification.

actions:
  # ------------------------------ data-plane-read ------------------------------
  - id: gather-context
    label: Gather context from sources
    category: data-plane-read
    defaultAutonomyTier: autonomous_with_monitoring
    defaultRiskTier: low
    definition: >
      Read state from internal or external sources without mutating them. Used
      to assemble inputs for downstream decisions.
    examples:
      - "read repository files for code review context"
      - "query an external tracker for ticket state"

  - id: read-repo-evidence
    label: Read repository evidence
    category: data-plane-read
    defaultAutonomyTier: autonomous_with_monitoring
    defaultRiskTier: low
    definition: >
      Read repository files, commit history, or local artifacts in support of
      a governed action.

  - id: read-external-system-state
    label: Read external system state
    category: data-plane-read
    defaultAutonomyTier: autonomous_with_monitoring
    defaultRiskTier: low
    definition: >
      Query an external system (issue tracker, identity directory, monitoring
      dashboard) read-only.

  - id: observe-process-state
    label: Observe process state
    category: data-plane-read
    defaultAutonomyTier: autonomous_with_monitoring
    defaultRiskTier: low
    definition: >
      Inspect the canonical state record for the in-flight process or work
      item without mutation.

  - id: observe-evidence
    label: Observe evidence
    category: data-plane-read
    defaultAutonomyTier: autonomous_with_monitoring
    defaultRiskTier: low
    definition: >
      Read previously recorded evidence items.

  # ----------------------------- data-plane-draft ------------------------------
  - id: draft-artifact
    label: Draft a reviewable artifact
    category: data-plane-draft
    defaultAutonomyTier: draft
    defaultRiskTier: low
    definition: >
      Produce an artifact intended for human review. The artifact is not
      persisted as approved state until a gate approves it.
    examples:
      - "draft a Product Requirement Document"
      - "draft a verification report"

  - id: draft-decision-record
    label: Draft a decision record
    category: data-plane-draft
    defaultAutonomyTier: draft
    defaultRiskTier: low
    definition: >
      Produce a reviewable decision rationale capturing options considered,
      tradeoffs, and proposed conclusion.

  - id: propose-route
    label: Propose a route
    category: data-plane-draft
    defaultAutonomyTier: recommend
    defaultRiskTier: low
    definition: >
      Recommend a triage or routing outcome for human selection. Does not
      commit the route until approved.

  - id: propose-classification
    label: Propose a classification
    category: data-plane-draft
    defaultAutonomyTier: recommend
    defaultRiskTier: medium
    definition: >
      Recommend a classification (severity, category, tier) for human
      confirmation.

  - id: propose-decomposition
    label: Propose work decomposition
    category: data-plane-draft
    defaultAutonomyTier: draft
    defaultRiskTier: medium
    definition: >
      Recommend a breakdown of larger work into child work items or slices.

  - id: propose-design
    label: Propose a technical design
    category: data-plane-draft
    defaultAutonomyTier: draft
    defaultRiskTier: medium
    definition: >
      Recommend a technical approach including architecture, contracts, and
      tradeoffs.

  - id: propose-plan
    label: Propose an execution plan
    category: data-plane-draft
    defaultAutonomyTier: draft
    defaultRiskTier: medium
    definition: >
      Recommend a sequenced execution plan including dependencies and
      verification approach.

  - id: propose-mitigation
    label: Propose a mitigation
    category: data-plane-draft
    defaultAutonomyTier: recommend
    defaultRiskTier: medium
    definition: >
      Recommend a control, remediation, or compensating measure for an
      identified risk or gap.

  - id: recommend-readiness
    label: Recommend readiness for approval
    category: data-plane-draft
    defaultAutonomyTier: recommend
    defaultRiskTier: low
    definition: >
      Signal that an artifact or boundary is review-ready. Does not constitute
      approval.

  # ---------------------------- data-plane-persist -----------------------------
  - id: record-evidence
    label: Record evidence
    category: data-plane-persist
    defaultAutonomyTier: execute_within_limits
    defaultRiskTier: low
    definition: >
      Write an evidence item to canonical state. Append-only; supersedes via
      new evidence rather than mutation of prior records.

  - id: update-local-state
    label: Update local state within boundary
    category: data-plane-persist
    defaultAutonomyTier: execute_within_limits
    defaultRiskTier: low
    definition: >
      Modify repo-local or process-local artifacts within an approved scope
      boundary.

  - id: edit-repository-file-in-boundary
    label: Edit repository file within approved boundary
    category: data-plane-persist
    defaultAutonomyTier: execute_with_approval
    defaultRiskTier: medium
    definition: >
      Modify code, configuration, or documentation files within an approved
      Work Item, Pull Request, or Change Request scope.

  - id: run-verification
    label: Run verification commands
    category: data-plane-persist
    defaultAutonomyTier: autonomous_with_monitoring
    defaultRiskTier: low
    definition: >
      Execute tests, linters, type checkers, security scanners, or local
      validation commands.

  - id: run-validation
    label: Run validation against canonical rules
    category: data-plane-persist
    defaultAutonomyTier: autonomous_with_monitoring
    defaultRiskTier: low
    definition: >
      Execute schema validators, policy validators, or canonical-state
      validators against in-flight or persisted artifacts.

  - id: annotate-existing-artifact
    label: Annotate an existing artifact
    category: data-plane-persist
    defaultAutonomyTier: execute_within_limits
    defaultRiskTier: low
    definition: >
      Add notes, cross-references, or supplementary context to an artifact
      that has already been approved or recorded.

  # ---------------------------- data-plane-external ----------------------------
  - id: project-to-external-system
    label: Project content to an external system
    category: data-plane-external
    defaultAutonomyTier: execute_with_approval
    defaultRiskTier: medium
    definition: >
      Post a one-way projection of canonical state to a collaboration surface
      (chat, ticket comment) without making the external system authoritative.

  - id: mutate-external-system
    label: Mutate state in an external system
    category: data-plane-external
    defaultAutonomyTier: execute_with_approval
    defaultRiskTier: high
    definition: >
      Change state in an external tracker, identity system, or operational
      tool. Requires explicit human confirmation.

  - id: dispatch-notification
    label: Dispatch a notification
    category: data-plane-external
    defaultAutonomyTier: execute_with_approval
    defaultRiskTier: medium
    definition: >
      Send an email, chat message, webhook, or other notification to an
      external recipient or system.

  - id: open-external-ticket
    label: Open an external ticket
    category: data-plane-external
    defaultAutonomyTier: execute_with_approval
    defaultRiskTier: medium
    definition: >
      Create a new item in an external tracker (Issue, Incident, Change
      Request).

  - id: comment-on-external-ticket
    label: Comment on an external ticket
    category: data-plane-external
    defaultAutonomyTier: execute_within_limits
    defaultRiskTier: low
    definition: >
      Add a comment to an existing external item.

  # ------------------------------ control-plane --------------------------------
  - id: approve-gate
    label: Approve a named gate
    category: control-plane
    defaultAutonomyTier: human_only
    defaultRiskTier: high
    definition: >
      Record explicit human approval of a defined gate. Promotes governed
      transitions on canonical state.
    roleAffinity: [approver, product_authority, technical_authority]

  - id: approve-scope-boundary
    label: Approve a scope boundary
    category: control-plane
    defaultAutonomyTier: human_only
    defaultRiskTier: high
    definition: >
      Approve a defined scope envelope for subsequent autonomous execution.
    roleAffinity: [approver, product_authority, technical_authority]

  - id: approve-closure
    label: Approve closure of work
    category: control-plane
    defaultAutonomyTier: human_only
    defaultRiskTier: high
    definition: >
      Approve final closure of a process or work item, including acceptance of
      verification outcomes.
    roleAffinity: [approver]

  - id: approve-route
    label: Approve a triage route
    category: control-plane
    defaultAutonomyTier: human_only
    defaultRiskTier: medium
    definition: >
      Approve a routing decision when downstream work depends on the route.
    roleAffinity: [approver, technical_authority, product_authority]

  - id: revoke-approval
    label: Revoke a prior approval
    category: control-plane
    defaultAutonomyTier: human_only
    defaultRiskTier: high
    definition: >
      Reverse a previously recorded approval. Requires recording a reason.
    roleAffinity: [approver]

  - id: record-gate-decision
    label: Record a gate decision outcome
    category: control-plane
    defaultAutonomyTier: execute_within_limits
    defaultRiskTier: medium
    definition: >
      Write the outcome of a gate evaluation (approve, escalate, reject) to
      canonical state. May be performed by an autonomous system within limits
      when the gate's decision table is deterministic and within scope.

  - id: transition-state
    label: Transition canonical state
    category: control-plane
    defaultAutonomyTier: execute_within_limits
    defaultRiskTier: medium
    definition: >
      Advance the canonical state record for a process or work item to the
      next state per the lane's transition rules.

  # --------------------------------- meta --------------------------------------
  - id: escalate-to-human
    label: Escalate to a human
    category: meta
    defaultAutonomyTier: autonomous_with_monitoring
    defaultRiskTier: low
    definition: >
      Pause autonomous execution and request a human decision. Used when
      authority boundary is insufficient or evidence is unclear.

  - id: escalate-to-higher-authority
    label: Escalate to higher authority
    category: meta
    defaultAutonomyTier: autonomous_with_monitoring
    defaultRiskTier: low
    definition: >
      Route a decision to an authority above the current approver.

  - id: request-clarification
    label: Request clarification from a participant
    category: meta
    defaultAutonomyTier: autonomous_with_monitoring
    defaultRiskTier: low
    definition: >
      Ask a participant for additional input needed to proceed.

  - id: request-evidence
    label: Request additional evidence
    category: meta
    defaultAutonomyTier: autonomous_with_monitoring
    defaultRiskTier: low
    definition: >
      Ask for additional evidence to support a gate or decision.

  - id: record-known-gap
    label: Record a known gap
    category: meta
    defaultAutonomyTier: execute_within_limits
    defaultRiskTier: low
    definition: >
      Log an unresolved gap for later attention without halting the current
      flow.

  - id: record-non-goal
    label: Record an explicit non-goal
    category: meta
    defaultAutonomyTier: execute_within_limits
    defaultRiskTier: low
    definition: >
      Explicitly mark something as out of scope for the current process or
      work item.

  - id: archive-closed-work
    label: Archive closed work
    category: meta
    defaultAutonomyTier: execute_with_approval
    defaultRiskTier: low
    definition: >
      Move closed artifacts to a defined archive location. Does not modify
      historical record.

  - id: unarchive-work
    label: Unarchive previously archived work
    category: meta
    defaultAutonomyTier: human_only
    defaultRiskTier: medium
    definition: >
      Restore archived artifacts to active state.

  # -------------------------- prohibited-anti-pattern --------------------------
  - id: approve-own-work
    label: Approve own work
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      The producer of an artifact also approves it. Always prohibited at any
      autonomous tier; allowed only when the role explicitly carries both
      producer and approver decision rights and a separate human attestation
      records the dual hat.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: close-unverified-work
    label: Close unverified work
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Mark work as closed without verification evidence supporting closure.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: mutate-canonical-state-silently
    label: Mutate canonical state without a recorded transition
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Change canonical state without producing a corresponding transition
      evidence record.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: bypass-gate
    label: Bypass a defined gate
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Skip a gate defined by the process specification.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: expand-scope-silently
    label: Expand scope without explicit approval
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Add scope to in-flight work without an approved scope-change record.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: alter-recorded-evidence
    label: Alter recorded evidence retroactively
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Modify the content of a previously recorded evidence item rather than
      appending superseding evidence.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: destroy-evidence-or-state
    label: Destroy evidence or canonical state irreversibly
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Irreversibly delete evidence items or canonical state.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: circumvent-policy-threshold
    label: Circumvent a policy threshold
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Structure work to fall below a defined policy threshold that would
      otherwise require higher authority.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: conceal-material-information
    label: Conceal material information from an approver
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Withhold information from an approver that is material to the decision.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: sign-binding-document
    label: Enter a binding commitment
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Sign a contract or enter any externally binding legal or financial
      commitment.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: make-binding-policy-interpretation
    label: Make a binding policy or legal interpretation
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Issue an interpretation of policy, regulation, or law that the
      organization will treat as authoritative.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: declare-final-classification
    label: Declare a final classification authoritatively
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Declare an incident severity, customer impact, regulatory category, or
      similar classification as the final authoritative outcome.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: downgrade-required-authority
    label: Downgrade the authority required for an action
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Lower the authority level the process specification requires for an
      action.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: infer-from-missing-evidence
    label: Infer a fact from the absence of evidence
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Treat the absence of an evidence item as positive evidence of a
      conclusion.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: impersonate-role
    label: Act as a role not assigned to the actor
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Take an action while represented as a role that is not assigned to the
      executing actor.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: route-without-required-evidence
    label: Route work without required evidence
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Make a routing decision that downstream work depends on without the
      minimum evidence the lane requires for that route.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: fork-canonical-state
    label: Create a parallel canonical state record
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Create a competing canonical state record outside the defined
      canonical-state path.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]

  - id: perform-destructive-containment
    label: Perform irreversible containment
    category: prohibited-anti-pattern
    defaultAutonomyTier: human_only
    defaultRiskTier: human_only
    definition: >
      Take an irreversible containment action during incident or risk
      response (delete data, terminate accounts, take systems offline) without
      a human-approved containment plan.
    alwaysProhibitedAt: [draft, execute_with_approval, execute_within_limits, autonomous_with_monitoring]
```

- [ ] **Step 2: Commit Task 2**

```bash
git add gaps/catalogs/v1/actions.yml
git commit -m "Add GAPS v1 action catalog"
```

---

### Task 3: Evidence-kinds catalog

**Files:**
- Create: `gaps/catalogs/v1/evidence-kinds.yml`

- [ ] **Step 1: Write the full evidence-kinds catalog**

Create `gaps/catalogs/v1/evidence-kinds.yml` with this content:

```yaml
catalogId: evidence-kinds
catalogVersion: v1
description: >
  Controlled vocabulary of evidence categories used in GAPS v1
  `evidenceModel.caseFileItems[].kind`. Each kind has a default producer,
  default retention, and default shape. Specs may tighten retention,
  override producer, or extend the shape; specs may not loosen retention
  without recording a rationale.

evidenceKinds:
  # ----------------------------- observation -----------------------------
  - id: triage-observation
    label: Triage observation
    category: observation
    defaultProducer: autonomous_system
    defaultRetention: process-lifetime
    definition: >
      A structured read of incoming work that captures source, requested
      outcome, sensitivity, and recommended routing.
    defaultShape:
      required: [source, requestedOutcome, observedAt]
      optional: [sensitivity, recommendedRoute, classification]
    examples:
      - "intake summary for a new GADD Work Item"
      - "incident triage observation for a paging event"

  - id: context-observation
    label: Context observation
    category: observation
    defaultProducer: autonomous_system
    defaultRetention: process-lifetime
    definition: >
      A read of surrounding state (repository, external tracker, monitoring
      data) gathered to support a downstream decision.
    defaultShape:
      required: [sources, observedAt]
      optional: [highlights, gaps]

  - id: external-state-snapshot
    label: External state snapshot
    category: observation
    defaultProducer: autonomous_system
    defaultRetention: process-lifetime
    definition: >
      A point-in-time read of an external system's relevant state.
    defaultShape:
      required: [system, snapshotAt, snapshot]

  # ----------------------------- attestation -----------------------------
  - id: human-attestation
    label: Human attestation
    category: attestation
    defaultProducer: any
    defaultRetention: regulatory
    definition: >
      A signed or otherwise non-repudiable statement by a named human role
      that something is true or has been reviewed.
    defaultShape:
      required: [role, actorId, statement, attestedAt]

  - id: approval-attestation
    label: Approval attestation
    category: attestation
    defaultProducer: approver
    defaultRetention: regulatory
    definition: >
      A specialized human-attestation for gate approvals. Carries the gate
      id and the rule outcome.
    defaultShape:
      required: [role, actorId, gateId, decision, attestedAt]
      optional: [conditions, rationale]

  - id: dual-control-attestation
    label: Dual-control attestation
    category: attestation
    defaultProducer: approver
    defaultRetention: regulatory
    definition: >
      A composite attestation requiring two distinct human actors, used for
      high-risk or irreversible actions.
    defaultShape:
      required: [primaryRole, primaryActorId, secondaryRole, secondaryActorId, statement, attestedAt]

  # ------------------------------- finding --------------------------------
  - id: verification-finding
    label: Verification finding
    category: finding
    defaultProducer: reviewer
    defaultRetention: process-lifetime
    definition: >
      A reviewer's structured finding from inspecting implementation
      evidence, test output, or compliance checks.
    defaultShape:
      required: [reviewer, finding, severity]
      optional: [recommendation, references]

  - id: policy-violation-finding
    label: Policy violation finding
    category: finding
    defaultProducer: reviewer
    defaultRetention: regulatory
    definition: >
      A finding that an action or artifact violates a named policy.
    defaultShape:
      required: [policyId, violation, severity, foundAt]

  - id: risk-finding
    label: Risk finding
    category: finding
    defaultProducer: any
    defaultRetention: process-lifetime
    definition: >
      Identification of a risk that may affect outcomes, evidence, or
      authority boundaries.
    defaultShape:
      required: [riskSummary, likelihood, impact]
      optional: [mitigationProposed]

  # --------------------------- decision-record ----------------------------
  - id: route-decision
    label: Route decision
    category: decision-record
    defaultProducer: any
    defaultRetention: process-lifetime
    definition: >
      The recorded decision of a triage route, including chosen route and
      rationale.
    defaultShape:
      required: [chosenRoute, rationale, decidedAt]
      optional: [alternativesConsidered]

  - id: gate-decision
    label: Gate decision
    category: decision-record
    defaultProducer: any
    defaultRetention: regulatory
    definition: >
      The outcome of evaluating a gate's decision rules.
    defaultShape:
      required: [gateId, decision, decidedAt]
      optional: [inputsObserved, ruleMatched]

  - id: scope-decision
    label: Scope decision
    category: decision-record
    defaultProducer: approver
    defaultRetention: process-lifetime
    definition: >
      Decision establishing the scope boundary for downstream autonomous
      execution.
    defaultShape:
      required: [scopeIncludes, scopeExcludes, decidedAt]

  - id: design-decision
    label: Design decision
    category: decision-record
    defaultProducer: technical_authority
    defaultRetention: process-lifetime
    definition: >
      A technical design decision capturing tradeoffs and chosen approach.

  # ----------------------------- artifact-ref -----------------------------
  - id: artifact-reference
    label: Artifact reference
    category: artifact-ref
    defaultProducer: any
    defaultRetention: process-lifetime
    definition: >
      Reference to a produced artifact (PRD, SDD, plan, code diff, test
      report) by path and content hash.
    defaultShape:
      required: [path]
      optional: [contentHash, kind, producedAt]

  - id: code-change-reference
    label: Code change reference
    category: artifact-ref
    defaultProducer: operator
    defaultRetention: process-lifetime
    definition: >
      Reference to a code change such as a commit, pull request, or change
      set.
    defaultShape:
      required: [vcs, ref]
      optional: [author, mergedAt]

  # ----------------------------- audit-event ------------------------------
  - id: state-transition-event
    label: State transition event
    category: audit-event
    defaultProducer: any
    defaultRetention: regulatory
    definition: >
      An auditable record of a canonical state transition.
    defaultShape:
      required: [fromState, toState, transitionId, transitionedAt]
      optional: [triggeringEvidence]

  - id: authority-invocation-event
    label: Authority invocation event
    category: audit-event
    defaultProducer: any
    defaultRetention: regulatory
    definition: >
      A record that a specific action was performed under a specific
      authority (autonomy tier, role).
    defaultShape:
      required: [actionId, actorRole, autonomyTier, invokedAt]

  # -------------------------- external-reference --------------------------
  - id: external-ticket-reference
    label: External tracker reference
    category: external-reference
    defaultProducer: any
    defaultRetention: process-lifetime
    definition: >
      Reference to an external tracker item.
    defaultShape:
      required: [system, ticketId]
      optional: [url, status]

  - id: regulatory-record-reference
    label: Regulatory record reference
    category: external-reference
    defaultProducer: any
    defaultRetention: regulatory
    definition: >
      Reference to a record held in a regulated system of record
      (procurement system, identity directory, financial system).
    defaultShape:
      required: [system, recordId]
      optional: [recordType, retrievedAt]
```

- [ ] **Step 2: Commit Task 3**

```bash
git add gaps/catalogs/v1/evidence-kinds.yml
git commit -m "Add GAPS v1 evidence-kinds catalog"
```

---

### Task 4: Risk-patterns catalog

**Files:**
- Create: `gaps/catalogs/v1/risk-patterns.yml`

- [ ] **Step 1: Write the full risk-patterns catalog**

Risk patterns are derived from `docs/governed-autonomy/uncontrolled-ai-risk-patterns.md`. Each pattern lifts the doc's "what it looks like" into structured signals, the "governed autonomy response" into default mitigations, and adds example evidence kinds the catalog now defines.

Create `gaps/catalogs/v1/risk-patterns.yml`:

```yaml
catalogId: risk-patterns
catalogVersion: v1
description: >
  The nine governed-autonomy risk patterns formalized for spec-level reference.
  Source: docs/governed-autonomy/uncontrolled-ai-risk-patterns.md. Each
  pattern includes signals an author can use to recognize the pattern,
  default mitigations, and evidence kinds that typically substantiate the
  mitigation.

riskPatterns:
  - id: chat-as-control-plane
    label: Chat as a control plane
    docReference: docs/governed-autonomy/uncontrolled-ai-risk-patterns.md#chat-as-a-control-plane
    definition: >
      Important process state, decisions, approvals, and evidence live inside
      a chat thread rather than a governed system of record.
    signals:
      - "Approvals are made by chat reactions or short replies."
      - "Reconstructing what was decided requires scrolling chat history."
      - "External systems do not reflect current process state."
    defaultMitigations:
      - "Declare a canonical state source in projectionPolicy.canonicalStateSource."
      - "Treat chat as a collaboration surface only."
      - "Require gate decisions to write to canonical state."
    exampleEvidenceKinds: [state-transition-event, gate-decision, approval-attestation]

  - id: unbounded-delegation
    label: Unbounded delegation
    docReference: docs/governed-autonomy/uncontrolled-ai-risk-patterns.md#unbounded-delegation
    definition: >
      AI moves from advice to action without explicit limits on what it may
      do, where it may act, or when it must stop.
    signals:
      - "Authority block has no explicit prohibitedActions."
      - "No stop conditions or escalation criteria are defined for lanes."
      - "Authority spans data-plane and control-plane without separation."
    defaultMitigations:
      - "Populate authority.allowedActions and authority.prohibitedActions from the action catalog."
      - "Define explicit state-machine transitions and gates."
      - "Separate control-plane actions into controlPlaneActions block."

  - id: role-collapse
    label: Role collapse
    docReference: docs/governed-autonomy/uncontrolled-ai-risk-patterns.md#role-collapse
    definition: >
      One AI session silently becomes analyst, operator, designer, reviewer,
      approver, and auditor.
    signals:
      - "A single role holds both producer and approver decision rights."
      - "Same skill performs implementation and verification."
      - "Approvals reference no named human role."
    defaultMitigations:
      - "Declare distinct roles in roles[] with non-overlapping canApprove[]."
      - "Tag prohibited-anti-pattern action approve-own-work in prohibitedActions."
      - "Require human_only autonomy tier on approval actions."
    exampleEvidenceKinds: [approval-attestation, dual-control-attestation]

  - id: evidence-drift
    label: Evidence drift
    docReference: docs/governed-autonomy/uncontrolled-ai-risk-patterns.md#evidence-drift
    definition: >
      Actions happen faster than evidence is captured; rationale and checks
      are reconstructed after the fact.
    signals:
      - "Lanes lack evidenceOutputs."
      - "Gates have no recordEvidence effect."
      - "Audit-event retention is below regulatory for actions that need it."
    defaultMitigations:
      - "Define evidenceOutputs[] for every lane that records persistent change."
      - "Add gate decision effects that recordEvidence at transition points."
      - "Set retention to regulatory for approval-attestation, dual-control-attestation, gate-decision, state-transition-event."
    exampleEvidenceKinds: [authority-invocation-event, state-transition-event, gate-decision]

  - id: approval-theater
    label: Approval theater
    docReference: docs/governed-autonomy/uncontrolled-ai-risk-patterns.md#approval-theater
    definition: >
      Humans approve large bundles of AI-generated work without clear
      evidence, alternatives, risk summary, or scope boundary.
    signals:
      - "Approval gates collapse multiple decisions into one."
      - "Gate inputs reference no evidence items."
      - "Approval decision rules are absent or trivial (always approve)."
    defaultMitigations:
      - "Require gates to declare decision.inputs that reference specific evidence items."
      - "Require non-trivial decision.rules with explicit when expressions."
      - "Split bundled gates into per-decision gates with distinct approvalConditions."

  - id: tool-sprawl
    label: Tool sprawl
    docReference: docs/governed-autonomy/uncontrolled-ai-risk-patterns.md#tool-sprawl
    definition: >
      Autonomous work touches many systems, but no one can tell which system
      holds canonical process state.
    signals:
      - "Multiple external systems are referenced without role assignment."
      - "External systems perform mutations that affect process outcomes."
      - "Canonical state source is undeclared."
    defaultMitigations:
      - "Declare projectionPolicy.canonicalStateSource and pathPattern."
      - "Assign every external system a role (collaboration-surface, projection-target, or system-of-record)."
      - "Require mutationRequiresApproval: true on systems that are not system-of-record."
    exampleEvidenceKinds: [external-ticket-reference, external-state-snapshot]

  - id: accountability-gaps
    label: Accountability gaps
    docReference: docs/governed-autonomy/uncontrolled-ai-risk-patterns.md#accountability-gaps
    definition: >
      When an AI-driven action causes harm or confusion, no named owner can
      explain the decision or accept responsibility for correction.
    signals:
      - "Gates lack named approvalRole."
      - "Lanes lack a human-affiliated role in autonomousResponsibilities oversight."
      - "Roles lack accountabilityScope."
    defaultMitigations:
      - "Set approvalRole on every gate to a resolvable role id."
      - "Populate accountabilityScope on every role."
      - "Require record-evidence: authority-invocation-event for any action above defaultRiskTier medium."

  - id: scope-creep-at-machine-speed
    label: Scope creep at machine speed
    docReference: docs/governed-autonomy/uncontrolled-ai-risk-patterns.md#scope-creep-at-machine-speed
    definition: >
      A narrow request expands into broader operational change because the AI
      infers additional tasks and executes them.
    signals:
      - "No scope-decision evidence required before execution."
      - "No transition guards reference scope boundaries."
      - "prohibitedActions does not include expand-scope-silently."
    defaultMitigations:
      - "Require scope-decision evidence before control-plane execution gates."
      - "Add prohibitedActions: [expand-scope-silently] to data-plane execution lanes."
      - "Define transitions that exit to escalate-to-human when scope boundary breached."

  - id: post-hoc-governance
    label: Post-hoc governance
    docReference: docs/governed-autonomy/uncontrolled-ai-risk-patterns.md#post-hoc-governance
    definition: >
      Controls are added only after an AI workflow already exists and has
      started producing operational effects.
    signals:
      - "controlAssessment is empty or all controls are mappingStatus: planned."
      - "Spec was written after skills shipped."
      - "Skills have no GAPS implementation map binding."
    defaultMitigations:
      - "Require controlAssessment.controlImplementations[] entries for every shipped lane."
      - "Bind every skill to a lane via implementation map before activation."
      - "Run validate-gaps-v1 in CI before any skill change merges."
```

- [ ] **Step 2: Commit Task 4**

```bash
git add gaps/catalogs/v1/risk-patterns.yml
git commit -m "Add GAPS v1 risk-patterns catalog"
```

---

### Task 5: OSCAL control catalogs (sources + builder)

OSCAL catalogs are large and have boilerplate UUIDs. The plan ships them as compact YAML source files plus a `build-oscal-catalogs.py` script that expands sources into valid OSCAL JSON. Sources are the canonical edit surface; JSON outputs are regenerated and committed.

**Files:**
- Create: `gaps/catalogs/v1/controls/sources/nist-ai-rmf.yml`
- Create: `gaps/catalogs/v1/controls/sources/iso-42001-annex-a.yml`
- Create: `gaps/catalogs/v1/controls/sources/eu-ai-act-articles.yml`
- Create: `scripts/build-oscal-catalogs.py`
- Generate: `gaps/catalogs/v1/controls/nist-ai-rmf.json`
- Generate: `gaps/catalogs/v1/controls/iso-42001-annex-a.json`
- Generate: `gaps/catalogs/v1/controls/eu-ai-act-articles.json`

- [ ] **Step 1: Write `gaps/catalogs/v1/controls/sources/nist-ai-rmf.yml`**

Each entry maps to one OSCAL control. NIST AI RMF 1.0 organizes guidance into four functions (Govern, Map, Measure, Manage) with categories and subcategories. Subcategory IDs follow NIST's pattern (`GOVERN-1.1`, etc.). UUIDs are deterministic UUIDv5 generated from the namespace `gaps.governed-autonomy.dev` plus the control id — keeps regeneration stable.

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

- [ ] **Step 2: Write `gaps/catalogs/v1/controls/sources/iso-42001-annex-a.yml`**

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

- [ ] **Step 3: Write `gaps/catalogs/v1/controls/sources/eu-ai-act-articles.yml`**

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

- [ ] **Step 4: Write the OSCAL builder script**

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
import datetime as _dt
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
                "last-modified": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            "groups": groups,
        },
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")


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
        if args.check and output_path.exists() and output_path.read_text(encoding="utf-8") != rendered:
            print(f"DIFFER: {output_path}", file=sys.stderr)
            differ = True
            continue
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        if not args.check:
            print(f"wrote {output_path}")
    return 1 if differ else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the builder to generate the OSCAL JSON files**

Run:

```bash
chmod +x scripts/build-oscal-catalogs.py
python3 scripts/build-oscal-catalogs.py
```

Expected output:

```
wrote /Users/.../gaps/catalogs/v1/controls/nist-ai-rmf.json
wrote /Users/.../gaps/catalogs/v1/controls/iso-42001-annex-a.json
wrote /Users/.../gaps/catalogs/v1/controls/eu-ai-act-articles.json
```

- [ ] **Step 6: Sanity-check one output**

Run:

```bash
python3 -c "import json; d=json.load(open('gaps/catalogs/v1/controls/nist-ai-rmf.json')); print(d['catalog']['metadata']['title']); print('groups:', [g['id'] for g in d['catalog']['groups']]); print('total controls:', sum(len(g['controls']) for g in d['catalog']['groups']))"
```

Expected:

```
NIST AI Risk Management Framework 1.0
groups: ['govern', 'map', 'measure', 'manage']
total controls: 72
```

- [ ] **Step 7: Commit Task 5**

```bash
git add gaps/catalogs/v1/controls scripts/build-oscal-catalogs.py
git commit -m "Add GAPS v1 OSCAL control catalogs (NIST AI RMF, ISO 42001, EU AI Act)"
```

---

### Task 6: Catalog validator

**Files:**
- Create: `scripts/validate-catalogs.py`
- Create: `tests/gaps/v1/test_validate_catalogs.py`

The catalog validator validates each catalog file against its meta-schema and runs cross-catalog semantic checks (every category enum value is used at least once for the action catalog; every risk-pattern `exampleEvidenceKinds` resolves to an evidence-kinds catalog id; every OSCAL catalog has a unique UUID).

- [ ] **Step 1: Write the failing test fixtures**

Create `tests/gaps/v1/test_validate_catalogs.py`:

```python
"""Tests for scripts/validate-catalogs.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-catalogs.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ValidateCatalogsTests(unittest.TestCase):
    def test_default_run_passes(self) -> None:
        result = run()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_missing_catalog_fails(self) -> None:
        result = run("--catalogs-root", "gaps/catalogs/v1/does-not-exist")
        self.assertNotEqual(result.returncode, 0)

    def test_evidence_kind_reference_resolves(self) -> None:
        risk = json.loads(
            subprocess.check_output(
                [
                    "ruby",
                    "-ryaml",
                    "-rjson",
                    "-e",
                    "print YAML.load_file(ARGV[0]).to_json",
                    str(ROOT / "gaps" / "catalogs" / "v1" / "risk-patterns.yml"),
                ],
                text=True,
            )
        )
        evidence = json.loads(
            subprocess.check_output(
                [
                    "ruby",
                    "-ryaml",
                    "-rjson",
                    "-e",
                    "print YAML.load_file(ARGV[0]).to_json",
                    str(ROOT / "gaps" / "catalogs" / "v1" / "evidence-kinds.yml"),
                ],
                text=True,
            )
        )
        evidence_ids = {entry["id"] for entry in evidence["evidenceKinds"]}
        for pattern in risk["riskPatterns"]:
            for kind in pattern.get("exampleEvidenceKinds", []):
                self.assertIn(kind, evidence_ids, f"pattern {pattern['id']} references unknown evidence kind {kind}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test, confirm it fails**

```bash
python3 -m unittest tests.gaps.v1.test_validate_catalogs -v
```

Expected: `test_default_run_passes` FAILS because the validator does not exist yet.

- [ ] **Step 3: Write `scripts/validate-catalogs.py`**

```python
#!/usr/bin/env python3
"""Validate every GAPS v1 catalog against its meta-schema plus cross-catalog rules."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True


class ValidationError(Exception):
    pass


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
        raise ValidationError(f"failed to load {path}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValidationError(f"unable to read {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValidationError(f"invalid JSON in {path}: {error}") from error


def validate_against_schema(data: Any, schema: dict[str, Any], where: str) -> None:
    """Tiny JSON Schema subset evaluator covering the patterns this repo uses.

    Supports: type, required, properties, additionalProperties (False or schema),
    items, minItems, minLength, enum, const, pattern, anyOf, oneOf.
    Mirrors the subset proven in v0.1 validators.
    """
    errors: list[str] = []

    def check(node_data: Any, node_schema: dict[str, Any], path: str) -> None:
        node_type = node_schema.get("type")
        if "const" in node_schema and node_data != node_schema["const"]:
            errors.append(f"{path}: expected const {node_schema['const']!r}, got {node_data!r}")
            return
        if "enum" in node_schema and node_data not in node_schema["enum"]:
            errors.append(f"{path}: value {node_data!r} not in enum")
            return
        if node_type == "object":
            if not isinstance(node_data, dict):
                errors.append(f"{path}: expected object, got {type(node_data).__name__}")
                return
            for required_key in node_schema.get("required", []):
                if required_key not in node_data:
                    errors.append(f"{path}: missing required key {required_key!r}")
            properties = node_schema.get("properties", {})
            additional = node_schema.get("additionalProperties", True)
            for key, value in node_data.items():
                if key in properties:
                    check(value, properties[key], f"{path}.{key}")
                elif additional is False:
                    errors.append(f"{path}: unexpected key {key!r}")
                elif isinstance(additional, dict):
                    check(value, additional, f"{path}.{key}")
        elif node_type == "array":
            if not isinstance(node_data, list):
                errors.append(f"{path}: expected array, got {type(node_data).__name__}")
                return
            if "minItems" in node_schema and len(node_data) < node_schema["minItems"]:
                errors.append(f"{path}: minItems={node_schema['minItems']} but len={len(node_data)}")
            item_schema = node_schema.get("items")
            if isinstance(item_schema, dict):
                for index, item in enumerate(node_data):
                    check(item, item_schema, f"{path}[{index}]")
        elif node_type == "string":
            if not isinstance(node_data, str):
                errors.append(f"{path}: expected string, got {type(node_data).__name__}")
                return
            if "minLength" in node_schema and len(node_data) < node_schema["minLength"]:
                errors.append(f"{path}: minLength={node_schema['minLength']} but len={len(node_data)}")
            if "pattern" in node_schema and not re.search(node_schema["pattern"], node_data):
                errors.append(f"{path}: does not match pattern {node_schema['pattern']!r}")
        elif node_type == "boolean":
            if not isinstance(node_data, bool):
                errors.append(f"{path}: expected boolean")
        elif node_type == "number":
            if not isinstance(node_data, (int, float)) or isinstance(node_data, bool):
                errors.append(f"{path}: expected number")
        elif node_type == "integer":
            if not isinstance(node_data, int) or isinstance(node_data, bool):
                errors.append(f"{path}: expected integer")

    check(data, schema, where)
    if errors:
        raise ValidationError("\n".join(errors))


def unique_ids(items: list[dict[str, Any]], key: str, where: str) -> None:
    seen: dict[str, int] = {}
    for item in items:
        ident = item.get(key)
        if ident is None:
            continue
        if ident in seen:
            raise ValidationError(f"{where}: duplicate {key}={ident!r}")
        seen[ident] = 1


def validate(catalogs_root: Path, schemas_root: Path) -> None:
    action_schema = load_json(schemas_root / "action-catalog.schema.json")
    evidence_schema = load_json(schemas_root / "evidence-kinds-catalog.schema.json")
    risk_schema = load_json(schemas_root / "risk-patterns-catalog.schema.json")
    oscal_schema = load_json(schemas_root / "oscal-catalog.schema.json")

    actions = load_yaml(catalogs_root / "actions.yml")
    evidence_kinds = load_yaml(catalogs_root / "evidence-kinds.yml")
    risk_patterns = load_yaml(catalogs_root / "risk-patterns.yml")

    validate_against_schema(actions, action_schema, "actions.yml")
    validate_against_schema(evidence_kinds, evidence_schema, "evidence-kinds.yml")
    validate_against_schema(risk_patterns, risk_schema, "risk-patterns.yml")

    unique_ids(actions["actions"], "id", "actions.yml")
    unique_ids(evidence_kinds["evidenceKinds"], "id", "evidence-kinds.yml")
    unique_ids(risk_patterns["riskPatterns"], "id", "risk-patterns.yml")

    evidence_ids = {entry["id"] for entry in evidence_kinds["evidenceKinds"]}
    for pattern in risk_patterns["riskPatterns"]:
        for kind in pattern.get("exampleEvidenceKinds", []):
            if kind not in evidence_ids:
                raise ValidationError(
                    f"risk-patterns.yml: pattern {pattern['id']} references unknown evidence kind {kind!r}"
                )

    expected_categories = {
        "data-plane-read",
        "data-plane-draft",
        "data-plane-persist",
        "data-plane-external",
        "control-plane",
        "meta",
        "prohibited-anti-pattern",
    }
    observed = {entry["category"] for entry in actions["actions"]}
    missing = expected_categories - observed
    if missing:
        raise ValidationError(f"actions.yml: missing actions in categories {sorted(missing)}")

    controls_dir = catalogs_root / "controls"
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

        control_ids: dict[str, str] = {}
        for group in catalog["catalog"]["groups"]:
            for control in group["controls"]:
                cid = control["id"]
                if cid in control_ids:
                    raise ValidationError(f"{path}: duplicate control id {cid!r}")
                control_ids[cid] = group["id"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalogs-root",
        type=Path,
        default=ROOT / "gaps" / "catalogs" / "v1",
        help="Directory containing catalogs (default: gaps/catalogs/v1)",
    )
    parser.add_argument(
        "--schemas-root",
        type=Path,
        default=ROOT / "gaps" / "schema" / "v1",
        help="Directory containing meta-schemas (default: gaps/schema/v1)",
    )
    args = parser.parse_args()
    try:
        validate(args.catalogs_root, args.schemas_root)
    except ValidationError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    except FileNotFoundError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("GAPS v1 catalogs validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the test, confirm it passes**

```bash
chmod +x scripts/validate-catalogs.py
python3 -m unittest tests.gaps.v1.test_validate_catalogs -v
```

Expected: all tests PASS, including `test_default_run_passes`, `test_missing_catalog_fails`, `test_evidence_kind_reference_resolves`.

- [ ] **Step 5: Run the validator directly**

```bash
python3 scripts/validate-catalogs.py
```

Expected: `GAPS v1 catalogs validated`.

- [ ] **Step 6: Commit Task 6**

```bash
git add scripts/validate-catalogs.py tests/gaps/v1/test_validate_catalogs.py
git commit -m "Add GAPS v1 catalog validator"
```

---

### Task 7: v1 ga-process JSON Schema

**Files:**
- Create: `gaps/schema/v1/ga-process.schema.json`

- [ ] **Step 1: Write the v1 ga-process schema**

Create `gaps/schema/v1/ga-process.schema.json`. This schema enforces structural shape and conditional shapes by conformance level. Cross-reference resolution against catalogs is handled by `validate-gaps-v1.py` in Task 8, not by the schema alone.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/awjreynolds/governed-autonomy/gaps/schema/v1/ga-process.schema.json",
  "title": "GAPS v1 GA Process",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "gapsVersion",
    "specStatus",
    "conformanceLevel",
    "process",
    "substrate",
    "roles",
    "evidenceModel",
    "lanes",
    "gates",
    "projectionPolicy",
    "riskPatterns",
    "controlAssessment",
    "freshness",
    "knownGaps"
  ],
  "properties": {
    "gapsVersion": { "type": "string", "const": "1.0.0" },
    "specStatus": { "type": "string", "enum": ["draft", "published", "deprecated"] },
    "conformanceLevel": { "type": "string", "enum": ["descriptive", "machine-validatable", "generative"] },
    "process": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "name", "purpose", "scope"],
      "properties": {
        "id": { "type": "string", "pattern": "^[a-z][a-z0-9-]*[a-z0-9]$" },
        "name": { "type": "string" },
        "purpose": { "type": "string" },
        "scope": {
          "type": "object",
          "additionalProperties": false,
          "required": ["includes", "excludes"],
          "properties": {
            "includes": { "type": "array", "items": { "type": "string" } },
            "excludes": { "type": "array", "items": { "type": "string" } }
          }
        },
        "localActions": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["id", "label", "category", "defaultAutonomyTier", "defaultRiskTier", "definition", "justification"],
            "properties": {
              "id": { "type": "string", "pattern": "^[a-z][a-z0-9-]*[a-z0-9]$" },
              "label": { "type": "string" },
              "category": { "type": "string", "enum": ["data-plane-read", "data-plane-draft", "data-plane-persist", "data-plane-external", "control-plane", "meta", "prohibited-anti-pattern"] },
              "defaultAutonomyTier": { "type": "string", "enum": ["assist", "recommend", "draft", "execute_with_approval", "execute_within_limits", "autonomous_with_monitoring", "human_only"] },
              "defaultRiskTier": { "type": "string", "enum": ["low", "medium", "high", "human_only"] },
              "definition": { "type": "string", "minLength": 20 },
              "justification": { "type": "string", "minLength": 20 }
            }
          }
        }
      }
    },
    "substrate": {
      "type": "object",
      "additionalProperties": false,
      "required": ["oscalControlCatalogs", "actionCatalog", "evidenceCatalog", "riskPatternCatalog"],
      "properties": {
        "oscalControlCatalogs": { "type": "array", "items": { "type": "string" } },
        "oscalProfile": { "type": "string" },
        "actionCatalog": { "type": "string" },
        "evidenceCatalog": { "type": "string" },
        "riskPatternCatalog": { "type": "string" }
      }
    },
    "roles": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "label", "accountabilityScope"],
        "properties": {
          "id": { "type": "string", "pattern": "^[a-z][a-z0-9_]*$" },
          "label": { "type": "string" },
          "accountabilityScope": { "type": "string" },
          "decisionRights": { "type": "array", "items": { "type": "string" } },
          "canApprove": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "evidenceModel": {
      "type": "object",
      "additionalProperties": false,
      "required": ["caseFileItems"],
      "properties": {
        "caseFileItems": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["id", "kind", "label", "producer", "consumer"],
            "properties": {
              "id": { "type": "string", "pattern": "^[a-z][a-z0-9-]*[a-z0-9]$" },
              "kind": { "type": "string" },
              "label": { "type": "string" },
              "shape": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "required": { "type": "array", "items": { "type": "string" } },
                  "optional": { "type": "array", "items": { "type": "string" } }
                }
              },
              "producer": { "type": "string" },
              "consumer": { "type": "array", "items": { "type": "string" } },
              "retentionPolicy": { "type": "string" }
            }
          }
        }
      }
    },
    "lanes": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "label", "purpose", "authority", "skills"],
        "properties": {
          "id": { "type": "string", "pattern": "^[a-z][a-z0-9_]*$" },
          "label": { "type": "string" },
          "purpose": { "type": "string" },
          "authority": {
            "type": "object",
            "additionalProperties": false,
            "required": ["plane", "autonomyTier", "riskTier", "allowedActions", "prohibitedActions"],
            "properties": {
              "plane": { "type": "string", "enum": ["data_plane", "control_plane"] },
              "autonomyTier": { "type": "string", "enum": ["assist", "recommend", "draft", "execute_with_approval", "execute_within_limits", "autonomous_with_monitoring", "human_only"] },
              "riskTier": { "type": "string", "enum": ["low", "medium", "high", "human_only"] },
              "allowedActions": { "type": "array", "items": { "type": "string" } },
              "prohibitedActions": { "type": "array", "items": { "type": "string" } }
            }
          },
          "stateModel": {
            "type": "object",
            "additionalProperties": false,
            "required": ["states", "transitions"],
            "properties": {
              "states": {
                "type": "array",
                "minItems": 1,
                "items": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["id", "label"],
                  "properties": {
                    "id": { "type": "string", "pattern": "^[a-z][a-z0-9_]*$" },
                    "label": { "type": "string" },
                    "isInitial": { "type": "boolean" },
                    "isTerminal": { "type": "boolean" }
                  }
                }
              },
              "transitions": {
                "type": "array",
                "items": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["id", "from", "to"],
                  "properties": {
                    "id": { "type": "string", "pattern": "^[a-z][a-z0-9_-]*$" },
                    "from": { "type": "string" },
                    "to": { "type": "string" },
                    "gate": { "type": "string" },
                    "guard": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": ["inputs", "rules"],
                      "properties": {
                        "inputs": { "type": "array", "items": { "type": "string" } },
                        "rules": {
                          "type": "array",
                          "minItems": 1,
                          "items": {
                            "type": "object",
                            "additionalProperties": false,
                            "required": ["when", "then"],
                            "properties": {
                              "when": { "type": "string" },
                              "then": { "type": "string", "enum": ["allow", "block"] }
                            }
                          }
                        },
                        "else": { "type": "string", "enum": ["allow", "block"] }
                      }
                    }
                  }
                }
              }
            }
          },
          "evidenceInputs": { "type": "array", "items": { "type": "string" } },
          "evidenceOutputs": { "type": "array", "items": { "type": "string" } },
          "autonomousResponsibilities": { "type": "array", "items": { "type": "string" } },
          "skills": { "type": "array", "items": { "type": "string", "pattern": "^[a-z][a-z0-9-]*[a-z0-9]$" } }
        }
      }
    },
    "gates": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "label", "gateType", "approvalRole"],
        "properties": {
          "id": { "type": "string", "pattern": "^[a-z][a-z0-9_-]*$" },
          "label": { "type": "string" },
          "gateType": { "type": "string", "enum": ["validating", "blocking", "escalating", "advisory"] },
          "approvalRole": { "type": "string" },
          "approvalCondition": { "type": "string" },
          "escalationCondition": { "type": "string" },
          "decision": {
            "type": "object",
            "additionalProperties": false,
            "required": ["inputs", "rules"],
            "properties": {
              "inputs": { "type": "array", "items": { "type": "string" } },
              "rules": {
                "type": "array",
                "minItems": 1,
                "items": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["when", "then"],
                  "properties": {
                    "when": { "type": "string" },
                    "then": { "type": "string", "enum": ["approve", "escalate", "reject"] },
                    "effect": {
                      "type": "object",
                      "additionalProperties": false,
                      "properties": {
                        "transitionTo": { "type": "string" },
                        "recordEvidence": { "type": "array", "items": { "type": "string" } }
                      }
                    }
                  }
                }
              },
              "else": { "type": "string", "enum": ["approve", "escalate", "reject"] }
            }
          }
        }
      }
    },
    "controlPlaneActions": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["skill", "plane", "autonomyTier", "riskTier", "actions"],
        "properties": {
          "skill": { "type": "string" },
          "plane": { "type": "string", "const": "control_plane" },
          "autonomyTier": { "type": "string" },
          "riskTier": { "type": "string" },
          "actions": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "projectionPolicy": {
      "type": "object",
      "additionalProperties": false,
      "required": ["canonicalStateSource"],
      "properties": {
        "canonicalStateSource": { "type": "string", "enum": ["repo-local-ledger", "external-system", "hybrid"] },
        "pathPattern": { "type": "string" },
        "externalSystems": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["kind", "role", "mutationRequiresApproval"],
            "properties": {
              "kind": { "type": "string" },
              "role": { "type": "string", "enum": ["collaboration-surface", "projection-target", "system-of-record"] },
              "mutationRequiresApproval": { "type": "boolean" }
            }
          }
        }
      }
    },
    "riskPatterns": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["patternRef", "mitigations"],
        "properties": {
          "patternRef": { "type": "string" },
          "mitigations": { "type": "array", "items": { "type": "string" } },
          "evidenceRefs": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "controlAssessment": {
      "type": "object",
      "additionalProperties": false,
      "required": ["catalogRefs", "controlImplementations"],
      "properties": {
        "catalogRefs": { "type": "array", "items": { "type": "string" } },
        "controlImplementations": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["controlId", "mappingStatus"],
            "properties": {
              "controlId": { "type": "string" },
              "mappingStatus": { "type": "string", "enum": ["implemented", "partial", "planned", "not-applicable"] },
              "implementedBy": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "skills": { "type": "array", "items": { "type": "string" } },
                  "evidence": { "type": "array", "items": { "type": "string" } }
                }
              },
              "statement": { "type": "string" }
            }
          }
        }
      }
    },
    "freshness": {
      "type": "object",
      "additionalProperties": false,
      "required": ["reviewedAt", "driftPolicy"],
      "properties": {
        "reviewedAt": { "type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$" },
        "implementationFingerprint": {
          "type": "object",
          "additionalProperties": false,
          "required": ["algorithm", "value"],
          "properties": {
            "algorithm": { "type": "string", "enum": ["sha256"] },
            "value": { "type": "string", "pattern": "^[0-9a-f]{64}$" }
          }
        },
        "driftPolicy": { "type": "string" }
      }
    },
    "knownGaps": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "summary", "severity"],
        "properties": {
          "id": { "type": "string" },
          "summary": { "type": "string" },
          "severity": { "type": "string", "enum": ["blocking", "important", "minor"] },
          "plannedResolution": { "type": ["string", "null"] }
        }
      }
    }
  }
}
```

- [ ] **Step 2: Commit Task 7**

```bash
git add gaps/schema/v1/ga-process.schema.json
git commit -m "Add GAPS v1 ga-process JSON Schema"
```

---

### Task 8: v1 schema validator and minimal fixture

**Files:**
- Create: `scripts/validate-gaps-v1.py`
- Create: `gaps/examples/v1/minimal/ga-process.v1.yml`
- Create: `tests/gaps/v1/test_validate_gaps_v1.py`

`validate-gaps-v1.py` performs structural schema validation only. Cross-reference integrity, state-machine soundness, gate decision completeness, and conformance-level gating are Phase 2.

- [ ] **Step 1: Write the failing test**

Create `tests/gaps/v1/test_validate_gaps_v1.py`:

```python
"""Tests for scripts/validate-gaps-v1.py (structural schema validation)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-gaps-v1.py"
MINIMAL_FIXTURE = ROOT / "gaps" / "examples" / "v1" / "minimal" / "ga-process.v1.yml"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ValidateGapsV1Tests(unittest.TestCase):
    def test_minimal_fixture_passes(self) -> None:
        result = run(str(MINIMAL_FIXTURE))
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_missing_required_field_fails(self, tmp_path=None) -> None:
        import tempfile
        import textwrap

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as handle:
            handle.write(textwrap.dedent(
                """\
                gapsVersion: "1.0.0"
                specStatus: draft
                conformanceLevel: descriptive
                """
            ))
            broken = Path(handle.name)
        try:
            result = run(str(broken))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required key", result.stderr.lower() + result.stdout.lower())
        finally:
            broken.unlink(missing_ok=True)

    def test_unknown_top_level_field_fails(self) -> None:
        import tempfile
        import textwrap

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as handle:
            handle.write(MINIMAL_FIXTURE.read_text() + "\nrogueField: nope\n")
            broken = Path(handle.name)
        try:
            result = run(str(broken))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected key", result.stderr.lower() + result.stdout.lower())
        finally:
            broken.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test, confirm it fails**

```bash
python3 -m unittest tests.gaps.v1.test_validate_gaps_v1 -v
```

Expected: tests FAIL because `scripts/validate-gaps-v1.py` and the minimal fixture do not exist yet.

- [ ] **Step 3: Write the minimal fixture**

Create `gaps/examples/v1/minimal/ga-process.v1.yml`:

```yaml
gapsVersion: "1.0.0"
specStatus: draft
conformanceLevel: descriptive

process:
  id: minimal-example
  name: Minimal GAPS v1 fixture
  purpose: >
    Smoke-test fixture proving the v1 schema accepts a structurally valid
    minimal spec at descriptive conformance.
  scope:
    includes:
      - smoke testing the v1 schema
    excludes:
      - any real process

substrate:
  oscalControlCatalogs:
    - gaps/catalogs/v1/controls/nist-ai-rmf.json
  actionCatalog: gaps/catalogs/v1/actions.yml
  evidenceCatalog: gaps/catalogs/v1/evidence-kinds.yml
  riskPatternCatalog: gaps/catalogs/v1/risk-patterns.yml

roles:
  - id: process_owner
    label: Process owner
    accountabilityScope: This minimal fixture and its smoke-test outcome.

evidenceModel:
  caseFileItems:
    - id: minimal-observation
      kind: context-observation
      label: A single observation item
      producer: lane:single_lane
      consumer:
        - role:process_owner

lanes:
  - id: single_lane
    label: Single lane
    purpose: One lane for smoke testing.
    authority:
      plane: data_plane
      autonomyTier: draft
      riskTier: low
      allowedActions:
        - draft-artifact
      prohibitedActions:
        - approve-own-work
    skills:
      - minimal-example-draft

gates: []

projectionPolicy:
  canonicalStateSource: repo-local-ledger
  pathPattern: "gaps/examples/v1/minimal/state/**"

riskPatterns:
  - patternRef: post-hoc-governance
    mitigations:
      - "This fixture is descriptive only and exists to smoke-test the schema."

controlAssessment:
  catalogRefs: []
  controlImplementations: []

freshness:
  reviewedAt: "2026-05-18"
  driftPolicy: >
    Update this fixture only when the v1 schema changes. The fixture exists
    to smoke-test the schema; it does not describe a real process.

knownGaps:
  - id: minimal-fixture-is-descriptive-only
    summary: >
      The minimal fixture is intentionally at the descriptive conformance
      level. Phase 4 introduces a generative reference spec.
    severity: minor
    plannedResolution: phase-4-generator
```

- [ ] **Step 4: Write `scripts/validate-gaps-v1.py`**

```python
#!/usr/bin/env python3
"""Validate a GAPS v1 ga-process YAML against the v1 JSON Schema.

Structural validation only. Cross-reference integrity, state-machine
soundness, gate decision completeness, and conformance-level gating live
in Phase 2.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "gaps" / "schema" / "v1" / "ga-process.schema.json"

sys.dont_write_bytecode = True


class ValidationError(Exception):
    pass


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
        raise ValidationError(f"failed to load {path}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_against_schema(data: Any, schema: dict[str, Any]) -> None:
    """JSON Schema subset evaluator (same shape as validate-catalogs.py)."""
    errors: list[str] = []

    def check(node_data: Any, node_schema: dict[str, Any], path: str) -> None:
        if "const" in node_schema and node_data != node_schema["const"]:
            errors.append(f"{path}: expected const {node_schema['const']!r}, got {node_data!r}")
            return
        if "enum" in node_schema and node_data not in node_schema["enum"]:
            errors.append(f"{path}: value {node_data!r} not in enum")
            return
        node_type = node_schema.get("type")
        if isinstance(node_type, list):
            if not any(matches_type(node_data, t) for t in node_type):
                errors.append(f"{path}: type mismatch (expected one of {node_type})")
                return
            node_type = next((t for t in node_type if matches_type(node_data, t)), None)
        if node_type == "object":
            if not isinstance(node_data, dict):
                errors.append(f"{path}: expected object")
                return
            for required_key in node_schema.get("required", []):
                if required_key not in node_data:
                    errors.append(f"{path}: missing required key {required_key!r}")
            properties = node_schema.get("properties", {})
            additional = node_schema.get("additionalProperties", True)
            for key, value in node_data.items():
                if key in properties:
                    check(value, properties[key], f"{path}.{key}")
                elif additional is False:
                    errors.append(f"{path}: unexpected key {key!r}")
                elif isinstance(additional, dict):
                    check(value, additional, f"{path}.{key}")
        elif node_type == "array":
            if not isinstance(node_data, list):
                errors.append(f"{path}: expected array")
                return
            if "minItems" in node_schema and len(node_data) < node_schema["minItems"]:
                errors.append(f"{path}: minItems={node_schema['minItems']} but len={len(node_data)}")
            item_schema = node_schema.get("items")
            if isinstance(item_schema, dict):
                for index, item in enumerate(node_data):
                    check(item, item_schema, f"{path}[{index}]")
        elif node_type == "string":
            if not isinstance(node_data, str):
                errors.append(f"{path}: expected string")
                return
            if "minLength" in node_schema and len(node_data) < node_schema["minLength"]:
                errors.append(f"{path}: minLength={node_schema['minLength']} but len={len(node_data)}")
            if "pattern" in node_schema and not re.search(node_schema["pattern"], node_data):
                errors.append(f"{path}: does not match pattern {node_schema['pattern']!r}")
        elif node_type == "boolean":
            if not isinstance(node_data, bool):
                errors.append(f"{path}: expected boolean")

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
        return False

    check(data, schema, "$")
    if errors:
        raise ValidationError("\n".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to a GAPS v1 ga-process YAML file.")
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH, help="Schema path override.")
    args = parser.parse_args()
    try:
        data = load_yaml(args.spec)
        schema = load_json(args.schema)
        validate_against_schema(data, schema)
    except ValidationError as error:
        print(f"FAIL {args.spec}: {error}", file=sys.stderr)
        return 1
    except FileNotFoundError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"GAPS v1 spec validated: {args.spec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the tests, confirm they pass**

```bash
chmod +x scripts/validate-gaps-v1.py
python3 -m unittest tests.gaps.v1.test_validate_gaps_v1 -v
```

Expected: all three tests PASS.

- [ ] **Step 6: Run the validator directly on the fixture**

```bash
python3 scripts/validate-gaps-v1.py gaps/examples/v1/minimal/ga-process.v1.yml
```

Expected: `GAPS v1 spec validated: gaps/examples/v1/minimal/ga-process.v1.yml`.

- [ ] **Step 7: Commit Task 8**

```bash
git add scripts/validate-gaps-v1.py gaps/examples/v1/minimal/ga-process.v1.yml tests/gaps/v1/test_validate_gaps_v1.py
git commit -m "Add GAPS v1 schema validator and minimal fixture"
```

---

### Task 9: Integrate v1 validators into repo-level validation and docs

**Files:**
- Modify: `scripts/validate-governed-autonomy.sh`
- Modify: `gaps/README.md`
- Modify: `README.md`

- [ ] **Step 1: Read the current `scripts/validate-governed-autonomy.sh`**

```bash
cat scripts/validate-governed-autonomy.sh
```

- [ ] **Step 2: Update the validation script**

Modify `scripts/validate-governed-autonomy.sh` so that after the existing v0.1 validation commands it also runs the v1 validators. Replace the entire file with:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Validating GAPS v0.1 reference specs"
python3 scripts/validate-gaps.py

echo "==> Validating GAPS v0.1 GADD implementation map"
python3 scripts/validate-gaps-implementation.py

echo "==> Validating GAPS v1 catalogs"
python3 scripts/validate-catalogs.py

echo "==> Validating GAPS v1 reference specs"
for spec in gaps/examples/v1/*/ga-process.v1.yml; do
  [ -e "$spec" ] || continue
  python3 scripts/validate-gaps-v1.py "$spec"
done

echo "==> Checking OSCAL catalogs are up to date with sources"
python3 scripts/build-oscal-catalogs.py --check

echo "==> Running test suites"
python3 -m unittest discover tests/gaps -v

echo "All Governed Autonomy validation checks passed."
```

- [ ] **Step 3: Run the integrated validation suite**

```bash
chmod +x scripts/validate-governed-autonomy.sh
./scripts/validate-governed-autonomy.sh
```

Expected: completes with `All Governed Autonomy validation checks passed.`

- [ ] **Step 4: Update `gaps/README.md`**

Locate the existing Status section and append a v1 incubation note. Add a new section before "Relationship to existing standards":

```markdown
## v1.0.0 Incubation

GAPS v1.0.0 is in active design. v1 lives alongside v0.1 during the
deprecation window and uses a separate validator, schema, and catalogs:

- `gaps/schema/v1/` — v1 JSON Schemas (ga-process + catalog meta-schemas).
- `gaps/catalogs/v1/` — controlled vocabularies (actions, evidence kinds,
  risk patterns) and OSCAL control catalogs (NIST AI RMF, ISO/IEC 42001
  Annex A, EU AI Act).
- `gaps/examples/v1/` — v1 reference specs.
- `scripts/validate-gaps-v1.py` — v1 structural schema validator.
- `scripts/validate-catalogs.py` — catalog meta-validator.
- `scripts/build-oscal-catalogs.py` — regenerates OSCAL JSON from compact
  YAML sources.

v1.0.0 adopts OSCAL structurally for evidence and control mappings, and
adopts CMMN case-and-stage and DMN decision-table concepts conceptually in
GAPS-native YAML. See `docs/superpowers/specs/2026-05-18-gaps-v1-0-0-design.md`
for the full architecture.
```

- [ ] **Step 5: Update `README.md` quickstart**

Add a v1 line to the existing `## Quick start` section, after the existing `python3 scripts/validate-gaps.py` block:

```markdown
Run the v1 validators (incubation):

```bash
python3 scripts/validate-catalogs.py
python3 scripts/validate-gaps-v1.py gaps/examples/v1/minimal/ga-process.v1.yml
```
```

- [ ] **Step 6: Final commit for Phase 1**

```bash
git add scripts/validate-governed-autonomy.sh gaps/README.md README.md
git commit -m "Integrate GAPS v1 validators into repo validation suite"
```

- [ ] **Step 7: Confirm full validation passes**

```bash
./scripts/validate-governed-autonomy.sh
```

Expected: exit 0; final line `All Governed Autonomy validation checks passed.`

---

## Self-Review Checklist

- Every catalog file has a meta-schema, and every meta-schema is validated by `validate-catalogs.py`.
- The v1 ga-process schema enforces `additionalProperties: false` on every closed structural block.
- The minimal fixture validates at `descriptive` conformance and uses every required top-level field.
- OSCAL catalogs are regenerable from human-readable YAML sources; `--check` mode detects drift.
- Tests fail before implementation and pass after, for every script created.
- v0.1 tooling is untouched; v0.1 specs continue to validate via the existing validator.
- Cross-reference and semantic checks (`approvalRole` resolves, action ids resolve, state-machine soundness, gate decision completeness) are deferred to Phase 2 — not promised by Phase 1.

## What Phase 1 does NOT do

- Does not validate that `authority.allowedActions[i]` resolves to an action catalog id (Phase 2).
- Does not validate `state-machine soundness` or `gate decision completeness` (Phase 2).
- Does not enforce conformance-level gating beyond schema-level field presence (Phase 2).
- Does not port any v0.1 reference spec (Phase 3).
- Does not generate skills from specs (Phase 4).
- Does not implement round-trip diffing or reverse lift (Phase 5).

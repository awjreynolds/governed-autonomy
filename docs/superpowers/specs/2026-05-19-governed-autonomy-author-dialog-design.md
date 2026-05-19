# Governed Autonomy Author Dialog Design

## Context

GAPS v1.0.0 shipped on 2026-05-19 with five user-facing skills, a 368-line JSON schema requiring 14 top-level fields, a 1,041-line generator, a v0→v1 migrator, three imported OSCAL control catalogs, a reverse-lift, a round-trip verifier, and roughly 6,200 lines of Python tooling. The "minimal" reference fixture is 80 lines and exists only to prove the schema accepts a structurally valid input — its `purpose` explicitly states it is a smoke-test, not a real process.

The job-to-be-done is helping humans design and ship workflow skills that embody governed-autonomy principles: roles and accountability, authority boundaries, input gates, scope, risk and blast radius, evidence, escalation vs approval, state and projection. The current artifact (a hand-authored `ga-process.v1.yml`) is the wrong shape for that job. A passing GAPS spec proves the YAML matches a schema; it does not prove the process is well-governed. Controlled vocabularies (`autonomyTier`: assist|recommend|draft|execute_with_approval|...) imply precision the operating model does not actually define. Conformance levels, OSCAL catalogs, round-trip, and reverse-lift are properties of formalism, not of authoring quality. Almost nobody wakes up wanting to author a GAPS YAML — they want a skill they can trust to run.

This design replaces hand-authored GAPS specs with a dialog-driven authoring flow. The operating model becomes the dialog's question set. The catalogs become conversational content. The GAPS v1 schema is demoted to internal plumbing for an opt-in `--emit-spec` flag. Most of the v1 tooling — generator, migrator, lift, round-trip, v0 surfaces — is decommissioned.

The design target: a practitioner walks an interrogative dialog grounded in the operating model, the dialog refuses to proceed when core governance facts are absent or not load-bearing, and the dialog emits a coordinated skill set plus a single process-level `governance.yml`. Authoring rigor falls out of the grill-me stance and the dialog's question set, not out of schema validation.

## Decisions

1. **One author skill, one critique skill, one lint command** — the entire user-facing surface. Revision is authoring with prefilled answers, not a separate skill.
2. **Dialog generates skills directly** — no template engine, no deterministic renderer. The LLM writes `SKILL.md` and `governance.yml`.
3. **Process → set of skills + one governance.yml** — a non-trivial process produces N × `SKILL.md` (one per discrete agent-executable step) plus one process-level sidecar. Trivial processes collapse to N=1.
4. **Branching dialog, one skill** — the author skill detects input mode (cold start / notes / retrofit / revision) and routes to the appropriate branch. Modes converge on a shared emit phase.
5. **Hard refuse on a small core set** — missing accountability, missing allowed/prohibited actions, missing evidence destination, missing escalation. Everything else produces warnings.
6. **Catalogs feed the dialog as suggestions and hints** — both catalog ids and novel local entries are valid in `governance.yml`. Vocabulary is not enforced.
7. **Grill-me stance, default-on** — every phase is a small loop (ask → probe → cross-check → accept). `--quick` flag escapes probing for revision and trivial processes.
8. **Quality refusal in addition to mechanical refusal** — a populated field that doesn't survive probing fails the same as an empty field. Quality refusal blocks emit only when the contradiction touches a core field; non-core contradictions are recorded and proceed.
9. **Help-and-research integration** — when the user is stuck, the dialog offers brainstorm-style options, local research (read repo / docs), or external research via whatever web search the host agent has available (provider-agnostic). User can always type the answer to skip the offer.
10. **Investigation/research as a first-class step type** — `step_kind: investigate` is recognised; investigation steps are read-only by definition and feed a downstream decision step.
11. **GAPS v1 schema is internal** — kept for `--emit-spec` users (audit / compliance use case). Hand-authoring GAPS YAML stops being the supported authoring path.

## Architecture

```
User-facing
├── governed-autonomy:author    LLM dialog, branches on input mode, writes files
├── governed-autonomy:critique  LLM read-only review, writes findings
└── ga-lint                     deterministic CLI, no LLM, exits non-zero on errors

Internal content (conversational material, not enforced)
├── docs/governed-autonomy/operating-model.md         9 concerns drive dialog phases
├── gaps/catalogs/v1/actions.yml                      action suggestions
├── gaps/catalogs/v1/evidence-kinds.yml               evidence suggestions
└── gaps/catalogs/v1/risk-patterns.yml                risk-pattern suggestions

Internal plumbing (used only on --emit-spec)
├── gaps/schema/v1/                                   schema kept as reference
├── scripts/gaps_v1_validator/                        validator package, internal use only
└── scripts/validate-gaps-v1.py                       CLI, internal use only
```

## Output artifacts

A process lives in its own directory:

```
<process-id>/
├── governance.yml              process-level governance (single source of truth)
├── governance-validation.md    synthesis: what was asked, probed, researched
├── skills/
│   ├── <step-id>/SKILL.md
│   └── ...
└── commands/                   optional, only if process has an orchestrator
    └── <process-id>.md
```

### governance.yml

Target ~50 lines for typical processes. Sketch:

```yaml
governanceVersion: "1"
process:
  id: sdlc-feature-delivery
  name: SDLC feature delivery
  purpose: One sentence.
  scope:
    includes: [...]
    excludes: [...]

roles:
  - id: tech_lead
    label: Tech lead
    accountable_for: Merge decisions and release readiness.
  - id: agent
    label: Coding agent
    autonomous: true
    accountable_for: nothing

authority:
  default_autonomy_tier: draft
  default_allowed_actions:
    - catalog:action:draft-artifact
    - catalog:action:run-verification
    - local:open-pr
  prohibited_actions:
    - catalog:action:approve-own-work
    - catalog:action:expand-scope-silently
    - local:merge-to-main

local_definitions:
  open-pr:
    definition: Open a pull request against the integration branch with the drafted change set.
    category: data-plane-external
  merge-to-main:
    definition: Push or merge any commit onto the main branch directly without an approved gate.
    category: data-plane-persist

input_gates:
  - A linked spec or ticket exists.
  - Acceptance criteria are stated.

risk:
  patterns:
    - catalog:risk:post-hoc-governance
    - catalog:risk:scope-creep-at-machine-speed
  blast_radius: production-code

evidence:
  destination: repo
  items:
    - id: design-record
      kind: catalog:evidence:design-decision
      producer: step:design
      consumer: [role:tech_lead]
    - id: verification-record
      kind: catalog:evidence:verification-finding
      producer: step:implement
      consumer: [role:tech_lead]

gates:
  - id: pre-merge
    requires_role: role:tech_lead
    requires_evidence: [evidence:design-record, evidence:verification-record]
    blocks_steps: [step:merge]

escalation:
  - condition: scope-change-detected
    to: role:tech_lead
  - condition: verification-fails-after-3-retries
    to: role:tech_lead

state:
  canonical: repo
  projections: [linear, slack]

freshness:
  reviewed_at: "2026-05-19"
  drift_policy: Review every 6 months or when authority changes.

steps:
  - id: design
    label: Design
    purpose: Produce a design record describing the change and its reversibility.
    step_kind: execute
    requires_role: role:agent
  - id: investigate-risk
    label: Investigate risk
    purpose: Read code paths and external dependencies to identify reversibility constraints.
    step_kind: investigate
    requires_role: role:agent
    authority_overrides:
      allowed_actions:
        - catalog:action:gather-context
        - catalog:action:read-repo-evidence
        - catalog:action:read-external-system-state
  - id: implement
    label: Implement
    purpose: Draft the code change and run verification.
    step_kind: execute
    requires_role: role:agent
  - id: merge
    label: Merge
    purpose: Merge to integration branch after pre-merge gate passes.
    step_kind: approve
    requires_role: role:tech_lead
    authority_overrides:
      autonomy_tier: human_only

warnings: []
knownGaps: []
```

Conventions:

- **Namespaced refs everywhere** — `catalog:…`, `local:…`, `role:…`, `step:…`, `lane:…`, `evidence:…`. Every internal reference uses a prefix. No bare ids inside the file.
- **`local_definitions` is top-level and structured** — `local:` refs may appear anywhere in the file (actions, evidence, escalation conditions). Every `local:` ref must have an entry in the top-level `local_definitions` map with two fields: `definition` (string, ≥20 chars) and `category` (string, the catalog action category vocabulary: `data-plane-read | data-plane-draft | data-plane-persist | data-plane-external | control-plane | meta | prohibited-anti-pattern`). The category is required because `E011` cannot decide read-vs-write semantics from prose alone.
- **`step_kind` enum** — `steps[*].step_kind` is one of: `execute` (produces a work product), `investigate` (read-only, produces findings), `decide` (routes or classifies), `approve` (human gates a transition), `monitor` (ongoing observation). The enum is closed; lint rejects values outside it.
- **`steps[*].requires_role` is required** — every step names the role responsible for executing it. For agent-executable steps, this is the autonomous agent role (`role:agent`). For human steps, a human role. This field makes ownership deterministic and powers `W009`.
- **`default_allowed_actions` (process level) vs `allowed_actions` (step level)**: the field names encode the semantic difference.
  - `authority.default_allowed_actions` is the **process-level default**. It says "this is what most steps do." It is not a process-wide authority boundary. Steps may declare entirely different allowed actions (an investigate step that does only reads, when the process default is draft-write).
  - `steps[*].authority_overrides.allowed_actions` is the **step-level boundary**. For that step, this set (when present) is the actual list of allowed actions.
  - `authority.prohibited_actions` is the **hard ceiling**. No step can do anything in this set. Step-level prohibitions are additive and non-removable. This is the load-bearing safety constraint.
  - There is no process-wide "total authority" concept — authority is per-step, scoped by each step's effective allowed set minus the inherited prohibitions. Authors who want a hard maximum must express it as prohibitions.
- **Step authority merge semantics**:
  - `authority_overrides.allowed_actions`, when present at step level, **replaces** the process default. Steps may set an allowed action that is not in the process default.
  - `authority_overrides.prohibited_actions` is **unioned** with the process-level prohibitions. Step-level prohibited additions are allowed; step-level *removals* of inherited prohibitions are not. Rationale: prohibitions are safety constraints — a step cannot weaken them. This is the actual mechanism that keeps step-level discretion bounded.
  - `authority_overrides.autonomy_tier`, when present, **replaces** the process default for that step.
  - `authority_overrides.justification`, when present, is a free-text string explaining why this step deviates from the process default. Required by `W005` whenever the step's autonomy tier is more permissive than the process default.
  - **Effective allowed** = step `authority_overrides.allowed_actions` (if set) else process `default_allowed_actions`. **Effective prohibited** = process `prohibited_actions` ∪ step `authority_overrides.prohibited_actions`.
  - `E005` fires when any action appears in both effective allowed and effective prohibited.
- **Autonomy tier lattice** (least to most permissive): `human_only < assist < recommend < draft < execute_with_approval < execute_within_limits < autonomous_with_monitoring`. Used by `W005` to detect step-level escalation of autonomy.
- **One file per process** — process-level decisions belong together; splitting per-step creates drift.
- **`warnings:` and `knownGaps:` persisted by the author skill**, not by lint. Lint produces output; author reads lint output and writes warnings into the file. Lint itself is pure read.
- **No state machines, no FEEL expressions, no DMN tables, no OSCAL refs** — added only when a real user proves they need them.

### SKILL.md per step

Standard Claude Code skill with a `governance` block in frontmatter:

```markdown
---
name: sdlc-implement
description: Implement code to satisfy a design spec; opens a PR, never merges.
governance:
  process: ../../governance.yml
  step: implement
  inherits: [authority, evidence, escalation]
  overrides:
    autonomy_tier: draft
---

# Implement

## Authority (inherited from governance.yml, narrowed here)
You may: ...
You must not: ...

## Evidence
...

## Escalation
...

## Steps
[normal skill body]
```

The YAML is the canonical source for tooling. The prose body restates governance constraints inline so the runtime LLM sees them at execution time. Disagreement between the two is a semantic issue, not a mechanical one — `governed-autonomy:critique` flags prose/YAML drift; `ga-lint` does not, because freeform prose cannot be deterministically compared to structured YAML.

### governance-validation.md

Lightweight synthesis output produced once at authoring time. Records:

- What was claimed at each phase and what was probed
- Which contradictions were surfaced and how they resolved
- Which questions the user could not answer (research items)
- Which research mode was used and what sources informed the answer
- Which load-bearing claims the dialog accepted

Lives alongside `governance.yml`. Never regenerated.

## Dialog flow

The author skill is invoked with one of four entry shapes:

```
/governed-autonomy:author                       cold start
/governed-autonomy:author <path/to/notes.md>    notes branch
/governed-autonomy:author <path/to/SKILL.md>    retrofit branch
/governed-autonomy:author <path/to/process-dir> revision branch
```

Eleven phases, shared across branches; branches skip what's already known.

| Phase | Cold | Notes | Retrofit | Revision |
|---|---|---|---|---|
| 1. Process identity | ask | extract → confirm | ask | prefilled |
| 2. Roles & accountability **(hard refuse)** | ask | extract → confirm | ask | prefilled |
| 3. Authority — allowed/prohibited **(hard refuse)** | ask + catalog hints | extract → confirm | infer → confirm | prefilled |
| 4. Input quality gates | ask | extract | ask | prefilled |
| 5. Risk & blast radius | ask + catalog hints | extract | ask | prefilled |
| 6. Evidence & destination **(hard refuse)** | ask + catalog hints | extract | ask | prefilled |
| 7. Escalation vs approval **(hard refuse)** | ask | extract | infer → confirm | prefilled |
| 8. State & projection | ask | extract | ask | prefilled |
| 9. Decomposition into steps | ask | extract | one step | prefilled |
| 10. Per-step narrowing | per step | per step | n/a | only changed |
| 11. Emit | write files | write files | write files | rewrite changed |

### Grill-me loop per phase

Each phase is a small loop, not a single question:

1. **Ask** the phase's primary question.
2. **Probe** the answer — 1–3 follow-ups that test whether the answer is load-bearing. Examples:
   - Phase 2 (accountability): "If tech_lead is accountable, what specifically can be revoked? Who can actually page them? What happens when they're on vacation?"
   - Phase 3 (authority): "You said 'auto-approve under $5K' — what's the audit trail? What stops the agent from issuing 100 × $4,999 approvals in a row?"
   - Phase 5 (risk): "You said low risk, but this writes to production. Reconcile."
   - Phase 6 (evidence): "Who reads this? When? What decision do they make from it?"
3. **Cross-check** against prior phases. Dialog maintains a running list of claims; contradictions surface as probes.
4. **Accept** only when the answer survives the probe and doesn't contradict.

`--quick` mode reduces probing to one follow-up per phase. Trivial processes and revisions use it by default.

### Refusal model — two tiers

- **Mechanical refusal** — a core-set field is empty. Hard stop. No files written.
- **Quality refusal** — a core-set field is populated but doesn't survive grilling. Hard stop. Same as mechanical.

Quality refusal is what catches "passes validation, fails in production." Contradictions that don't touch core fields are recorded in `governance-validation.md` as unresolved items and proceed.

### Phase exemplars (the implementable form of "load-bearing")

The dialog does not use a binary rubric — that would rebuild the false-confidence problem the GAPS validator created. Instead, each phase has a set of exemplars showing what the dialog should probe for and what counts as accept vs reject. Exemplars are part of the spec, are testable as fixtures (run them through the implemented dialog and check the outcome), and are the closest implementable form of "doesn't survive grilling."

A worked exemplar for Phase 2 (Roles & accountability):

- **Probes the dialog must fire** (any answer must survive at least one):
  - "If <role> is accountable, what specifically can be revoked from them when this process fails?"
  - "Who can actually page <role> at 2am? What's the route?"
  - "What happens when <role> is on vacation? Who owns it then?"
- **Accept example**: "tech_lead is accountable. Failure means the on-call rotation pages them via PagerDuty. Vacation handoff is documented in the team runbook; deputy is staff_engineer. The merge bit can be revoked from their GitHub team membership."
- **Reject example (quality refusal fires)**: "The engineering team is accountable for everything." → probes surface no concrete revocation, no paging route, no handoff. Quality refusal: "accountable_for is populated but no concrete accountability mechanism survived probing."

Each phase ships with one accept exemplar and one reject exemplar in the spec. The author skill's implementation tests run those exemplars through the dialog and check that the dialog accepts the accept-exemplar and refuses the reject-exemplar. The exemplars themselves live in `docs/governed-autonomy/phase-exemplars/`. Full exemplar set is out of scope for this design doc and is the first deliverable of the implementation plan.

### Help and research when the user is stuck

Three modes the dialog can offer at any "I don't know" or quality-refusal moment:

1. **Brainstorm** — propose 2–3 candidate answers with tradeoffs and a recommendation. Used when the user has the knowledge but hasn't formalized it.
2. **Local research** — read the repo, prior `governance.yml` files, referenced docs. Used when the information exists in the workspace.
3. **External research** — use whatever external web search the host agent has available (provider-agnostic; no hard dependency on any specific search service). Used for standards, regulations, industry practice. If no external search is available, the dialog says so and falls back to brainstorm or local research.

The dialog offers the modes when about to refuse; the user can always type the answer to skip the offer. Sources go into `governance-validation.md`.

### Investigation as a step type

`step_kind: investigate` is recognized. Investigation steps:

- Are read-only by definition — only `data-plane-read` actions allowed
- Produce investigation evidence (findings, sources consulted, confidence assessment)
- Feed a downstream decision step; never decide themselves
- Safe at higher autonomy tier (`autonomous_with_monitoring` or `execute_within_limits`)

The dialog proposes an explicit investigation step when phase 5 (risk) or phase 8 (state) surface uncertainty the process needs to resolve before acting.

## Lint rules

`ga-lint` is a deterministic Python CLI (~150 lines target, no LLM). Reads `governance.yml` and the skills directory; writes nothing to disk (output goes to stdout/stderr; optional `--json` flag changes the format). Exits non-zero on errors; warnings don't fail the command. Mutating `governance.yml` to persist `warnings:` is the author skill's job, not lint's.

### Errors

| Rule | Check |
|---|---|
| `E001` core-field-missing | `process.id`, `process.name`, `roles`, `authority.default_allowed_actions` AND `authority.prohibited_actions` (both non-empty), `evidence.destination`, at least one `escalation` entry. Both sides of authority must be populated because "what the agent must not do" is load-bearing on its own; missing it produces ungoverned actions by omission. |
| `E002` accountable-role-absent | At least one role has `accountable_for` that is not `nothing`/empty |
| `E003a` catalog-ref-missing | A `catalog:` ref does not exist in the referenced catalog |
| `E003b` local-ref-undefined | A `local:` ref has no entry in `local_definitions`, or its `definition` is under 20 chars, or its `category` field is missing or not one of the catalog action-category values |
| `E003c` internal-ref-missing | A `role:`/`step:`/`lane:`/`evidence:` ref does not exist in the file |
| `E004` self-approval | For any gate, `gate.requires_role` must not equal `requires_role` of any step that (a) produces an evidence item the gate requires AND (b) has `step_kind: execute`. Catches the anti-pattern of the same role both executing the work product and approving it. Reviewer/approver workflows where a reviewer produces a verification finding and then approves are explicitly allowed — those producing steps are `investigate` or `monitor`, not `execute`. |
| `E005` action-conflict | Same action in both `allowed_actions` and `prohibited_actions` after step-override merge |
| `E006` step-without-skill | A `steps[*].id` has no matching `skills/<step-id>/SKILL.md` |
| `E007` skill-without-step | A `skills/<id>/SKILL.md` has no matching entry in `steps` |
| `E008` frontmatter-mismatch | A `SKILL.md` `governance.step` doesn't resolve, or `governance.process` path doesn't resolve to this file |
| `E009` agent-accountable | A role with `autonomous: true` has `accountable_for` set to a value that is not empty and not the sentinel `nothing`. The sentinel `nothing` is the explicit "this role owns no accountability" marker and is the recommended value for autonomous roles. (Operating model: agents do not own accountability.) |
| `E010` dead-gate | A gate requires evidence that no step produces |
| `E011` investigate-with-write | A `step_kind: investigate` step's effective allowed actions (after merge) include any action whose category is not `data-plane-read`. Catalog actions are checked by their declared `category`; `local:` actions are checked by the `category` field on their `local_definitions` entry. The `meta` category is **not** whitelisted because it includes mutating actions (`record-known-gap`, `archive-closed-work`, etc.). If an investigation must ask a human, split it into a read-only investigate step followed by a separate escalate/ask step. |
| `E012` step-role-missing | Every entry in `steps[*]` has a `requires_role` field whose value resolves to a defined role. There is no inheritance — each step names its responsible role explicitly. |
| `E013` steps-missing | `steps` is non-empty. A `governance.yml` with zero steps cannot be a process; even a single-skill process has one entry. |
| `E014` step-kind-invalid | Every `steps[*].step_kind` is one of the closed enum: `execute`, `investigate`, `decide`, `approve`, `monitor`. |

### Warnings

| Rule | Check |
|---|---|
| `W001` drift-policy-undefined | No `freshness.drift_policy` |
| `W002` blast-radius-undefined | `risk.blast_radius` missing or `unknown` |
| `W003` evidence-without-consumer | An evidence item has no `consumer` |
| `W004` step-purpose-missing | A step's `purpose` is missing or under 20 chars |
| `W005` autonomy-mismatch | Step `authority_overrides.autonomy_tier` is more permissive than the process default (per the autonomy lattice) AND `authority_overrides.justification` is missing or under 20 characters. Authors can suppress the warning by either tightening the override or supplying a real justification. |
| `W007` orphan-gate | A gate references no steps in `blocks_steps` |
| `W008` projection-as-canonical | A value in `state.projections` also appears as `state.canonical` |
| `W009` human-only-without-owner | A step with effective `autonomy_tier: human_only` has `requires_role` set to a role flagged `autonomous: true`, or has no `requires_role` at all. (A human-only step must name a non-autonomous role as its executor.) |
| `W010` escalation-condition-undefined | An escalation entry has an empty or `unknown` condition |

### Behavior

```
$ ga-lint governance.yml
governance.yml: E002 accountable-role-absent
  No role has a non-empty accountable_for.
  Operating model section 1 requires an accountable human owner.

governance.yml: W002 blast-radius-undefined
  risk.blast_radius is missing.

1 error, 1 warning
exit 1
```

JSON output via `--json` for CI use.

### Integration

- Author skill runs `ga-lint` after emit. Errors here signal a dialog bug (refusal logic should have caught them earlier). Warnings get written into `warnings:` and shown.
- Critique skill runs `ga-lint` first as baseline, layers LLM judgment on top.
- Pre-commit / CI can call `ga-lint --json` against any `governance.yml`.

## Critique skill

`governed-autonomy:critique` does not modify reviewed artifacts. It reads an existing skill, skill set, or process directory and writes a single sidecar file — `governance-review.md` — in the target's directory. Same operating-model concerns and same grill-me stance as the author skill, inverted.

Findings taxonomy:

- **blocking** — would trigger a hard refusal in the author skill
- **significant** — would be a lint error but isn't a core-field gate
- **advisory** — would be a lint warning, or a grill-me observation that didn't survive probing

Every finding cites the operating-model section it touches. This makes the review educational, not just a list of fails.

The critique skill can run against material that has no `governance.yml` at all — finding `F001 blocking: no governance record at all` is the natural first finding.

**Sequencing note:** the critique skill can ship before the author skill. Running it against existing artifacts (the v1 reference specs, the GADD reference package, external skills) produces evidence for whether the operating-model question set translates into useful findings on real material. Critique-first de-risks the question set before authoring bets on it.

## Decommission plan

### Stage 1 — Build alongside (no deletions)

Add skills and scripts:

```
skills/governed-autonomy-critique/SKILL.md
skills/governed-autonomy-author/SKILL.md
scripts/ga_lint/                              Python package, ~150 lines
scripts/ga-lint                               CLI entry point
```

Add commands and manifest entries (this is how slash commands route in this repo — `agent-skills.json` is the canonical registry):

```
commands/governed-autonomy/author.md
commands/governed-autonomy/author.toml
commands/governed-autonomy/critique.md
commands/governed-autonomy/critique.toml
commands/governed-autonomy/lint.md
commands/governed-autonomy/lint.toml
agent-skills.json                             add /governed-autonomy:author, :critique, :lint entries
gemini-extension.json                         add equivalents for Gemini routing
README.md                                     update Quick start to lead with /governed-autonomy:author
```

Add docs:

```
docs/governed-autonomy/authoring-dialog.md
docs/governed-autonomy/governance-sidecar.md
docs/governed-autonomy/critique.md
docs/governed-autonomy/lint.md
docs/governed-autonomy/phase-exemplars/       one file per phase, with probes + accept/reject examples
```

Repurpose (no code change, change use sites only): catalogs and operating-model docs become dialog content.

Demote to internal (remove from `agent-skills.json` and `gemini-extension.json`, remove slash commands, remove SKILL entry points): GAPS schema, validator, `validate-gaps-v1.py`. The skill packages under `skills/gaps-*/` stay on disk through Stage 2 but are no longer registered as user-facing commands.

### Stage 2 — Validate new flow

Acceptance criteria before deleting anything:

- **Golden critique fixtures**: three target artifacts (one v1 reference spec, the GADD reference package, one external skill) each have a ground-truth `governance-review.md` written by hand with expected finding ids and severities. The critique skill must produce findings whose ids match ground-truth at ≥80% rate (correct id + correct severity tier). Spurious findings beyond ground-truth are not failures but are reported.
- **Author skill cold-start fixture**: one new process is authored end-to-end from cold start; the resulting `governance.yml` passes `ga-lint` with zero errors; phase exemplar acceptance tests (accept-exemplar accepted, reject-exemplar refused) pass for every phase.
- **Author skill retrofit fixture**: an existing GADD skill is retrofitted; the dialog reads it, produces a `governance.yml`, and the merged process passes `ga-lint`.
- **Phase exemplar tests**: every phase's accept-exemplar produces accept; every reject-exemplar produces quality refusal.
- **`ga-lint` performance**: under 1 second on every `governance.yml` produced by the new flow (the cold-start fixture, the retrofit fixture, and the three golden-critique target processes). `ga-lint` reads `governance.yml`, not `ga-process.v1.yml`, so legacy GAPS example directories are out of scope for the lint acceptance target.

### Stage 3 — Delete

Once Stage 2 passes:

```
DELETE
skills/gaps-author/, skills/gaps-validate/, skills/gaps-generate/,
skills/gaps-lift/, skills/gaps-round-trip/
commands/gaps/ (all five .md and .toml)
scripts/gaps-lift.py, scripts/gaps-round-trip.py
scripts/gaps_v1_lift/, scripts/gaps_v1_migrator/, scripts/gaps_v1_generator/
scripts/migrate-gaps-v0-to-v1.py
scripts/generate-gaps-skill-package.py
scripts/generate-gaps-skill-package-v1.py
scripts/validate-gaps.py
scripts/validate-gaps-implementation.py
docs/governed-autonomy/gaps/authoring-guide.md
docs/governed-autonomy/gaps/generator.md
docs/governed-autonomy/gaps/round-trip.md
docs/governed-autonomy/gaps/migration-from-v0-1.md
gaps/examples/incident-response/, procurement-approval/, compliance-review/, gadd/    (v0 examples)
gaps/examples/v1/minimal/, comprehensive/, benefits-eligibility-review/,
              procurement-approval/, compliance-review/                                (v1 examples — keep 2)
```

Keep two v1 examples (`gadd` for anchoring GADD, `incident-response` for a different domain).

Update README to lead with `governed-autonomy:author` and `governed-autonomy:critique`; GAPS becomes a "see also" section.

### Stage 4 — Maintenance posture

After Stage 3:

- One author skill, one critique skill, one lint command — the user-facing surface
- One operating model and three catalog files — the conceptual surface
- One GAPS schema kept internally for `--emit-spec`
- Two reference processes

Approximately 5,200 lines of Python come out: generator, migrator, lift, round-trip, v0 validator, and validate-gaps-implementation. The schema, validator package, and catalogs stay.

### Not backwards-compatible, not a deprecation window

No shims, no migration warnings, no dual config formats. Stage 2 → Stage 3 is gated on functional acceptance, not time.

## Out of scope

The following are deliberately not part of this design:

- A deterministic renderer (`governance.yml` → `SKILL.md`). LLM authors directly.
- Per-skill governance sidecars. Governance is process-level.
- OSCAL control coverage analysis, conformance levels, state machines, FEEL expressions, DMN tables.
- Round-trip property tests (`SKILL.md` → `governance.yml` → `SKILL.md`).
- A v0/v1 GAPS migrator.
- Multi-platform skill packaging (Claude / Gemini / Copilot). The output is Claude Code skills; multi-platform packaging is a separate concern handled by `agent-skills.json` if a future need arises.

## Smallest useful next experiment

Build the critique skill first. Run it against:

- The five v1 reference specs in `gaps/examples/v1/`
- The `reference-packages/gadd/` skill set
- 1–2 external skills

Measure: does the operating-model question set produce useful findings on real material? If yes, the author skill is critique-in-reverse — same questions, opposite direction. If no, the question set needs revision before authoring is built on it.

## State persistence (v1 decision)

Dialog state for v1 lives in the host agent's conversation context for a single authoring session. Phase answers, accepted claims, probe outcomes, and contradictions are tracked in-conversation by the author skill itself (using TaskCreate or equivalent host-agent state, plus the running message history). Files are written only at emit phase 11.

Cross-session resumption — picking up an interrupted authoring session in a new conversation — is **deferred to a later version**. The dialog will not write partial `governance.yml` mid-session, and abandoning a session loses the dialog state. Users who need to pause mid-authoring can ask the dialog to emit a `governance-draft.md` with current answers, but this is opt-in and not a supported resume path.

This is an architectural constraint that the implementation plan inherits. It is not negotiable in the plan; changing it requires returning to design.

## Open questions for implementation

These belong in the implementation plan, not this design:

- File structure of the author skill (one SKILL.md or SKILL.md + sub-files per phase)
- Whether `governance-validation.md` is committed to git by default or gitignored
- Format of the `--emit-spec` flag invocation and where the spec file is written
- How `ga-lint` discovers `governance.yml` files when invoked without an argument
- Test harness format for phase exemplar fixtures (does each phase's exemplars actually round-trip through the dialog with the expected accept/reject outcome?)

---
name: governed-autonomy-author
description: Use when the user says /governed-autonomy:author or wants to create, retrofit, or revise governed-autonomy skills and process governance through an interrogative dialog.
---

# /governed-autonomy:author

Author a governed skill set through a dialog. The operating model is the question set; `governance.yml` is the process source of truth; each generated step gets its own `SKILL.md`.

State persists only in the current conversation. Do not write partial `governance.yml` files before Phase 11. Cross-session resume is not supported.

## Invocation

```text
/governed-autonomy:author
/governed-autonomy:author <path/to/notes.md>
/governed-autonomy:author <path/to/SKILL.md>
/governed-autonomy:author <path/to/process-dir>
```

Flags:

- `--quick`: use one probe per phase. Appropriate for trivial processes, focused revisions, or already well-governed inputs.
- `--emit-spec`: after emitting `governance.yml`, also write `<process-dir>/ga-process.v1.yml` and validate it with the kept GAPS v1 validator: `python3 scripts/validate-gaps-v1.py <process-dir>/ga-process.v1.yml`.

## Input Mode Detection

- **Cold start**: no path. Ask from scratch.
- **Notes**: path to notes, policy, process doc, or transcript. Extract candidate answers, then confirm.
- **Retrofit**: path to an existing `SKILL.md` or skill directory without `governance.yml`. Infer authority/evidence/escalation from the skill, then confirm before accepting.
- **Revision**: path to a process directory with `governance.yml`. Prefill all phases, ask only where changes or contradictions appear.

If the mode is unclear, ask one clarifying question. Do not invent organization-specific facts.

## Required Reads

- `docs/governed-autonomy/operating-model.md`
- `docs/governed-autonomy/phase-exemplars/phase-01-process-identity.md` through `phase-10-per-step-narrowing.md`
- `gaps/catalogs/v1/actions.yml`, `evidence-kinds.yml`, and `risk-patterns.yml` as suggestion material
- Supplied notes, existing skills, or process directory

## Grill-Me Loop

Every phase follows:

1. Ask the primary question.
2. Probe the answer with 1-3 follow-ups from the relevant phase exemplar. In `--quick`, ask one probe.
3. Cross-check against already accepted claims.
4. Accept only when the answer is load-bearing and not contradicted.

When an answer is weak, offer help before refusal:

- **Brainstorm**: propose 2-3 candidate answers with tradeoffs.
- **Local research**: inspect repository docs, prior `governance.yml` files, or referenced artifacts.
- **External research**: use whatever web search the host agent provides; if unavailable, say so and fall back to brainstorm or local research.

Record accepted claims, probes, contradictions, and research sources in conversation state for Phase 11.

## Refusal Model

- **Mechanical refusal**: a core field is empty. Hard stop. No files written.
- **Quality refusal**: a core field is populated but fails probing. Hard stop when it affects accountability, authority, evidence destination, or escalation.

Non-core contradictions become `warnings:` or `knownGaps:` and are recorded in `governance-validation.md`.

Core hard-refusal fields:

- at least one accountable human role;
- both `authority.default_allowed_actions` and `authority.prohibited_actions`;
- `evidence.destination`;
- at least one escalation path.

## Phases

### Phase 1 - Process Identity

Primary question: what process are we governing, what is its purpose, and what is in or out of scope?

Probe with `phase-01-process-identity.md`: ask what the process does not cover and what observable result proves it worked.

Accept when `process.id`, `process.name`, one-sentence `process.purpose`, and scope includes/excludes are concrete. Quality-refuse when the process is just a broad aspiration.

### Phase 2 - Roles and Accountability

Primary question: which roles participate, and which human role is accountable for outcomes?

Probe with `phase-02-roles-accountability.md`: revocation, paging route, and handoff. Autonomous roles must use `accountable_for: nothing`.

Accept when a named human role owns failure operationally. Mechanically refuse when no accountable human role exists. Quality-refuse when accountability is assigned to a vague group with no route, revocation, or handoff.

### Phase 3 - Authority

Primary question: what may the autonomous system do, and what must it never do?

Probe with `phase-03-authority.md`: audit trail, rate/abuse control, and whether prohibitions are load-bearing. Suggest catalog actions, but allow `local:` definitions with category and definition.

Accept when both allowed and prohibited actions are explicit. Mechanically refuse if either side is empty. Quality-refuse when authority is phrased as "do useful things" or "avoid harm."

### Phase 4 - Input Quality Gates

Primary question: what input must exist before the process starts, and what happens when it is weak?

Probe with `phase-04-input-gates.md`: source, fields, owner, and weak-input routing.

Accept concrete gate criteria and routing. Quality-refuse vague "good ticket" standards, but do not hard-refuse if the process intentionally accepts broad input; record the risk.

### Phase 5 - Risk and Blast Radius

Primary question: what can break, how reversible is it, and which risk patterns matter?

Probe with `phase-05-risk-blast-radius.md`: worst case, detection time, reversal path, and contradiction with authority.

Accept named blast radius and relevant risk patterns. Quality-refuse claims like "low risk because humans approve" when approval fatigue or downstream harm is unresolved.

### Phase 6 - Evidence and Destination

Primary question: what evidence is produced, who consumes it, and where does it live later?

Probe with `phase-06-evidence.md`: producer, consumer, decision use, destination, and retention.

Accept when evidence has destination and consumers who make real decisions. Mechanically refuse when no evidence destination exists. Quality-refuse evidence nobody reads.

### Phase 7 - Escalation and Approval

Primary question: when does the system escalate, to whom, and which transitions require approval?

Probe with `phase-07-escalation-approval.md`: distinguish escalation from approval, routing, self-approval, and approver identity.

Accept concrete escalation conditions and routes plus any approval gates. Mechanically refuse when no escalation path exists. Quality-refuse "ask engineering when confused."

### Phase 8 - State and Projection

Primary question: where is canonical state, and which systems are projections?

Probe with `phase-08-state-projection.md`: conflict resolution, chat-as-control-plane risk, and drift policy.

Accept when canonical state and projections are named. Record warnings when canonical state or drift policy is weak.

### Phase 9 - Decomposition Into Steps

Primary question: what are the discrete agent-executable steps?

Probe with `phase-09-decomposition.md`: grain, pause points, `step_kind`, and `requires_role`.

Accept non-empty steps with `id`, `label`, `purpose`, `step_kind`, and `requires_role`. Quality-refuse a mega-step such as "the agent does the work."

### Phase 10 - Per-Step Narrowing

Primary question: where does each step narrow or change process-level authority?

Probe with `phase-10-per-step-narrowing.md`: read-only investigation, human-only steps, more-permissive autonomy, and justification.

Accept inheritance by default. Record `authority_overrides` only where a step deviates. Quality-refuse more-permissive overrides justified only by speed or convenience.

### Phase 11 - Emit

Primary question: where should the process directory be written, and are the accepted claims ready to emit?

Before writing, build the draft `governance.yml` in conversation state. Summarize the process, hard-refusal fields, warnings, known gaps, and target directory. If the user changes a core answer, return to the relevant phase.

Pipe the draft into `scripts/ga-lint --stdin --json` when available. If lint reports errors, return to the offending phase and write no files. If lint reports warnings, persist them in `warnings:` and summarize them. Warnings do not block emit.

Only after clean pre-emit lint, write:

- `<process-dir>/governance.yml`
- `<process-dir>/governance-validation.md`
- `<process-dir>/skills/<step-id>/SKILL.md` for every step
- optional `<process-dir>/commands/<process-id>.md` only when an orchestrator command is explicitly part of the process
- optional `<process-dir>/ga-process.v1.yml` when `--emit-spec` is set

After writing, run `ga-lint <process-dir>/governance.yml` when available as a sanity check. If lint fails after a clean pre-emit lint, report this as a bug in the dialog, not as a user error, and do not claim success.

When `--emit-spec` is set, generate the GAPS v1 projection from the accepted conversation state, write `<process-dir>/ga-process.v1.yml`, and run `python3 scripts/validate-gaps-v1.py <process-dir>/ga-process.v1.yml`. If validation fails, keep `governance.yml` as canonical and report the spec projection failure.

## governance.yml Rules

Use the conventions documented in `docs/governed-autonomy/governance-sidecar.md`:

- refs are namespaced: `catalog:`, `local:`, `role:`, `step:`, `evidence:`, and `lane:`;
- `local:` refs must have top-level `local_definitions`;
- process-level allowed actions are defaults, not a global maximum;
- process prohibitions are a hard ceiling and step prohibitions union with them;
- step allowed actions replace the process default when present;
- `step_kind` is one of `execute`, `investigate`, `decide`, `approve`, or `monitor`;
- investigation steps are read-only.

## Step SKILL.md Rules

Each generated step skill must:

- include normal Agent Skill frontmatter;
- include a `governance:` frontmatter block with `process`, `step`, `inherits`, and any overrides;
- restate authority, evidence, and escalation in prose so the runtime agent sees them;
- keep prose aligned with `governance.yml`;
- avoid claiming legal, regulatory, certification, or executable correctness.

## governance-validation.md Rules

Record:

- phase claims accepted;
- probes asked and answers received;
- contradictions found and how resolved;
- research modes used and sources consulted;
- unresolved questions and known gaps;
- load-bearing claims accepted for hard-refusal fields.

This file is authoring evidence and is committed by default.

## Stop Conditions

Stop without writing when:

- a core hard-refusal field is mechanically missing;
- a core field fails quality probing;
- the user asks for regulatory, legal, certification, or compliance conclusions;
- the target path would overwrite unrelated existing files;
- the requested process has no accountable human owner.

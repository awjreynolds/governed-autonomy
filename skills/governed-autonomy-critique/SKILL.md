---
name: governed-autonomy-critique
description: Use when the user says /governed-autonomy:critique or wants a read-only Governed Autonomy review of a skill, skill set, process directory, or artifact without a governance record.
---

# /governed-autonomy:critique

Review an existing artifact for Governed Autonomy quality. This skill is read-only against the reviewed artifact: it writes exactly one file, `governance-review.md`, in the target directory.

Treat `docs/governed-autonomy/operating-model.md` as the review backbone. Use `ga-lint` as the deterministic baseline when a `governance.yml` exists, then add LLM judgment for gaps that lint cannot decide, especially prose/YAML drift, weak accountability, non-load-bearing authority, and evidence nobody consumes.

## Inputs

Accepted target shapes:

- **Single skill**: a path to one `SKILL.md`.
- **Skill set**: a directory containing `skills/*/SKILL.md`.
- **Process directory**: a directory containing `governance.yml`, optional `governance-validation.md`, and generated skills.
- **No-governance directory**: a directory or artifact with no `governance.yml`; still review it and normally start with `F001 blocking: no governance record at all`.

If the target is ambiguous, ask for one path. Do not infer a target from unrelated repository files.

## Reads

- The target artifact or directory.
- `governance.yml`, if present.
- Step `SKILL.md` files, if present.
- `governance-validation.md`, if present.
- `docs/governed-autonomy/operating-model.md`.
- `docs/governed-autonomy/uncontrolled-ai-risk-patterns.md`, when risk claims need context.
- `gaps/catalogs/v1/actions.yml`, `evidence-kinds.yml`, and `risk-patterns.yml`, when catalog references appear.

## Writes

Write only:

```text
<target-dir>/governance-review.md
```

Never edit reviewed artifacts. Never create or update `governance.yml`, `SKILL.md`, manifests, commands, tickets, or source code from this skill.

## Baseline

If `governance.yml` exists, run `ga-lint <path/to/governance.yml>` before the LLM review.

- Copy lint errors and warnings into the review under "Lint Baseline".
- If `ga-lint` is unavailable, record `baseline_unavailable` with the exact command attempted and continue the LLM review.
- Do not treat a clean lint result as sufficient. Lint checks mechanical structure; critique checks whether governance claims are load-bearing.

## Review Structure

Review in this order, citing the operating-model section for every finding:

1. **Roles and decision rights**: named human accountability, decision rights, revocation, handoff, and the rule that autonomous systems own no accountability.
2. **Authority boundaries**: allowed actions, prohibited actions, limits, write surfaces, escalation triggers, and omitted authority that would be unsafe by implication.
3. **Input quality gates**: viable input criteria and routing for weak input.
4. **Scope and execution boundaries**: includes/excludes, stop conditions, assumption limits, and scope reset triggers.
5. **Risk and blast radius**: customer, financial, legal, data, operational, reversibility, and cross-system impact.
6. **Evidence requirements**: evidence items, producers, consumers, destinations, retention, and whether evidence informs a real decision.
7. **Escalation and approval**: distinction between escalation and approval, named routes, self-approval, and approval fatigue.
8. **State and auditability**: durable source of truth for state, evidence, approvals, and closure.
9. **Projection into existing systems**: canonical/projection split, drift policy, and conflict resolution.

For generated skill sets, also check whether each step skill's prose matches `governance.yml`: authority, evidence, escalation, role, and step id. Flag semantic drift; do not try to auto-fix it.

## Findings Taxonomy

Use these severity tiers:

- **blocking**: would trigger a hard refusal in `/governed-autonomy:author`; examples include no governance record, no accountable human role, missing allowed or prohibited actions, missing evidence destination, or missing escalation path.
- **significant**: would be a lint error or a structural governance defect outside the author hard-refusal core; examples include self-approval, undefined refs, dead gates, investigate steps with write authority, or missing step skills.
- **advisory**: would be a lint warning or a grill-me observation that weakens governance but does not block emit; examples include unknown blast radius, missing drift policy, vague input gates, or evidence with weak consumers.

Use finding ids in this form:

```text
F001 blocking: no governance record at all
F002 blocking: accountable human role absent
F101 significant: self-approval possible at pre-merge gate
F201 advisory: blast radius named but not operationalized
```

Prefer stable ids when equivalent findings recur. Do not invent pass/fail scores.

## Citation Requirement

Every finding must cite:

- the artifact location, with file path and line number when available;
- the operating-model concern, e.g. "Operating model section 2, Authority boundaries";
- any lint rule id when the finding came from `ga-lint`;
- any catalog or risk-pattern source used.

If a finding is inferred from absence, cite the files inspected and state the absence explicitly.

## Output Format

Write `governance-review.md` with:

```markdown
# Governance Review

Target: <path>
Review date: <YYYY-MM-DD>

## Lint Baseline
<command, status, copied issues or baseline_unavailable>

## Findings

### F001 blocking: <title>
- Evidence: <path:line or inspected absence>
- Operating-model citation: <section>
- Impact: <why this matters>
- Remediation: <smallest useful fix>

## Residual Risk
<short note, including areas not inspected>
```

If there are no findings, say so and still include lint baseline and residual risk.

## Stop Conditions

Stop without writing when:

- the target path does not exist;
- the user asks the critique skill to modify the artifact;
- producing a review would require facts owned by a human process owner and no artifact evidence exists.

When stopping, report the blocker in the conversation only.

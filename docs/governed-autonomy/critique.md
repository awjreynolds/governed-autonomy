# Governed Autonomy Critique

`/governed-autonomy:critique` is a read-only review surface for governed skills and process directories. It writes one sidecar, `governance-review.md`, beside the target and does not edit the reviewed artifact.

Use it when you have an existing `SKILL.md`, a generated skill set, a process directory with `governance.yml`, or an artifact that should have governance but does not.

## Inputs

Accepted shapes:

- one `SKILL.md`;
- a directory containing `skills/*/SKILL.md`;
- a process directory containing `governance.yml`;
- a directory with no governance record, where the likely first finding is `F001 blocking: no governance record at all`.

The critique reads the target, the operating model, any sidecars present, and catalog files when catalog references appear.

## Review Method

The review follows the nine operating-model concerns:

1. roles and decision rights;
2. authority boundaries;
3. input quality gates;
4. scope and execution boundaries;
5. risk and blast radius;
6. evidence requirements;
7. escalation and approval;
8. state and auditability;
9. projection into existing systems.

When `governance.yml` exists, the critique runs `ga-lint` first and includes the result as the deterministic baseline. It then adds LLM judgment for issues lint cannot decide, such as weak accountability, prose/YAML drift, vague evidence consumers, or approval fatigue.

## Findings

Findings use three severity tiers:

- `blocking`: would stop the author dialog from emitting, such as missing accountable human role, missing authority, missing evidence destination, or no escalation path.
- `significant`: structural governance defects outside the author hard-refusal core, usually equivalent to lint errors.
- `advisory`: lint warnings or grill-me observations that weaken governance but do not block emit.

Every finding cites the artifact location and the operating-model section it touches. Absence findings cite the inspected files and state what was missing.

## Output

The only output file is:

```text
<target-dir>/governance-review.md
```

The reviewed artifact remains unchanged. If the user wants edits after a critique, run `/governed-autonomy:author` in revision or retrofit mode.

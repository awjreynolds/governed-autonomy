# Governed Autonomy Lint

`/governed-autonomy:lint` routes to the deterministic `ga-lint` checker for `governance.yml`.

Lint is not an LLM critique. It reads the governance sidecar and matching `skills/<step-id>/SKILL.md` files, reports mechanical errors and warnings, and writes nothing to disk. Warnings do not fail the command; errors do.

The Python implementation is intentionally separate from this user-facing surface. In this phase, the command router documents and invokes `scripts/ga-lint` when that implementation exists.

## Inputs

```bash
scripts/ga-lint governance.yml
scripts/ga-lint --json governance.yml
scripts/ga-lint
```

Without an argument, the lint implementation should walk up from the current directory looking for `governance.yml`, then fall back to bounded repository discovery. It should error when zero or multiple candidates exist.

## What Lint Checks

Errors include missing core fields, absent accountable human role, undefined references, self-approval, allowed/prohibited action conflicts, missing step skills, governance frontmatter mismatch, autonomous roles owning accountability, dead gates, write authority in investigate steps, missing step roles, missing steps, and invalid step kinds.

Warnings include missing drift policy, unknown blast radius, evidence without consumers, weak step purpose, more-permissive autonomy overrides without justification, orphan gates, projections treated as canonical, human-only steps assigned to autonomous roles, and undefined escalation conditions.

## Relationship to Author and Critique

`/governed-autonomy:author` runs lint after Phase 11 emit. Lint errors after emit mean the dialog emitted invalid governance and must be corrected. Lint warnings are persisted into `warnings:` by the author skill.

`/governed-autonomy:critique` runs lint as a baseline, then adds judgment over the operating model.

Lint does not prove the process is well-governed. It proves the sidecar is mechanically checkable enough for the higher-level review surfaces.

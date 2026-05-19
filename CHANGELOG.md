# Changelog

## 1.1.0 — 2026-05-19

Governed Autonomy authoring cutover. Replaces hand-authored GAPS specs
as the user-facing workflow with an interrogative author dialog,
read-only critique skill, and deterministic `ga-lint` CLI for
`governance.yml`.

### Added

- `/governed-autonomy:author`, `/governed-autonomy:critique`, and
  `/governed-autonomy:lint` command surfaces.
- `scripts/ga-lint` and `scripts/ga_lint/` deterministic lint package.
- Phase exemplar contracts for the operating-model dialog.
- Critique and author acceptance fixtures.

### Changed

- README and quickstart now lead with governed-autonomy authoring,
  critique, and linting.
- GAPS v1 schema/catalogs/validator are retained as internal
  `--emit-spec` plumbing.

### Removed

- Retired GAPS user-facing skills, commands, generator, migrator, lift,
  round-trip, v0 validator, v0 examples, and generated v1 package
  examples.

## 1.0.0 — 2026-05-19

GAPS v1.0.0. Adopts OSCAL structurally for evidence and control
mappings, adopts CMMN case-and-stage and DMN decision-table concepts
conceptually. Adds controlled vocabularies, typed evidence, executable
state and gate models, conformance levels, a spec-driven generator,
reverse lift, and round-trip verification.

### Added

- v1 ga-process schema (`gaps/schema/v1/`).
- Catalogs: actions, evidence kinds, risk patterns, NIST AI RMF, ISO/IEC
  42001 Annex A, EU AI Act articles (`gaps/catalogs/v1/`).
- v1 validator (`scripts/validate-gaps-v1.py`) with schema, cross-ref,
  catalog-ref, state-machine, gate-decision, authority, OSCAL-ref, and
  conformance-level checks.
- v1 generator (`scripts/retired GAPS v1 package builder`).
- Migrator (`scripts/retired v0-to-v1 migration tool`).
- Reverse lift (`scripts/retired GAPS lift script`).
- Round-trip (`scripts/retired GAPS round trip script`).
- Five v1 reference specs: `gadd`, `compliance-review`,
  `incident-response`, `procurement-approval`,
  `benefits-eligibility-review`. Plus minimal and comprehensive
  fixtures.
- v1 user-facing skills: `/gaps:lift` and `/gaps:round-trip`.
- Docs set under `docs/governed-autonomy/gaps/`.

### Changed

- `skills/retired GAPS author`, `skills/retired GAPS validate`, and `skills/retired GAPS generate`
  now point at v1 workflows by default.

### Deprecated

- v0.1 schema, validator, and generator print a one-line deprecation
  notice on invocation. They remain available for the deprecation
  window but receive only bug fixes.

### Not changed

- v0.1 reference specs continue to validate against the v0.1 validator.

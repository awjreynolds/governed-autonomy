# Changelog

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
- v1 generator (`scripts/generate-gaps-skill-package-v1.py`).
- Migrator (`scripts/migrate-gaps-v0-to-v1.py`).
- Reverse lift (`scripts/gaps-lift.py`).
- Round-trip (`scripts/gaps-round-trip.py`).
- Five v1 reference specs: `gadd`, `compliance-review`,
  `incident-response`, `procurement-approval`,
  `benefits-eligibility-review`. Plus minimal and comprehensive
  fixtures.
- v1 user-facing skills: `/gaps:lift` and `/gaps:round-trip`.
- Docs set under `docs/governed-autonomy/gaps/`.

### Changed

- `skills/gaps-author`, `skills/gaps-validate`, and `skills/gaps-generate`
  now point at v1 workflows by default.

### Deprecated

- v0.1 schema, validator, and generator print a one-line deprecation
  notice on invocation. They remain available for the deprecation
  window but receive only bug fixes.

### Not changed

- v0.1 reference specs continue to validate against the v0.1 validator.

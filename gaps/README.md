# GAPS

GAPS is the **Governed Autonomy Process Specification** layer incubating in this repository.

GADD is the concrete software-delivery methodology. GAPS is the emerging profile for describing how a governed process preserves accountability, authority, autonomy boundaries, evidence, escalation, approval, state, projection, verification, closure, and external control mappings when autonomous systems may participate.

## Status

GAPS remains exploratory. The current validation profile is built from four reference processes.

The current surface is intentionally small:

- `examples/gadd/ga-process.yml` expresses GADD as the first reference process.
- `examples/gadd/implementation.yml` binds that GADD process spec to a reference-package fixture copied from the concrete GADD skill package.
- `examples/compliance-review/ga-process.yml` expresses a second, unlike casework reference process.
- `examples/incident-response/ga-process.yml` expresses a time-critical operational response process.
- `examples/procurement-approval/ga-process.yml` expresses a budget, supplier-risk, and segregation-of-duties process.
- `schema/ga-process.schema.json` defines the exploratory machine-readable shape.
- `schema/implementation.schema.json` defines the exploratory implementation-map shape.
- `../scripts/validate-gaps.py` validates reference processes against the schema and GAPS-specific semantic checks.
- `../scripts/validate-gaps-implementation.py` validates implementation maps against process specs and package files.
- `/gaps:author`, `/gaps:validate`, and `/gaps:generate` provide the first GAPS authoring, validation, and skill-package generation skills.
- This README explains the incubation model and boundaries.

There is no BPMN/CMMN/DMN/OSCAL exporter or runtime target yet.

## v0.1 deprecation

GAPS v0.1 is in deprecation. New specs should be authored at v1.0.0. The
v0.1 schema, validator, and generator remain available for the
deprecation window but receive only bug fixes:

- `gaps/schema/ga-process.schema.json` — v0.1 schema (frozen).
- `scripts/validate-gaps.py` — v0.1 validator (frozen).
- `scripts/generate-gaps-skill-package.py` — v0.1 generator (frozen).

v0.1 reference specs continue to validate against the v0.1 validator. A
migrator (`scripts/migrate-gaps-v0-to-v1.py`) produces a v1 spec at
descriptive conformance from any v0.1 spec.

## v1.0.0 Incubation

GAPS v1.0.0 is in active design. v1 lives alongside v0.1 during the
deprecation window and uses a separate validator, schema, and catalogs:

- `gaps/schema/v1/` — v1 JSON Schemas (ga-process + catalog meta-schemas).
- `gaps/catalogs/v1/` — controlled vocabularies (actions, evidence kinds,
  risk patterns).
- `gaps/catalogs/v1/controls/` — OSCAL control catalogs (NIST AI RMF,
  ISO/IEC 42001 Annex A, EU AI Act) generated from compact YAML sources
  via `scripts/build-oscal-catalogs.py`.
- `gaps/examples/v1/` — v1 reference specs.
- `scripts/validate-gaps-v1.py` — v1 structural schema validator.
- `scripts/validate-catalogs.py` — catalog meta-validator.

The v1.0.0 reference docs live at `docs/governed-autonomy/gaps/`.

v1.0.0 adopts OSCAL structurally for evidence and control mappings, and
adopts CMMN case-and-stage and DMN decision-table concepts conceptually in
GAPS-native YAML. See `docs/superpowers/specs/2026-05-18-gaps-v1-0-0-design.md`
for the full architecture.

### v1 reference specs

The v1 reference set lives under `gaps/examples/v1/`:

- `gadd/` — software-delivery case study, migrated from v0.1 at descriptive conformance.
- `compliance-review/` — adaptive compliance review, migrated from v0.1 at descriptive conformance.
- `incident-response/` — incident handling, migrated from v0.1 at descriptive conformance.
- `procurement-approval/` — procurement approvals, migrated from v0.1 at descriptive conformance.
- `benefits-eligibility-review/` — public-sector casework reference, authored fresh and promoted to generative conformance.
- `minimal/` — schema smoke-test fixture at descriptive conformance.
- `comprehensive/` — validator coverage fixture at machine-validatable conformance.

Migrate a v0.1 spec to v1:

```bash
python3 scripts/migrate-gaps-v0-to-v1.py gaps/examples/<process-id>/ga-process.yml
```

The migrator always emits `conformanceLevel: descriptive`. Uplift to
`machine-validatable` and `generative` deliberately, recording the
review in `freshness.driftPolicy`.

### v1 generator

A generative-conformance spec drives the generator:

```bash
python3 scripts/generate-gaps-skill-package-v1.py gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml --output-root gaps/generated/benefits-eligibility-review --validate-after
```

The pilot package lives at `gaps/examples/v1/benefits-eligibility-review/expected/`. The generator produces a deterministic byte-identical package for unchanged input.

OSCAL JSON files are generated from compact YAML sources under
`gaps/catalogs/v1/controls/sources/`. Regenerate after editing a source:

```bash
python3 scripts/build-oscal-catalogs.py
```

CI runs `python3 scripts/build-oscal-catalogs.py --check` to detect drift
between sources and committed JSON.

## Relationship to existing standards

GAPS is not intended to become a competing process notation.

Where existing standards already own a concept, GAPS should align with them rather than re-derive them:

- BPMN for structured process flow.
- CMMN for adaptive case-style work.
- DMN for decision and policy logic.
- OSCAL-style structures for control mappings, implementation status, and evidence.
- NIST AI RMF, ISO/IEC 42001, and the EU AI Act as governance and regulatory anchors where applicable.

The intended GAPS contribution is the Governed Autonomy profile layered over that substrate:

- autonomy tier
- authority plane
- gate type
- human accountability
- evidence contract
- escalation and approval separation
- canonical state and projection rule
- drift and freshness rule
- Governed Autonomy risk-pattern coverage
- external control mapping stubs

## Why GADD is the first reference process

GADD already implements Governed Autonomy for the software-delivery process: intake, triage, product scope, technical design, planning, implementation, verification, closure, and archive cleanup.

Using GADD first keeps GAPS grounded in a real process with existing skills, templates, ledgers, tests, and docs. If GAPS cannot describe GADD faithfully, the GAPS model is not ready to generalize.

## GADD implementation binding

GADD is the first GAPS-described agent skill package and remains the concrete SDLC implementation in the `gadd` repository.

The binding is explicit:

- `examples/gadd/ga-process.yml` describes the governed software-delivery process.
- `examples/gadd/implementation.yml` maps each GAPS lane, gate, command, and control-plane action to GADD skills, command adapters, manifests, and validators.
- `../reference-packages/gadd/` contains a fixture copy of the GADD package surfaces needed to validate that implementation map in this repository.
- `../scripts/validate-gaps-implementation.py` checks that the implementation map still matches the process spec and reference package files.

This is an implementation-conformance check for the repo package. It is not a regulatory, legal, standards-export, or runtime-execution claim.

## V0.1 completion rule

The GADD reference process should be faithful and explicit, not exhaustive.

The reference process is acceptable when:

- every current GADD lane and approval boundary is represented
- core fields are present where they apply
- missing or weak concepts are recorded as known gaps
- optional fields are used only when they describe real GADD behavior
- no regulatory, safety, validator, generation, or runtime execution support is claimed

Sparse but honest is better than a large file that invents structure GADD does not yet have.

## Additional reference processes

The additional reference processes are intentionally unlike GADD.

The compliance review example stresses adaptive case flow, long-running state, statutory or policy deadlines, named human identities, multiple authority levels, budget or resource gates, and event-driven escalation.

The incident response example stresses severity escalation, time-boxed containment, rollback authority, evidence preservation, communication approval, and closure under operational pressure.

The procurement approval example stresses budget gates, supplier-risk review, segregation of duties, contract handoff, conflict escalation, and renewal monitoring.

## Validation

Run:

```bash
python3 scripts/validate-gaps.py
python3 scripts/validate-gaps-implementation.py
```

The validator checks every `gaps/examples/*/ga-process.yml` file against `gaps/schema/ga-process.schema.json` and GAPS-specific semantic rules.

The implementation validator checks `gaps/examples/gadd/implementation.yml` against `gaps/examples/gadd/ga-process.yml` and the GADD reference package fixture.

Validator success means the reference processes and implementation maps conform to this repository's current exploratory GAPS profile. It is not regulatory compliance, certification, proof of executable correctness, legal sufficiency, or a BPMN/CMMN/DMN/OSCAL export.

## Generation

Run:

```bash
python3 scripts/generate-gaps-skill-package.py <path-to-ga-process.yml>
```

Generation is dry-run-first. By default it writes a reviewable package skeleton under `gaps/generated/<process-id-slug>/` with skills, command adapters, manifest patch suggestions, an implementation map, and a validation checklist.

When `implementation.yml` exists beside the input `ga-process.yml`, the generator uses it to produce command-level skill skeletons that match the implementation map. For GADD, that means generated skills such as `gadd-refine`, `gadd-implement`, and `gadd-verify`, not only broad lane skills. Use `--no-implementation-map` to force the older lane-level preview mode, or `--implementation-map <path>` to supply a map explicitly.

Adopting generated files into package roots requires explicit write mode:

```bash
python3 scripts/generate-gaps-skill-package.py <path-to-ga-process.yml> --write --adopt-output
```

Adopted mode writes package files under `skills/` and `commands/`, while review artifacts stay under `gaps/generated/<process-id-slug>/`. Existing files are not replaced unless `--overwrite` is also supplied.

Generated output is a starting point for human process-owner review. It is not production-ready by default and does not claim regulatory compliance, certification, legal sufficiency, runtime execution, or standards export.

To validate this repository's full GAPS surface, run:

```bash
./scripts/validate-governed-autonomy.sh
```

## Files

- `examples/gadd/ga-process.yml` - GADD as the first GAPS reference process.
- `examples/gadd/implementation.yml` - GADD implementation map for the skill package.
- `examples/compliance-review/ga-process.yml` - Compliance review casework as the second GAPS reference process.
- `examples/incident-response/ga-process.yml` - Incident response as a time-critical operational reference process.
- `examples/procurement-approval/ga-process.yml` - Procurement approval as a budget and supplier governance reference process.
- `schema/ga-process.schema.json` - Exploratory schema for the GAPS process profile.
- `schema/implementation.schema.json` - Exploratory schema for implementation maps.

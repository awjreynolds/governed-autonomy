# GAPS v1 Format Reference

The canonical schema is `gaps/schema/v1/ga-process.schema.json`. This
page summarizes the top-level shape.

## Required top-level keys

- `gapsVersion` (must be `"1.0.0"`)
- `specStatus` (`draft | published | deprecated`)
- `conformanceLevel` (`descriptive | machine-validatable | generative`)
- `process` (id, name, purpose, scope)
- `substrate` (paths to catalogs)
- `roles` (with id, label, accountabilityScope)
- `evidenceModel.caseFileItems` (typed evidence entities)
- `lanes` (with authority, optional state model, evidence i/o, skills)
- `gates` (with gateType, approvalRole, optional decision table)
- `projectionPolicy` (canonicalStateSource, external systems)
- `riskPatterns` (references the risk-patterns catalog)
- `controlAssessment` (OSCAL-shaped controls)
- `freshness` (review date, drift policy)
- `knownGaps`

## Optional

- `process.localActions` (process-specific action extensions, with justification)
- `controlPlaneActions` (skills that mutate governance state)
- `freshness.implementationFingerprint` (set by the generator)

## Conformance level gating

- `descriptive` - structural schema + cross-references + catalog references.
- `machine-validatable` - additionally requires non-empty
  `allowedActions`, `prohibitedActions`, and gate
  `approvalCondition`/`escalationCondition` text on every applicable entry.
- `generative` - additionally requires `stateModel` on every lane, a
  `guard` on every transition, a `decision` on every blocking gate, and
  `shape.required` on every evidence item used as a lane input.

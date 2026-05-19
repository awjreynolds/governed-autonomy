# GAPS v1 Catalogs

Catalogs are the controlled vocabularies the v1 format depends on. They
live under `gaps/catalogs/v1/`.

## Action catalog (`actions.yml`)

A flat list of action primitives. Each entry has an id, a category
(`data-plane-read`, `data-plane-draft`, `data-plane-persist`,
`data-plane-external`, `control-plane`, `meta`,
`prohibited-anti-pattern`), default autonomy and risk tiers, a
definition, and optional examples / role-affinity hints.

Specs reference action ids in `lane.authority.allowedActions[]`,
`lane.authority.prohibitedActions[]`, `lane.autonomousResponsibilities[]`,
`role.decisionRights[]`, and `controlPlaneActions[].actions[]`.

A spec may extend the catalog locally via `process.localActions[]`, but
each local action requires a justification string.

## Evidence-kinds catalog (`evidence-kinds.yml`)

Categories of evidence: `observation`, `attestation`, `finding`,
`decision-record`, `artifact-ref`, `audit-event`, `external-reference`.
Each kind declares default producer, default retention, and default
shape.

Specs reference evidence-kind ids in
`evidenceModel.caseFileItems[].kind`.

## Risk-patterns catalog (`risk-patterns.yml`)

The nine governed-autonomy risk patterns from
`docs/governed-autonomy/uncontrolled-ai-risk-patterns.md`, formalized
with stable ids and signals.

Specs reference risk-pattern ids in `riskPatterns[].patternRef`.

## OSCAL control catalogs

`gaps/catalogs/v1/controls/` holds three OSCAL Catalog Model JSON files:
`nist-ai-rmf.json`, `iso-42001-annex-a.json`, `eu-ai-act-articles.json`.
Each catalog is generated from a compact YAML source in
`gaps/catalogs/v1/controls/sources/` via
`scripts/build-oscal-catalogs.py`.

Specs reference OSCAL control ids in
`controlAssessment.controlImplementations[].controlId`.

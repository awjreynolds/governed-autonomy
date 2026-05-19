# Standards Substrates

GAPS v1 adopts three industry concepts.

## OSCAL - structural

GAPS v1 adopts the OSCAL Catalog Model and Assessment Plan shape for
evidence and control mappings. `controlAssessment.catalogRefs[]`
resolves to OSCAL Catalog files; `controlAssessment.controlImplementations[]`
follows OSCAL shape. The `gaps/catalogs/v1/controls/` directory ships
NIST AI RMF, ISO/IEC 42001 Annex A, and EU AI Act articles as OSCAL
catalogs.

Real interop: a v1 spec's `controlAssessment` is a subset OSCAL
assessment-plan and can be exported with mechanical translation.

## CMMN - conceptual

GAPS adopts CMMN's case-and-stage modeling concepts: each lane has a
state model with named states, milestones (terminal states), and
sentries (transition guards). The YAML names are GAPS-native; the
modeling shape is CMMN-equivalent.

## DMN - conceptual

GAPS adopts DMN's decision-table model for gates. Each gate's
`decision` block has typed `inputs`, a list of `rules` with `when`
expressions (FEEL subset) and `then` outcomes
(`approve | escalate | reject`), and an `else` clause.

## What GAPS does not adopt

- BPMN process flow notation (use the state model instead).
- Full FEEL grammar (the subset supports string equality, defined /
  undefined, comparison operators, and boolean combinators).
- OSCAL System Security Plan (controls and components are sufficient
  for v1).

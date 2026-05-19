# GAPS v1.0.0

GAPS is the Governed Autonomy Process Specification format. v1.0.0 is a
machine-validatable, machine-generatable profile for describing governed
processes that may include autonomous systems.

## What v1 changes

- **Controlled vocabularies.** Action ids, evidence kinds, and risk
  patterns are drawn from catalogs in `gaps/catalogs/v1/`. Two authors
  writing specs for the same process produce structurally comparable
  YAML.
- **Typed evidence.** Every evidence reference in a spec resolves to a
  typed `caseFileItems[]` entry with a shape.
- **Executable state and gates.** Each lane carries a state machine;
  each gate carries a decision table. The generator derives skill
  content from those structures.
- **OSCAL substrate.** Control mappings reference OSCAL catalog control
  ids (NIST AI RMF, ISO/IEC 42001 Annex A, EU AI Act). A spec's
  `controlAssessment` block is a subset OSCAL assessment-plan.
- **Conformance levels.** `descriptive` -> `machine-validatable` ->
  `generative`. The level the spec declares is the level the validator
  enforces.

## Pages

- [Format reference](format.md)
- [Catalogs](catalogs.md)
- [Substrates: OSCAL/CMMN/DMN](substrates.md)
- [Authoring guide](authoring-guide.md)
- [Generator](generator.md)
- [Round-trip](round-trip.md)
- [Migration from v0.1](migration-from-v0-1.md)

# Governed Autonomy

Governed Autonomy is a process-governance discipline for work that may include autonomous systems. It defines where autonomy can participate, which authority boundaries apply, what evidence must exist, when humans approve, and how accountable state is preserved.

This repository contains:

- `docs/governed-autonomy/` - the Governed Autonomy operating model and reference material.
- `gaps/` - the Governed Autonomy Process Specification profile.
- `gaps/schema/` - exploratory JSON Schemas for process specs and implementation maps.
- `gaps/examples/` - reference processes, currently GADD and compliance-review casework.
- `reference-packages/gadd/` - a fixture copy of the GADD skill package surfaces used to validate the GADD implementation map.
- `scripts/` - GAPS validation and generation tooling.
- `skills/` and `commands/` - GAPS authoring, validation, and generation skills.

GAPS is not a replacement for BPMN, CMMN, DMN, OSCAL, NIST AI RMF, ISO/IEC 42001, or the EU AI Act. It is an exploratory Governed Autonomy profile that should align with those standards where they already own the underlying concept.

## Quick start

Run the core validation suite:

```bash
./scripts/validate-governed-autonomy.sh
```

Run individual checks:

```bash
python3 scripts/validate-gaps.py
python3 scripts/validate-gaps-implementation.py
python3 -m unittest discover tests/gaps
```

Generate a reviewable skill package from a GAPS process:

```bash
python3 scripts/generate-gaps-skill-package.py gaps/examples/compliance-review/ga-process.yml
```

## Relationship to GADD

GADD is the first concrete SDLC implementation of Governed Autonomy. This repository keeps GADD as a reference process and includes fixture package surfaces for validation, but the GADD product and published SDLC skills remain in the `gadd` repository.

## License

MIT.

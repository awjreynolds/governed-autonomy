# Governed Autonomy

Governed Autonomy is a process-governance discipline for work that may include autonomous systems. It defines where autonomy can participate, which authority boundaries apply, what evidence must exist, when humans approve, and how accountable state is preserved.

This repository contains:

- `docs/governed-autonomy/` - the Governed Autonomy operating model and reference material.
- `gaps/` - the Governed Autonomy Process Specification profile.
- `gaps/schema/` - exploratory JSON Schemas for process specs and implementation maps.
- `gaps/examples/` - validated reference process specifications across software delivery, casework, incident response, and procurement.
- `reference-packages/` - fixture package surfaces used to validate implementation maps.
- `scripts/` - GAPS validation and generation tooling.
- `skills/` and `commands/` - GAPS authoring, validation, and generation skills.

GAPS is not a replacement for BPMN, CMMN, DMN, OSCAL, NIST AI RMF, ISO/IEC 42001, or the EU AI Act. It is an exploratory Governed Autonomy profile that should align with those standards where they already own the underlying concept.

GAPS v1.0.0 reference docs live at `docs/governed-autonomy/gaps/`.

## Website

The public documentation front door is:

https://awjreynolds.github.io/governed-autonomy/

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

Run the v1 validators (incubation):

```bash
python3 scripts/validate-catalogs.py
python3 scripts/validate-gaps-v1.py gaps/examples/v1/minimal/ga-process.v1.yml
```

Round-trip the v1 pilot spec:

```bash
python3 scripts/gaps-round-trip.py gaps/examples/v1/benefits-eligibility-review/ga-process.v1.yml
```

Generate a reviewable skill package from a GAPS process:

```bash
python3 scripts/generate-gaps-skill-package.py gaps/examples/compliance-review/ga-process.yml
```

## License

MIT.

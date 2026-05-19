# Governed Autonomy

Governed Autonomy is a process-governance discipline for work that may include autonomous systems. It defines where autonomy can participate, which authority boundaries apply, what evidence must exist, when humans approve, and how accountable state is preserved.

This repository contains:

- `docs/governed-autonomy/` - the Governed Autonomy operating model and reference material.
- `skills/governed-autonomy-author/` - dialog-driven authoring for governed skill sets.
- `skills/governed-autonomy-critique/` - read-only review of existing skills and process directories.
- `scripts/ga-lint` - deterministic linting for `governance.yml`.
- `gaps/` - internal GAPS v1 schema/catalog plumbing kept for optional spec projection.
- `reference-packages/` - fixture package surfaces used to validate implementation maps.
- `skills/` and `commands/` - Governed Autonomy authoring, critique, and lint command surfaces.

GAPS is not a replacement for BPMN, CMMN, DMN, OSCAL, NIST AI RMF, ISO/IEC 42001, or the EU AI Act. It is an exploratory Governed Autonomy profile that should align with those standards where they already own the underlying concept.

GAPS v1.0.0 reference docs live at `docs/governed-autonomy/gaps/` as internal plumbing for `--emit-spec`.

## Website

The public documentation front door is:

https://awjreynolds.github.io/governed-autonomy/

## Quick start

Author a governed skill set through the operating-model dialog:

```bash
/governed-autonomy:author
```

Review an existing skill set or process directory without modifying it:

```bash
/governed-autonomy:critique <path>
```

Lint an emitted governance sidecar:

```bash
scripts/ga-lint <process-dir>/governance.yml
scripts/ga-lint --json <process-dir>/governance.yml
```

Run the repository validation suite:

```bash
./scripts/validate-governed-autonomy.sh
python3 -m unittest discover tests/ga_lint
python3 -m unittest discover -s tests/gaps
```

## See also: GAPS v1 internals

GAPS v1 is no longer the user-facing authoring path. The schema, catalogs, and validator remain for audit-oriented projection from `/governed-autonomy:author --emit-spec`.

```bash
python3 scripts/validate-catalogs.py
python3 scripts/validate-gaps-v1.py gaps/examples/v1/gadd/ga-process.v1.yml
```

## License

MIT.

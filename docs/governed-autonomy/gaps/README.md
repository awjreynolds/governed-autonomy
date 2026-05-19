# GAPS v1 Internal Reference

GAPS v1 is internal plumbing for `/governed-autonomy:author --emit-spec`. The supported authoring path is the governed-autonomy dialog, which emits `governance.yml`, step skills, and `governance-validation.md`.

Kept reference material:

- `format.md` documents the retained v1 spec shape.
- `catalogs.md` documents the retained action, evidence, and risk catalogs.
- `substrates.md` documents standards-alignment context.

The validator remains available for spec projections:

```bash
python3 scripts/validate-gaps-v1.py gaps/examples/v1/gadd/ga-process.v1.yml
```

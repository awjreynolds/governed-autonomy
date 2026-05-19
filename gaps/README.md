# GAPS v1 Internals

The `gaps/` tree is retained as internal support for Governed Autonomy authoring:

- `schema/v1/` contains the optional `ga-process.v1.yml` projection schema.
- `catalogs/v1/` contains action, evidence, and risk vocabularies used as conversational suggestions by the author and critique skills and as deterministic inputs to `ga-lint`.
- `examples/v1/gadd/` and `examples/v1/incident-response/` are retained validator fixtures.

Human users should not hand-author GAPS specs. Use `/governed-autonomy:author`; pass `--emit-spec` only when an audit or compliance workflow needs a GAPS v1 projection.

Validate retained projections with:

```bash
python3 scripts/validate-gaps-v1.py gaps/examples/v1/gadd/ga-process.v1.yml
python3 scripts/validate-gaps-v1.py gaps/examples/v1/incident-response/ga-process.v1.yml
```

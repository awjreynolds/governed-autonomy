# GAPS v1 Generator

The generator produces a usable skill package from a
generative-conformance spec.

```bash
python3 scripts/generate-gaps-skill-package-v1.py <spec> [--output-root <dir>] [--validate-after]
```

## What it generates

Per lane:

- `skills/<process>-<lane>/SKILL.md` with sections derived from the spec:
  - Input Quality Gate - from `evidenceInputs[].shape.required`.
  - Rules - from `authority.allowedActions[]` / `prohibitedActions[]`,
    with catalog definitions inlined verbatim.
  - State Loop - a Markdown table of states and transitions.
  - Gates - Markdown decision tables.
  - Stop Conditions - from terminal states and escalating gates.
  - Evidence To Produce - from `evidenceOutputs[]`.
- `skills/<process>-<lane>/agents/openai.yaml` - Codex skill metadata.
- `commands/<process>/<lane>.md` and `.toml` - command adapters.

Plus:

- `agent-skills.json`, `.claude-plugin/plugin.json`, `gemini-extension.json`.
- `implementation.v1.yml` - binds the spec to the generated package with
  a content-hash fingerprint.

## Determinism

The generator output is byte-identical for unchanged input. Run with
`--check` against an existing output to detect drift.

## Do not edit by hand

Every generated file carries a header marker. To change skill content,
edit the spec and regenerate.

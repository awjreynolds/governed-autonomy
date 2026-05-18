---
layout: page
title: Quickstart
---

# Quickstart

Clone the repository:

```bash
git clone https://github.com/awjreynolds/governed-autonomy.git
cd governed-autonomy
```

Run the full validation suite:

```bash
./scripts/validate-governed-autonomy.sh
```

Run individual checks:

```bash
python3 scripts/validate-gaps.py
python3 scripts/validate-gaps-implementation.py
python3 -m unittest discover tests/gaps
```

Generate a reviewable skill-package skeleton from a GAPS process:

```bash
python3 scripts/generate-gaps-skill-package.py gaps/examples/compliance-review/ga-process.yml
```

The generator writes preview artifacts under `gaps/generated/<process-id-slug>/` by default. Generated output is a starting point for human process-owner review. It is not production-ready by default and does not claim regulatory compliance, certification, legal sufficiency, runtime execution, or standards export.

## Authoring flow

1. Start from an existing process, not a desired automation.
2. Name the accountable roles and the canonical state source.
3. Define lanes, authority boundaries, gates, evidence, and escalation conditions.
4. Map relevant risk patterns and external control anchors.
5. Run validation.
6. Only then generate reviewable skills or adapters.

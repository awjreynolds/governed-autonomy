---
name: gaps-lift
description: Reverse-lift a generated GAPS v1 skill package into a structural spec representation.
command: /gaps:lift
---

# GAPS Lift

Lift a generated v1 skill package back into a structural spec representation. Use this skill when:

- You want to verify a generated package against its source spec.
- You inherited a generated package and need to recover its spec surface.
- You want to feed the round-trip command (`/gaps:round-trip`) which depends on lift.

## Input Quality Gate

- The package root contains `implementation.v1.yml` produced by `gaps-v1-generator`.
- The package's `SKILL.md` files are unmodified since generation.

## Rules

- Read `implementation.v1.yml` first; refuse to lift packages without it.
- Do not invent missing fields. The lift surface is structural - labels and prose remain in the spec, not in the lift.
- Output is YAML with `liftVersion`, `packageRoot`, `fingerprint`, `implementation`, and `lanes`.

## Stop Conditions

- The package is missing `implementation.v1.yml`.
- The package's `generatedBy` is not `gaps-v1-generator`. Manual lift of hand-authored packages is a future enhancement.

## How to run

```bash
python3 scripts/gaps-lift.py <package-root>
```

Pass `--out <path.yml>` to write to a file instead of stdout.

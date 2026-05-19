---
name: gaps-round-trip
description: Verify a GAPS v1 spec round-trips through the generator and lift.
command: /gaps:round-trip
---

# GAPS Round-trip

Run `generate -> lift -> diff` on a generative-conformance v1 spec. Round-trip is the v1.0.0 acceptance test: a spec that round-trips is provably sufficient to drive skill generation without human content authoring.

## Input Quality Gate

- The spec is at `conformanceLevel: generative` or stricter.
- The spec validates against the v1 schema and semantic rules.
- All catalogs referenced in `substrate.*` are reachable.

## Rules

- The diff is structural: lane ids, state ids, transition ids, gate ids, evidence ids, and fingerprint expectations. Free-text differences do not fail the round-trip.
- A non-empty diff is a hard fail. Investigate before merging the spec.

## Stop Conditions

- Generator refuses the spec (not generative).
- Lift cannot recover the package (missing `implementation.v1.yml`).
- Diff produces issues.

## How to run

```bash
python3 scripts/gaps-round-trip.py <spec>
```

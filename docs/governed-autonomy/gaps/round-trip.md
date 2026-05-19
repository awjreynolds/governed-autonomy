# Round-trip

The round-trip discipline is the v1.0.0 acceptance test for
generative-conformance specs.

```bash
python3 scripts/gaps-round-trip.py <spec>
```

The command runs:

1. Generate the skill package into a temporary directory
   (`--validate-after` ensures the spec is generative).
2. Lift the package back into a structural representation.
3. Diff the spec's skeleton against the lifted skeleton.

The diff is structural: lane ids, state ids, transition ids, gate ids,
evidence ids. Free-text differences are not part of the round-trip.

A non-empty diff is a hard fail. The most common causes:

- A generator change that drops information without a spec update.
- A spec edit that doesn't get reflected in the generator's output
  (e.g., a new evidence item whose binding the generator forgot to
  include in `implementation.v1.yml`).

CI invokes the round-trip on the pilot reference spec; extend this to
every generative-conformance spec the project ships.

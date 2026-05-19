# Migrating a v0.1 Spec to v1

## Run the migrator

```bash
python3 scripts/migrate-gaps-v0-to-v1.py gaps/examples/<process>/ga-process.yml
```

Output: `gaps/examples/<process>/ga-process.v1.yml` at
`conformanceLevel: descriptive`.

## Review the output

- `roles[].accountabilityScope` will be a TODO placeholder. Fill it in.
- `process.localActions[]` will contain unmatched v0.1 free-text values.
  For each, either map to an existing universal action and remove the
  local extension, or keep the local action with a real definition and
  justification.
- `evidenceModel.caseFileItems[]` will contain a single migrated
  placeholder. Add real evidence items derived from the v0.1 spec's
  evidence structure.
- `controlAssessment.controlImplementations[]` will have minimal
  statements. Expand them.
- Revisit every `knownGaps[]` entry. The migrator marks the migration
  itself as a known gap; remove it once you've reviewed.

## Promote deliberately

The migrator output is descriptive. Promote to `machine-validatable`
and then `generative` only when the spec actually meets the higher
level's requirements (see the
[authoring guide](authoring-guide.md)).

## When the v0.1 spec was hand-rich

If the v0.1 spec already had detailed `approvalCondition` and
`escalationCondition` text on every gate, the migrator preserves it
verbatim. That accelerates the promotion to `machine-validatable` -
most of the text is already in place.

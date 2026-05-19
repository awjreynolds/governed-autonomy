# Authoring a GAPS v1 Spec

## Start with `descriptive`

Author the structural surface first. Use the four reference specs in
`gaps/examples/v1/` as templates.

1. `process` block - id, name, purpose, scope includes/excludes.
2. `substrate` block - point at the v1 catalog paths.
3. `roles[]` - name the human roles. Capture `accountabilityScope`
   honestly: what does this role own?
4. `evidenceModel.caseFileItems[]` - list every artifact, attestation,
   observation, or decision record the process produces or consumes.
   Reference an evidence-kind catalog id.
5. `lanes[]` - one per phase of work. Set authority `plane`,
   `autonomyTier`, `riskTier`. Pick `allowedActions` and
   `prohibitedActions` from the action catalog.
6. `gates[]` - name each governed approval boundary. Set `gateType`,
   `approvalRole`, and text for `approvalCondition` /
   `escalationCondition`.
7. `projectionPolicy` - declare canonical state source and external
   systems with `mutationRequiresApproval`.
8. `riskPatterns[]` - reference relevant patterns and explain
   mitigations.
9. `controlAssessment` - list at least one OSCAL control id and its
   implementation status.
10. `knownGaps[]` - be honest about what's not done.

Validate: `python3 scripts/validate-gaps-v1.py <spec>`.

## Promote to `machine-validatable`

Fill in:

- Every lane's `allowedActions` and `prohibitedActions`.
- Every gate's `approvalCondition` and `escalationCondition`.

Re-validate.

## Promote to `generative`

Fill in:

- Every lane's `stateModel.states[]` and `stateModel.transitions[]`,
  with `isInitial`/`isTerminal` flags. Every transition needs a
  `guard` with typed inputs and rules.
- Every blocking gate's `decision` block with typed inputs and
  decision rules.
- Every `caseFileItems[]` entry referenced as a lane input needs
  `shape.required[]`.

Re-validate. Then round-trip: `python3 scripts/gaps-round-trip.py <spec>`.

## Anti-patterns to watch for

- Free-text fields where a catalog id would do.
- Generic mitigations like "follow best practice" instead of a concrete
  evidence-kind reference.
- A `controlAssessment.controlImplementations[]` entry with
  `mappingStatus: implemented` and no `implementedBy` block.
- A lane whose `prohibitedActions` is empty. Every autonomous lane has
  things it must not do.

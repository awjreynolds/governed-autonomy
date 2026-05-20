# GADD Parity Harness Design

## Context

Governed Autonomy can now emit and validate governed skill sets. The next question is sharper: can a generated governed skill set produce the same useful outcomes as the handcrafted GADD skills?

The sibling GADD repository at `/Users/awjre/Work/gadd` should be treated as the oracle for this question. It already contains the handcrafted `skills/gadd-*` package, generated-package validation, command-surface contracts, Level 1 ledger fixtures, Level 2 offline routing checks, and Level 3 scripted agent scenarios. Governed Autonomy should not invent a new definition of GADD correctness while that repo already has one.

The target is behavioral parity, not prose identity. Byte-for-byte equality is useful for deterministic templates and manifests. It is the wrong default for human-facing Markdown artifacts where generated prose can differ while preserving the same governance outcome.

## Goals

1. Prove that a GA-authored GADD package emits the same command surface as handcrafted GADD.
2. Prove that generated skills preserve GADD's required behavioral obligations.
3. Reuse GADD's existing deterministic harnesses where possible.
4. Keep normal Governed Autonomy CI self-contained.
5. Make cross-repo parity opt-in through an environment variable.

## Non-Goals

- Do not require byte-for-byte equality for all generated Markdown.
- Do not make this repository's default tests depend on a sibling checkout.
- Do not run live GitHub Level 2 or Level 3 tests by default.
- Do not replace GADD's own validation harness.
- Do not claim legal, regulatory, certification, or executable correctness.

## Parity Levels

Parity should be checked in layers.

1. **Manifest parity**
   - Same `/gadd:*` command set.
   - Same command-to-skill mapping.
   - Same command adapter files.
   - Same expected package metadata.

2. **Skill contract parity**
   - Each generated skill has frontmatter, a matching command heading, command mapping, and required sections.
   - Each generated skill includes required behavioral phrases or equivalent obligations from the handcrafted skill.
   - The checker should prefer section-level requirements over raw substring checks when the structure is stable.

3. **Structured state parity**
   - Ledgers are compared after normalization.
   - Normalize timestamps, generated run ids, external URLs, branch names, PR numbers, and commit hashes.
   - Compare durable fields such as `work_item.state`, `artifacts.*.status`, `approved_artifacts`, `closure.status`, `execution_context.current_gate`, `execution_context.next_command`, and `execution_context.next_human_action`.

4. **Artifact contract parity**
   - PRD, SDD, plan, issue bodies, PR bodies, and verification reports must contain required headings and traceability fields.
   - Byte equality is allowed only for deterministic templates copied verbatim by setup.
   - Markdown quality should be checked by required sections and trace markers, not exact prose.

5. **Workflow parity**
   - The same fixture state should route to the same next command or blocking condition.
   - Missing approval, missing verification, terminal triage, stale state, and closure readiness should resolve the same way.

## Proposed Architecture

Add a parity layer in this repository with two modes.

```
tests/gadd_parity/
├── fixtures/
│   ├── expected-commands.yml
│   ├── required-skill-contracts.yml
│   └── normalization.yml
├── test_gadd_contract_parity.py
└── test_gadd_optional_cross_repo.py
```

### Default Mode

Default tests run without `/Users/awjre/Work/gadd`.

They validate checked-in GA-side fixtures and contracts:

- `reference-packages/gadd` has the expected command set.
- generated or governed GADD fixtures have 15 skills when present.
- required command obligations are present.
- `ga-lint` still validates any governed GADD sidecar added later.

This mode protects this repository from drift without importing the sibling repo into CI.

### Cross-Repo Mode

Cross-repo tests run only when `GADD_REPO_PATH` is set.

Example:

```sh
GADD_REPO_PATH=/Users/awjre/Work/gadd python3 -m unittest discover tests/gadd_parity
```

The test should:

1. Confirm `GADD_REPO_PATH` points to a clean GADD checkout.
2. Run GADD's generated-package validator where available:
   - `python3 scripts/validate-generated-gadd-package.py`
3. Read GADD's own expected command contracts.
4. Compare GA-side generated or reference packages against those contracts.
5. Optionally run GADD Level 2 offline and Level 3 scripted scenarios with a generated package root.

Live GitHub checks remain outside this repo's default harness.

## First PR

The first implementation should be narrow.

Add contract parity only:

- expected `/gadd:*` command list;
- manifest and command adapter checks;
- required skill section checks;
- required behavioral obligation checks for the highest-risk commands:
  - `/gadd:next`
  - `/gadd:approve`
  - `/gadd:implement`
  - `/gadd:verify`
  - `/gadd:close`

No agent execution. No sibling checkout requirement. No live GitHub calls.

## Second PR

Add optional cross-repo verification:

- use `GADD_REPO_PATH`;
- run GADD's `validate-generated-gadd-package.py`;
- import or mirror the GADD command contract expectations;
- skip cleanly when the environment variable is absent.

This proves Governed Autonomy aligns with the current GADD oracle without forcing every developer to keep the sibling checkout.

## Third PR

Add structured fixture output parity:

- copy a small, curated subset of GADD Level 1 fixture states;
- normalize volatile fields;
- compare ledgers and artifact contracts;
- start with three scenarios:
  - product feature happy path;
  - engineering change happy path;
  - missing approval blocked.

This is the point where generated skills begin proving durable output parity, not only command-surface parity.

## Risks

**False confidence from shallow phrase checks.** Phrase checks should be treated as an initial guard. They must move toward structured sections and scenario outputs.

**Brittle snapshots.** Avoid full Markdown snapshots except for deterministic setup templates.

**Cross-repo drift.** The optional harness should report the GADD commit hash it used. If GADD changes, failures should point to the contract difference rather than hiding behind generic diffs.

**Conflating GADD and GA.** GADD remains the upstream oracle for GADD behavior. Governed Autonomy owns the generic authoring, linting, enforcement, and parity harness.

## Acceptance Criteria

- Default parity tests run without a sibling GADD checkout.
- Optional parity tests use `GADD_REPO_PATH` and skip cleanly when it is unset.
- The first PR proves command-surface and skill-contract parity for the high-risk GADD commands.
- Later PRs prove structured state and artifact parity against curated GADD fixtures.
- Documentation states clearly that full byte-for-byte Markdown equality is not the target.

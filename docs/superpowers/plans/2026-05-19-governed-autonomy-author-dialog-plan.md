# Governed Autonomy Author Dialog — Implementation Plan

## Context

GAPS v1.0.0 shipped on 2026-05-19 with ~6,200 lines of Python tooling (validator, generator, migrator, lift, round-trip), five user-facing skills, and a 368-line schema requiring 14 top-level fields. The artifact users were asked to hand-author (`ga-process.v1.yml`) is the wrong shape for the actual job-to-be-done: helping humans design workflow skills that embody governed-autonomy principles. A passing GAPS spec proves YAML matches a schema; it does not prove the process is well-governed.

The design at `docs/superpowers/specs/2026-05-19-governed-autonomy-author-dialog-design.md` (5 review rounds, latest commit `f6bd1bc`) replaces hand-authored YAML with a brainstorming-style dialog. The operating model becomes the question set. Catalogs become conversational content. GAPS v1 schema is demoted to internal plumbing for an opt-in `--emit-spec` flag. Most v1 tooling is decommissioned.

This plan sequences the implementation. The CTO wants it delivered quickly; the spec is precise about WHAT; this plan is HOW.

## Approach

Five sequential phases. The spec mandates critique-first sequencing (its "smallest useful next experiment" section): the critique skill validates the operating-model question set on real material *before* the author skill is built on the same questions. The Stage 2 acceptance checkpoint between Phases 3 and 4 gates all decommissioning.

### Phase 0 — Author phase exemplars

The exemplars are the testable spine. Without them, both downstream skills have no acceptance criteria.

Write one accept-exemplar and one reject-exemplar per operating-model phase (Phases 1–10; Phase 11 is emit). Each exemplar specifies: the user's stated answer, the probes the dialog must fire, the ground-truth dialog outcome (accept / quality-refusal / mechanical-refusal).

**Files:**
- `docs/governed-autonomy/phase-exemplars/phase-01-process-identity.md` through `phase-10-per-step-narrowing.md`

**Acceptance:** Every phase the spec marks **hard refuse** (2, 3, 6, 7) has at least one mechanical-refusal reject-exemplar AND one quality-refusal reject-exemplar. Other phases have at least one quality-refusal reject-exemplar.

### Phase 1 — `ga-lint` deterministic CLI

Build the lint tool first. Both downstream LLM skills depend on it (critique uses it as baseline; author runs it post-emit). It depends on nothing.

**Files to create:**
- `scripts/ga_lint/__init__.py`
- `scripts/ga_lint/loader.py` — lift verbatim from `scripts/gaps_v1_validator/loader.py` (42 lines, fully generic — Ruby YAML bridge + JSON loader + repo-root path resolver)
- `scripts/ga_lint/errors.py` — lift from `scripts/gaps_v1_validator/errors.py` (34 lines: `ValidationIssue`, `ValidationReport`), then extend `ValidationIssue` with a `severity: Literal["error","warning"]` field
- `scripts/ga_lint/catalog.py` — loads `gaps/catalogs/v1/actions.yml`, `evidence-kinds.yml`, `risk-patterns.yml`. Exposes catalog-id → category lookup (needed for E011)
- `scripts/ga_lint/merge.py` — single helper implementing the step-authority merge: `allowed_actions` replaces, `prohibited_actions` unions. The one piece of load-bearing logic in lint
- `scripts/ga_lint/rules.py` — one function per rule, E001–E014 + W001–W005, W007–W010 (W006 was deleted in round 4). Each rule takes loaded `governance.yml` dict + skills directory listing, returns `list[ValidationIssue]`. Autonomy tier lattice as a module constant
- `scripts/ga_lint/discovery.py` — walks up from cwd for `governance.yml`; falls back to `find . -maxdepth 4 -name governance.yml`; errors on zero or multiple
- `scripts/ga_lint/cli.py` — argparse: optional positional path, `--json`, exit codes
- `scripts/ga-lint` — shebang shim invoking `python3 -m scripts.ga_lint.cli "$@"`

**Tests:**
- `tests/ga_lint/test_rules.py` — one positive + one negative fixture per rule
- `tests/ga_lint/fixtures/<rule_id>/governance.yml` — minimal triggering / non-triggering files
- `tests/ga_lint/test_merge.py` — exhaustive table-driven test for step-authority merge semantics
- `tests/ga_lint/test_cli.py` — exit codes, `--json` shape, discovery behavior
- Invocation: `python3 -m unittest discover tests/ga_lint`

**Acceptance gate:**
- All rule tests pass
- `ga-lint` runs <1 s on three reference `governance.yml` files (hand-crafted comprehensive, GADD-derived, malformed)
- `ga-lint --json` produces valid JSON

### Phase 2 — `governed-autonomy:critique` skill (the de-risk)

Validates whether the operating-model question set produces useful findings on real material. Failure means rethink, not refactor.

**Files to create:**
- `skills/governed-autonomy-critique/SKILL.md` — single file, sections covering: input shapes (single skill / skill set / process dir / no-governance dir), operating-model concerns 1–9 as the review structure, findings taxonomy (blocking/significant/advisory), `ga-lint` baseline integration, output (only `governance-review.md` in target dir, no edits to reviewed artifact), citation requirement
- `skills/governed-autonomy-critique/agents/openai.yaml` — 8-line interface + policy, modeled on `skills/gaps-author/agents/openai.yaml`
- `commands/governed-autonomy/critique.md` — router stub mirroring `commands/gaps/author.md`
- `commands/governed-autonomy/critique.toml` — `description` + `prompt` with `{{args}}` mirroring `commands/gaps/author.toml`
- `docs/governed-autonomy/critique.md`
- `docs/governed-autonomy/lint.md`

**Manifest updates:**
- Add `/governed-autonomy:critique` entry to `agent-skills.json` `commands[]` array
- Add `/governed-autonomy:critique` to `gemini-extension.json` `commands[]` array

**Tests (golden fixtures — the critical project gate):**
- `tests/critique/fixtures/v1-gadd/` — copy of `gaps/examples/v1/gadd/`
- `tests/critique/fixtures/reference-gadd/` — copy of `reference-packages/gadd/`
- `tests/critique/fixtures/external-skill/` — one external skill vendored as a fixture
- Each fixture gets a hand-authored `governance-review.md.expected` containing `{finding_id, severity, op_model_section}` ground truth
- `tests/critique/score_findings.py` — parses both review files, computes finding-id-match-with-correct-severity rate

**Acceptance gate:**
- For each fixture: ≥80% of ground-truth findings appear in critique output with correct severity tier
- All findings cite an operating-model section
- Critique never modifies the reviewed artifact

**If gate fails on all three:** Stop. Question set is broken. Return to design. The spec explicitly anticipates this branch. Cost of stopping here is one skill + three fixtures; cost of catching it later is the whole author skill.

### Phase 3 — `governed-autonomy:author` skill

Critique has now validated the question set. Author is critique-in-reverse.

**Files to create:**
- `skills/governed-autonomy-author/SKILL.md` — single file with progressive disclosure: frontmatter; input-mode detection (cold/notes/retrofit/revision); Phase 1–11 sections each with primary question + probes + accept/reject criteria referencing the Phase 0 exemplars; grill-me loop spec; refusal model (mechanical vs quality); `--quick` flag; help & research modes (provider-agnostic external); emit phase writing `governance.yml` + per-step `SKILL.md` + `governance-validation.md`; `--emit-spec` flag handling that writes `<process-dir>/ga-process.v1.yml` via the kept `gaps_v1_validator`; state-persistence is in-conversation only (non-negotiable per spec)
- `skills/governed-autonomy-author/agents/openai.yaml`
- `commands/governed-autonomy/author.md` + `.toml`
- `commands/governed-autonomy/lint.md` + `.toml` (lint also gets a slash command for parity)
- `docs/governed-autonomy/authoring-dialog.md`
- `docs/governed-autonomy/governance-sidecar.md`

**Manifest updates:**
- Add `/governed-autonomy:author` and `/governed-autonomy:lint` to `agent-skills.json` and `gemini-extension.json`
- README updated to lead with `/governed-autonomy:author` and `/governed-autonomy:critique`; GAPS moves to "see also" section
- **Demote (not delete) GAPS surfaces:** remove `gaps-*` command entries from `agent-skills.json` and `gemini-extension.json` `commands[]` arrays. Leave `commands/gaps/*.toml` and `skills/gaps-*/` directories on disk; they no longer route

**Tests:**
- `tests/author/fixtures/cold-start/transcript.md` — scripted user inputs; expected `governance.yml` committed
- `tests/author/fixtures/retrofit-gadd/` — input: one existing GADD skill from `reference-packages/gadd/`; expected: a `governance.yml` that merges with the rest of GADD
- `tests/author/fixtures/phase-exemplars/` — one fixture per Phase 0 accept-exemplar and one per reject-exemplar
- `tests/author/run_phase_exemplars.py` — orchestrator driving the author skill with each exemplar's scripted inputs, asserting expected dialog terminal state

**Stage 2 acceptance gate (the all-of):**
1. Cold-start fixture: `governance.yml` passes `ga-lint` with zero errors
2. Retrofit fixture: `governance.yml` passes `ga-lint` with zero errors
3. Every accept-exemplar produces accept; every reject-exemplar produces quality-refusal (or mechanical-refusal where applicable)
4. Phase 2 golden critique fixtures still pass at ≥80%
5. `ga-lint` runs <1 s on all generated artifacts
6. README updated; GAPS commands demoted from manifests
7. Full test suite green: `python3 -m unittest discover tests/`

**Nothing in Phase 4 starts until all 7 conditions hold simultaneously.**

### Phase 4 — Stage 3 decommissioning (only after Phase 3 gate passes)

Pure removal. The full delete list is in the spec's Stage 3 section; key paths:

**Skills (delete entire directories):**
- `skills/gaps-author/`, `skills/gaps-validate/`, `skills/gaps-generate/`, `skills/gaps-lift/`, `skills/gaps-round-trip/`

**Commands (delete entire directory):**
- `commands/gaps/` (5 `.md` + 5 `.toml`)

**Scripts:**
- `scripts/gaps-lift.py`, `gaps-round-trip.py`, `migrate-gaps-v0-to-v1.py`
- `scripts/generate-gaps-skill-package.py`, `generate-gaps-skill-package-v1.py`
- `scripts/validate-gaps.py`, `validate-gaps-implementation.py`
- `scripts/gaps_v1_lift/`, `scripts/gaps_v1_migrator/`, `scripts/gaps_v1_generator/` (entire packages)

**Keep (the `--emit-spec` plumbing):** `scripts/gaps_v1_validator/`, `scripts/validate-gaps-v1.py`, `gaps/schema/v1/`, `gaps/catalogs/v1/`

**Tests consequent on script removal:**
- `tests/gaps/test_validate_gaps.py`, `test_generate_gaps_skill_package.py`, `test_validate_gaps_implementation.py` — delete
- `tests/gaps/fixtures/` — audit; delete orphaned, keep what `validate-gaps-v1` tests still need
- `scripts/validate-governed-autonomy.sh` — rewrite to invoke v1 validator + `ga-lint` + new test trees

**Docs:**
- `docs/governed-autonomy/gaps/authoring-guide.md`, `generator.md`, `round-trip.md`, `migration-from-v0-1.md` — delete
- `docs/governed-autonomy/gaps/README.md` — trim to one paragraph: "GAPS v1 schema is internal plumbing for `--emit-spec`"
- `docs/governed-autonomy/gaps/format.md`, `substrates.md`, `catalogs.md` — keep as reference

**Examples:**
- Delete v0: `gaps/examples/incident-response/`, `procurement-approval/`, `compliance-review/`, `gadd/`
- Delete five v1: `gaps/examples/v1/minimal/`, `comprehensive/`, `benefits-eligibility-review/`, `procurement-approval/`, `compliance-review/`
- Keep two v1: `gaps/examples/v1/gadd/`, `gaps/examples/v1/incident-response/`

**Acceptance gate:**
- Full test suite green
- `python3 scripts/validate-gaps-v1.py gaps/examples/v1/gadd/ga-process.v1.yml` passes
- `git grep -l "gaps-author\|gaps-validate\|gaps-generate\|gaps-lift\|gaps-round-trip\|gaps-lift\.py\|gaps-round-trip\.py\|generate-gaps-skill-package\|validate-gaps\.py\|validate-gaps-implementation\|gaps_v1_lift\|gaps_v1_migrator\|gaps_v1_generator\|migrate-gaps-v0-to-v1"` returns nothing — no dangling references

### Phase 5 — Maintenance posture and walkthrough

- Update `CHANGELOG.md` with the cutover entry
- Final manual walkthrough of the cold-start dialog by a non-author user, on a real process. This is the ultimate acceptance: does the dialog deliver authoring rigor as a felt experience, not just as a passing test suite?

## Critical files

**Reused (lift into ga_lint):**
- `scripts/gaps_v1_validator/loader.py` — verbatim
- `scripts/gaps_v1_validator/errors.py` — extend `ValidationIssue` with `severity`

**New (must read carefully when implementing):**
- `scripts/ga_lint/rules.py` — the single place lint logic lives
- `scripts/ga_lint/merge.py` — step-authority merge; load-bearing
- `skills/governed-autonomy-author/SKILL.md` — the dialog itself; this is where most of the design's correctness has to be encoded as prompt
- `skills/governed-autonomy-critique/SKILL.md` — the de-risk skill
- `docs/governed-autonomy/phase-exemplars/*.md` — the test contract

**Manifest entry points (must be updated atomically with skill additions):**
- `agent-skills.json` — `commands[]` array
- `gemini-extension.json` — `commands[]` array
- `README.md` — Quick start

## Resolved open questions

The spec listed five open questions; this plan resolves them:

1. **Author skill file structure** — single `SKILL.md`. Sub-files only if Phase 3 proves it won't fit.
2. **`governance-validation.md` git default** — committed by default; it's authoring evidence.
3. **`--emit-spec` location** — `<process-dir>/ga-process.v1.yml` next to `governance.yml`.
4. **`ga-lint` discovery without argument** — walk upward from cwd; fallback `find . -maxdepth 4`; error on zero or multiple.
5. **Phase exemplar test harness** — scripted user-input transcripts + assertion of dialog terminal state. `tests/author/run_phase_exemplars.py` drives them.

## Verification

End-to-end verification after Phase 4:

```bash
# Lint runs clean and fast on the canonical fixtures
python3 -m unittest discover tests/ga_lint
time scripts/ga-lint tests/critique/fixtures/v1-gadd/governance.yml

# Critique produces matching findings on golden fixtures
python3 tests/critique/score_findings.py tests/critique/fixtures/v1-gadd
python3 tests/critique/score_findings.py tests/critique/fixtures/reference-gadd
python3 tests/critique/score_findings.py tests/critique/fixtures/external-skill

# Author phase exemplars produce expected dialog outcomes
python3 tests/author/run_phase_exemplars.py

# Full test suite
python3 -m unittest discover tests/

# GAPS plumbing still functional for --emit-spec
python3 scripts/validate-gaps-v1.py gaps/examples/v1/gadd/ga-process.v1.yml

# No dangling references to deleted modules
git grep -l "gaps-lift\|gaps-round-trip\|generate-gaps-skill-package\|gaps_v1_lift\|gaps_v1_migrator\|gaps_v1_generator\|migrate-gaps-v0-to-v1"

# Manual walkthrough of cold-start dialog on a real process
# (See Phase 5)
```

## Risks

| Risk | Trigger | Action |
|---|---|---|
| Question set wrong | Phase 2 fails <80% across all three fixtures | Stop. Return to design. Spec anticipates this branch. |
| Author skill too brittle | Phase 3 cold-start loops or hallucinates | Add explicit accept/reject decision rules to SKILL.md from Phase 0 exemplars. If still brittle, consider per-phase sub-files. |
| Lint false positive blocks author | Author writes valid `governance.yml`, lint rejects | Bug in a lint rule. Fix the rule; don't relax the schema. |
| Author omits `local_definitions.category` | `E003b` fires post-emit | Author SKILL.md must prompt for category whenever it introduces a local action. |
| State loss mid-session | User interrupts a long authoring session | Spec deferred this; author offers opt-in `governance-draft.md` dump. Don't try to make it resumable in v1. |
| External web search unavailable | Host agent has no search tool | Dialog says so and falls back to brainstorm or local research. No hard dependency. |
| Catalog drift between author and critique | Both load catalogs separately | Single source of truth: `gaps/catalogs/v1/*.yml`. Both skills and `ga_lint/catalog.py` reference the same paths. |
| Dangling reference after deletion | Phase 4 grep check fails | Run `git grep` before deletion; fix references first; then delete. |

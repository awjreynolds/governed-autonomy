# Governed Autonomy Authoring Dialog

`/governed-autonomy:author` creates, retrofits, or revises governed skill sets. It is a dialog, not a YAML generator. The operating model supplies the questions; the author skill probes until the answers are load-bearing.

The emitted process directory contains:

```text
<process-id>/
├── governance.yml
├── governance-validation.md
└── skills/
    └── <step-id>/SKILL.md
```

An optional command adapter may be emitted when the governed process has an orchestrator command. With `--emit-spec`, the author also writes `<process-dir>/ga-process.v1.yml` for internal GAPS v1 validation.

## Input Modes

- Cold start: `/governed-autonomy:author`
- Notes: `/governed-autonomy:author path/to/notes.md`
- Retrofit: `/governed-autonomy:author path/to/SKILL.md`
- Revision: `/governed-autonomy:author path/to/process-dir`

Revision is not a separate surface. It is authoring with prefilled answers from `governance.yml`.

## Dialog Phases

The dialog has eleven phases:

1. process identity;
2. roles and accountability;
3. authority;
4. input quality gates;
5. risk and blast radius;
6. evidence and destination;
7. escalation and approval;
8. state and projection;
9. decomposition into steps;
10. per-step narrowing;
11. emit.

Phases 2, 3, 6, and 7 are hard-refusal phases because their missing fields collapse the operating model: no accountable human owner, no explicit authority boundary, no evidence destination, or no escalation path.

## Grill-Me Loop

Each phase asks a primary question, probes the answer, cross-checks it against earlier answers, and accepts only when it survives. `--quick` reduces probing to one follow-up per phase and is intended for focused revisions or trivial processes.

When the user gets stuck, the author can offer:

- brainstorm mode, for candidate answers and tradeoffs;
- local research, for repository docs and prior governance files;
- external research, using whatever web search the host agent provides.

Research sources and accepted claims are recorded in `governance-validation.md`.

## Refusal

Mechanical refusal means a required core field is empty. Quality refusal means the field is populated but fails probing, such as an "engineering team" accountability claim with no paging route or handoff.

Core quality refusal blocks emit. Non-core contradictions become warnings or known gaps and are emitted with the process.

## Emit

Phase 11 writes `governance.yml`, per-step `SKILL.md` files, and `governance-validation.md`. The author then runs `ga-lint` when available. Lint errors after emit are treated as authoring defects, not user success. Lint warnings are persisted into `warnings:`.

State is conversation-only until emit. Abandoning the conversation loses the authoring state unless the user explicitly asks for a draft note.

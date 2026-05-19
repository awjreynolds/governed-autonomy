# Phase 6 — Evidence and destination

Operating model section: §6 (Evidence requirements) and §8 (State and auditability).

## What the dialog is doing

Phase 6 establishes what evidence the process produces, who consumes it, and where the canonical record lives. Evidence captured-but-unread is theatre. Evidence with no destination cannot be audited.

**This phase is hard-refuse.** No evidence destination → stop.

## Accept exemplar

**Ground-truth dialog outcome:** accept

**User stated answer:**

> "Evidence lives in the repo — design records as markdown in `docs/decisions/`, verification records as the PR's CI artifacts plus a posted comment summary. The design record is produced by the design step and consumed by tech_lead at the pre-merge gate. The verification record is produced by the implement step and consumed by tech_lead at the same gate. Retention: indefinitely in git history. We don't have a separate ledger — the PR thread is the canonical record for this process, with Linear and Slack as projections."

**Probes the dialog must fire:**

- "Who reads the design record? When? What decision do they make from it?"
- "If a verification record is captured but nobody looks at it before the gate, is the gate doing any work?"
- "Where does this record live in a year? Five years? Is it still readable?"

**Why this passes:**

Destination is concrete (repo, PR thread). Each evidence item has a named producer (step) and a named consumer (role). The consumer makes a real decision from it (gate decision). Retention is named. Canonical vs projection distinction is explicit (PR thread is canonical; Linear/Slack are projections, not source of truth).

## Reject exemplar 1 (mechanical refusal)

**Ground-truth dialog outcome:** mechanical-refusal

**User stated answer:**

> "We should capture evidence, but I don't know what it is yet or where it should live."

**Probes the dialog must fire:**

- "Name one evidence item this process produces."
- "Where is that evidence stored as the durable record?"
- "Who consumes that evidence, and what decision do they make from it?"

**Why this fails (mechanical refusal):**

The user acknowledges the phase but gives no evidence item and no destination. The core-set field `evidence.destination` is empty and `evidence.items` cannot be populated. Hard stop.

The dialog explains: "Operating model §8: important process state should not live only in chat. What evidence items will exist after this process runs, and where will they be reachable later?"

## Reject exemplar 2 (quality refusal)

**Ground-truth dialog outcome:** quality-refusal

**User stated answer:**

> "We log everything to a directory called `process-logs/`. Producer: the agent. Consumer: nobody specifically, just whoever's curious later."

**Probes the dialog must fire:**

- "If nobody consumes the evidence, why are you capturing it?"
- "What decision is made from this evidence? By whom? When?"
- "Is 'whoever's curious' actually anyone? Has anyone ever read these logs?"

**Why this fails (quality refusal):**

Evidence is named and has a destination. But the probes establish that the consumer is not real — nobody is paged or required to read these logs. Evidence-without-consumer is the classic "we log it just in case" anti-pattern that produces noise without governance.

The dialog records quality-refusal and offers help:

- Brainstorm: who in the existing roles would benefit from reading each evidence item, and at what decision point
- Local research: who consumes evidence in the existing GADD reference package
- External research: common evidence patterns for SDLC governance (PR thread, deploy log, RCA doc)

## Test assertion

```yaml
phase: 6
hard_refuse: true

accept:
  user_inputs:
    - |
      Evidence lives in the repo — design records as markdown in docs/decisions/,
      verification records as the PR's CI artifacts plus a posted comment summary.
      The design record is produced by the design step and consumed by tech_lead
      at the pre-merge gate. The verification record is produced by the implement
      step and consumed by tech_lead at the same gate. Retention: indefinitely
      in git history. We don't have a separate ledger — the PR thread is the
      canonical record for this process, with Linear and Slack as projections.
  expected_outcome: accept
  must_capture:
    - evidence.destination
    - evidence.items
    - "evidence.items[].consumer non-empty"

reject_mechanical:
  user_inputs:
    - "We should capture evidence, but I don't know what it is yet or where it should live."
  expected_outcome: mechanical-refusal
  expected_refusal_reason: evidence-destination-missing

reject_quality:
  user_inputs:
    - "We log everything to a directory called process-logs/. Producer: the agent. Consumer: nobody specifically, just whoever's curious later."
  expected_outcome: quality-refusal
  expected_refusal_reason: evidence-without-consumer
```

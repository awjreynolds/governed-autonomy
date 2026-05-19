# Phase 8 — State and projection

Operating model section: §8 (State and auditability) and §9 (Projection into existing systems).

## What the dialog is doing

Phase 8 establishes where canonical process state lives and which surfaces are projections (collaboration views that can drift). Important process state should not live only in chat.

Not hard-refuse, but `state.canonical: unknown` will produce a warning, and any projection that overlaps with canonical fires `W008`.

## Accept exemplar

**Ground-truth dialog outcome:** accept

**User stated answer:**

> "Canonical state is the repo — PR threads, commits, merged branches, CI artifacts. Linear is a projection: it reflects the PR state but isn't the source of truth, and discrepancies are resolved by checking the PR. Slack is also a projection — discussion happens there but no decisions live there. Drift policy: review the projection mappings every 6 months or when we change source-control systems."

**Probes the dialog must fire:**

- "If Linear says 'done' but the PR isn't merged, which is correct? How would someone resolve the discrepancy?"
- "Is anyone treating Slack as the source of truth for any part of this process? Is there a risk of that creeping in?"
- "What's the drift policy — when do you re-check whether projections are still accurate?"

**Why this passes:**

Canonical is named (repo) and concrete (PR threads, commits, CI). Projections are explicitly named as projections, not as candidate sources of truth. Conflict resolution is named (check the PR). Drift policy exists. The user has thought about the asymmetry between source and projection.

## Reject exemplar (quality refusal)

**Ground-truth dialog outcome:** quality-refusal

**User stated answer:**

> "We use Linear, Slack, GitHub, and a Notion doc. Everyone knows where to look."

**Probes the dialog must fire:**

- "Which one is the source of truth? If they disagree, which wins?"
- "What happens when they drift?"
- "If a new team member asks 'where do I find the current state of this process,' what's the answer?"

**Why this fails (quality refusal):**

Multiple surfaces named, none designated canonical. The probes establish:
- No conflict-resolution rule
- No drift policy
- "Everyone knows where to look" is the textbook setup for chat-as-control-plane

The dialog records quality-refusal and offers help:

- Brainstorm: 2–3 candidate canonical-state choices given the named systems
- Local research: read existing skills' projectionPolicy fields for inspiration
- External research: common canonical-state patterns for SDLC workflows

## Test assertion

```yaml
phase: 8
hard_refuse: false

accept:
  user_inputs:
    - |
      Canonical state is the repo — PR threads, commits, merged branches, CI
      artifacts. Linear is a projection: it reflects the PR state but isn't the
      source of truth, and discrepancies are resolved by checking the PR. Slack
      is also a projection — discussion happens there but no decisions live
      there. Drift policy: review the projection mappings every 6 months or
      when we change source-control systems.
  expected_outcome: accept
  must_capture:
    - state.canonical
    - state.projections

reject_quality:
  user_inputs:
    - "We use Linear, Slack, GitHub, and a Notion doc. Everyone knows where to look."
  expected_outcome: quality-refusal
  expected_refusal_reason: canonical-state-not-named
```

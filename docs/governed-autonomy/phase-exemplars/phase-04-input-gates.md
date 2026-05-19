# Phase 4 — Input quality gates

Operating model section: §3 (Input quality gates).

## What the dialog is doing

Phase 4 establishes what counts as a viable input for the process. Weak input routes to clarification, research, or human decision — not to silent execution.

Not hard-refuse. A process with no input gates is still a process; it's just one that accepts any starting state, which the dialog can flag in `knownGaps` for later strengthening.

## Accept exemplar

**User input:**

> "Before this process starts: there must be a linked spec or ticket (Linear), the acceptance criteria must be stated explicitly, and the affected code area must be identifiable from the description. If any of these are missing, the agent routes to request-clarification rather than starting work."

**Probes the dialog must fire:**

- "Where do these inputs live and who supplies them? If acceptance criteria are ambiguous, who do you ask?"
- "What does the agent do when input fails the gate — refuse, draft a clarification, or escalate?"

**Why this passes:**

Three concrete inputs named (spec/ticket, acceptance criteria, code area). Failure routing is explicit: request-clarification, not silent execution. The user has thought about the bad path, not just the happy path.

## Reject exemplar (quality refusal)

**User input:**

> "The agent needs a good ticket to start."

**Probes the dialog must fire:**

- "What makes a ticket 'good'? Name the fields or properties."
- "If a ticket is missing acceptance criteria, what happens? Does the agent start anyway?"
- "Who supplies the ticket — a human, another agent, an external system?"

**Why this fails (quality refusal):**

"Good ticket" is not gate-able. The probes establish that the user doesn't have specific input requirements in mind, just a general "I'll know it when I see it" intuition. That intuition isn't reproducible by an agent.

The dialog records quality-refusal and offers help:

- Brainstorm: common input gate patterns for SDLC (spec link, AC, area, owner)
- Local research: read the existing GADD reference for its triage step
- External research: ticket-readiness checklists from common SDLC playbooks

## Test assertion

```yaml
phase: 4
hard_refuse: false

accept:
  user_inputs:
    - |
      Before this process starts: there must be a linked spec or ticket (Linear),
      the acceptance criteria must be stated explicitly, and the affected code
      area must be identifiable from the description. If any of these are
      missing, the agent routes to request-clarification rather than starting work.
  expected_outcome: accept
  must_capture:
    - input_gates

reject_quality:
  user_inputs:
    - "The agent needs a good ticket to start."
  expected_outcome: quality-refusal
  expected_refusal_reason: input-gates-not-decidable
```

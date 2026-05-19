# Phase 7 — Escalation and approval

Operating model section: §7 (Escalation and approval).

## What the dialog is doing

Phase 7 establishes the difference between escalation (the system saying "I've hit a boundary, I need help") and approval (a human authorizing a transition the process explicitly reserves for a human). These get conflated and shouldn't be. Both must be defined before deployment, and they should not be the same person clicking the same button.

**This phase is hard-refuse.** No escalation path → stop.

## Accept exemplar

**Ground-truth dialog outcome:** accept

**User stated answer:**

> "Escalation conditions: (a) scope-change-detected — agent attempts to touch a file outside the named feature; (b) verification-fails-after-3-retries — repeated test failure; (c) input-quality-gate-fail — ticket missing acceptance criteria. All three escalate to tech_lead via Slack mention with a link to the PR. Approval is separate: pre-merge gate requires tech_lead's explicit approval on the PR. The agent who drafted the change cannot approve it. The reviewer who flags the change is welcome to also approve it after they've reviewed."

**Probes the dialog must fire:**

- "Escalation vs approval — which is which here? Define them in your own words."
- "If the agent escalates and the human says 'go ahead,' is that escalation completing or approval being granted?"
- "Can the same person who reviews the work also approve it? What stops self-approval?"

**Why this passes:**

Escalation conditions are concrete (operational: scope-change, retries, AC missing). Routing is named (Slack mention to tech_lead). Approval is separate from escalation. Self-approval is explicitly addressed (agent-as-drafter cannot approve; reviewer-as-approver is fine because reviewing is the work product). The user has thought through the difference, not used the words interchangeably.

## Reject exemplar 1 (mechanical refusal)

**Ground-truth dialog outcome:** mechanical-refusal

**User stated answer:**

> "The agent asks for help when it's confused."

**Probes the dialog must fire:**

- "What exact condition makes the agent stop and escalate?"
- "Who does the escalation go to?"
- "What route does the escalation use, and what evidence accompanies it?"

**Why this fails (mechanical refusal):**

`escalation` block is effectively empty — there's no `condition` and no `to`. The spec's core-set field "at least one escalation entry" is not satisfied. Hard stop.

The dialog explains: "Operating model §7: escalation must be defined before deployment. Without it, the agent doesn't know what to do when it hits a boundary — and worse, the humans don't know what to expect when escalation happens."

## Reject exemplar 2 (quality refusal)

**Ground-truth dialog outcome:** quality-refusal

**User stated answer:**

> "Escalation: if the agent has trouble, it should escalate to engineering. Approval: someone from engineering will approve."

**Probes the dialog must fire:**

- "Define 'has trouble' as a condition the agent can check. What does it do? Run a check? Try N times?"
- "Who in 'engineering' specifically receives the escalation? Is there a pager? A Slack channel? A queue?"
- "Is the person who approves the same as the person who escalated to? Are those distinct?"

**Why this fails (quality refusal):**

Escalation has a target ("engineering") and a condition ("has trouble") but neither survives probing:
- "Has trouble" is not operationalizable — the agent can't detect it
- "Engineering" is not a paging route — no human is actually paged
- Approver and escalation target are conflated

The dialog records quality-refusal and offers help:

- Brainstorm: 3 escalation conditions drawn from common SDLC failure modes
- Local research: existing GADD reference's escalation patterns
- External research: SRE escalation playbooks for AI/agent systems

## Test assertion

```yaml
phase: 7
hard_refuse: true

accept:
  user_inputs:
    - |
      Escalation conditions: (a) scope-change-detected — agent attempts to touch
      a file outside the named feature; (b) verification-fails-after-3-retries —
      repeated test failure; (c) input-quality-gate-fail — ticket missing
      acceptance criteria. All three escalate to tech_lead via Slack mention
      with a link to the PR. Approval is separate: pre-merge gate requires
      tech_lead's explicit approval on the PR. The agent who drafted the change
      cannot approve it. The reviewer who flags the change is welcome to also
      approve it after they've reviewed.
  expected_outcome: accept
  must_capture:
    - escalation
    - "escalation[].condition non-empty"
    - "escalation[].to non-empty"

reject_mechanical:
  user_inputs:
    - "The agent asks for help when it's confused."
  expected_outcome: mechanical-refusal
  expected_refusal_reason: escalation-empty

reject_quality:
  user_inputs:
    - "Escalation: if the agent has trouble, it should escalate to engineering. Approval: someone from engineering will approve."
  expected_outcome: quality-refusal
  expected_refusal_reason: escalation-not-operational
```

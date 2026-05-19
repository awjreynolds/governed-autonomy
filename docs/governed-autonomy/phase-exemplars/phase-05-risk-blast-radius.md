# Phase 5 — Risk and blast radius

Operating model section: §5 (Risk and blast radius).

## What the dialog is doing

Phase 5 establishes what can break if the process fails: customer impact, financial impact, legal exposure, reversibility, data sensitivity, operational dependency, cross-team reach. Higher blast radius requires stronger evidence, more approvals, real monitoring, and a tested rollback path.

Not hard-refuse, but a `risk.blast_radius: unknown` produces a `W002` warning post-emit.

## Accept exemplar

**Ground-truth dialog outcome:** accept

**User stated answer:**

> "Blast radius is production-code. Worst case is a buggy merge that breaks CI for everyone or ships a regression to customers. Reversibility is good — we can revert a commit in minutes, but only if we notice within the post-deploy monitoring window. Risk patterns I care about: post-hoc-governance (the agent did something we only see in review) and scope-creep-at-machine-speed (touching files outside the named feature). The customer impact is mediated by canaries; we don't ship to 100% until 48 hours."

**Probes the dialog must fire:**

- "You said 'low risk' — but this writes to production. Reconcile." (cross-check against Phase 3 actions)
- "What does the agent do that the operating model's uncontrolled-AI-risk-patterns explicitly warns about? Name 2."
- "How long does it take to notice a failure? How long to revert?"

**Why this passes:**

Blast radius is named (production-code). Reversibility is concrete (revert + monitoring window). Risk patterns are picked from the catalog with reasons. Customer impact mediated by canary deploys — the rollout shape is part of the answer. The user has thought about what they'd see if it went wrong, not just labelled the severity.

## Reject exemplar (quality refusal)

**Ground-truth dialog outcome:** quality-refusal

**User stated answer:**

> "Pretty low risk, since the agent only drafts and humans approve everything."

**Probes the dialog must fire:**

- "What's the worst that can happen if the agent's draft is approved without scrutiny?"
- "If the agent generates 50 drafts a day, how does the human catch a subtle one?"
- "Approval fatigue is a known failure mode — what protects against it here?"

**Why this fails (quality refusal):**

"Low risk because humans approve" is a load-bearing claim that doesn't survive probing. The probes establish:
- The user hasn't considered approval fatigue
- "Humans approve everything" is an aspiration, not a process — what stops rubber-stamping?
- No risk patterns from the catalog were named

The dialog records quality-refusal and offers help:

- Brainstorm: 3 risk patterns from the catalog most applicable to this process
- Local research: read `docs/governed-autonomy/uncontrolled-ai-risk-patterns.md` for failure modes
- External research: look up post-incident reviews from similar agentic systems

## Test assertion

```yaml
phase: 5
hard_refuse: false

accept:
  user_inputs:
    - |
      Blast radius is production-code. Worst case is a buggy merge that breaks
      CI for everyone or ships a regression to customers. Reversibility is good —
      we can revert a commit in minutes, but only if we notice within the
      post-deploy monitoring window. Risk patterns I care about: post-hoc-governance
      and scope-creep-at-machine-speed. The customer impact is mediated by canaries;
      we don't ship to 100% until 48 hours.
  expected_outcome: accept
  must_capture:
    - risk.blast_radius
    - risk.patterns

reject_quality:
  user_inputs:
    - "Pretty low risk, since the agent only drafts and humans approve everything."
  expected_outcome: quality-refusal
  expected_refusal_reason: risk-not-load-bearing
```

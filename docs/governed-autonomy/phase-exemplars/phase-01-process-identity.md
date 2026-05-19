# Phase 1 — Process identity

Operating model section: §0 (preamble / process framing).

## What the dialog is doing

Phase 1 establishes the process's identity: its `id`, `name`, `purpose` (one sentence), and `scope` (includes/excludes).

This phase is **not** hard-refuse. A user who can't articulate the purpose can be helped by the dialog. But the dialog must surface vagueness before passing to Phase 2.

## Accept exemplar

**Ground-truth dialog outcome:** accept

**User stated answer:**

> "I want to set up a governed skill set for our SDLC feature-delivery workflow. The goal is to let coding agents draft changes, run tests, and open PRs, but never merge to main without a human reviewer. In scope: feature development through PR open. Out of scope: production deployment, hotfixes, and rollback playbooks."

**Probes the dialog must fire:**

- "What does this process *not* cover that someone might assume it does?" (forces excludes)
- "If someone said 'this process worked,' what would they be observing? One sentence." (forces purpose to be load-bearing)

**Why this passes:**

The user named the process (`sdlc-feature-delivery`), gave a one-sentence purpose, and explicitly listed both includes and excludes. The excludes are concrete (deployment, hotfixes, rollback) — the user clearly thought about boundary cases.

## Reject exemplar (quality refusal)

**Ground-truth dialog outcome:** quality-refusal

**User stated answer:**

> "It's our software development workflow. The agents help us build features faster."

**Probes the dialog must fire:**

- "What's the scope? Where does this process start and end?"
- "What does this process *not* cover?"
- "If someone said 'this process worked,' what would they be observing?"

**Why this fails (quality refusal):**

"Software development workflow" is too broad to be a process. "Build features faster" is an aspiration, not a purpose. The user can't name a single concrete decision the process governs, and can't name what's out of scope. The dialog records this as quality-refusal: phase populated but not load-bearing.

The dialog offers help options (brainstorm common SDLC sub-processes) before refusing.

## Test assertion

```yaml
phase: 1
hard_refuse: false

accept:
  user_inputs:
    - |
      I want to set up a governed skill set for our SDLC feature-delivery workflow.
      The goal is to let coding agents draft changes, run tests, and open PRs, but
      never merge to main without a human reviewer. In scope: feature development
      through PR open. Out of scope: production deployment, hotfixes, and rollback
      playbooks.
  expected_outcome: accept
  must_capture:
    - process.purpose
    - process.scope.includes
    - process.scope.excludes

reject_quality:
  user_inputs:
    - "It's our software development workflow. The agents help us build features faster."
  expected_outcome: quality-refusal
  expected_refusal_reason: purpose-not-load-bearing
```

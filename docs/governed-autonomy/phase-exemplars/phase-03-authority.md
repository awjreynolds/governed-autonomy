# Phase 3 — Authority (allowed and prohibited actions)

Operating model section: §2 (Authority boundaries).

## What the dialog is doing

Phase 3 establishes the authority surface: what the agent IS allowed to do (default affirmative list) and what it MUST NOT do (hard ceiling). Both sides are load-bearing. "What the agent must not do" is not derivable from "what it's allowed to do" by complement — prohibitions are explicit affirmative safety constraints.

**This phase is hard-refuse.** Either `default_allowed_actions` or `prohibited_actions` empty → stop.

## Accept exemplar

**Ground-truth dialog outcome:** accept

**User stated answer:**

> "Allowed: draft code changes, run verification (tests, linters, type checks), open pull requests. Prohibited: approve own work, expand scope silently (touching files outside the named feature), merge to main directly. The audit trail is GitHub's PR history; tech_lead is the only one who can grant merge permission. Nothing stops the agent issuing 10 PRs in a row, but each PR still has to clear the pre-merge gate."

**Probes the dialog must fire:**

- "You said 'draft' — what's the audit trail? What stops a draft from being silently promoted?"
- "What stops the agent from doing the same action 100 times in rapid succession?"
- "Your prohibitions: are these things the agent could otherwise plausibly do? Or are they obvious enough that they're filler?"

**Why this passes:**

Allowed and prohibited are concrete and from the catalog (draft-artifact, run-verification, approve-own-work, expand-scope-silently). Audit trail named (GitHub PR history). Rate-control mechanism (each PR clears the same gate). Prohibitions are load-bearing — not just "don't be malicious" filler.

Suggested catalog refs the dialog should surface:
- `catalog:action:draft-artifact`, `catalog:action:run-verification`
- `catalog:action:approve-own-work`, `catalog:action:expand-scope-silently`
- The user invented `local:open-pr` and `local:merge-to-main`, both with category and >=20-char definitions.

## Reject exemplar 1 (mechanical refusal)

**Ground-truth dialog outcome:** mechanical-refusal

**User stated answer:**

> "It can write code. That's it."

**Probes the dialog must fire:**

- "What is the affirmative list of actions the agent may take?"
- "What must the agent never do, even if doing it would seem useful?"
- "Are there systems, branches, spending limits, or customer-impacting actions that are explicitly off limits?"

**Why this fails (mechanical refusal):**

Allowed is populated. Prohibited is empty. The spec requires both populated. Hard stop.

The dialog explains: "Operating model §2 requires explicit prohibitions. What the agent must NOT do is load-bearing on its own; relying on 'what's not allowed is implicitly prohibited' produces ungoverned actions by omission."

## Reject exemplar 2 (quality refusal)

**Ground-truth dialog outcome:** quality-refusal

**User stated answer:**

> "Allowed: do useful things. Prohibited: don't do harmful things."

**Probes the dialog must fire:**

- "What's a 'useful thing'? Name one. Can the agent open a PR? Can it run tests?"
- "What's a 'harmful thing'? Could the agent merge to main? Push to a customer-facing branch? Delete a file?"
- "Would someone reading this know what's allowed without asking you?"

**Why this fails (quality refusal):**

Authority is populated but neither side is operational. Probes establish that "useful" and "harmful" are not decidable by anyone reading the file. The dialog records this as quality-refusal and offers help:

- Brainstorm: 3 candidate action sets for SDLC processes drawn from `gaps/catalogs/v1/actions.yml`
- Local research: read the existing skill (retrofit branch) or `reference-packages/gadd/` for inspiration
- External research: look up common authority patterns for coding-agent workflows

## Test assertion

```yaml
phase: 3
hard_refuse: true

accept:
  user_inputs:
    - |
      Allowed: draft code changes, run verification (tests, linters, type checks),
      open pull requests. Prohibited: approve own work, expand scope silently
      (touching files outside the named feature), merge to main directly.
      The audit trail is GitHub's PR history; tech_lead is the only one who can
      grant merge permission. Nothing stops the agent issuing 10 PRs in a row,
      but each PR still has to clear the pre-merge gate.
  expected_outcome: accept
  must_capture:
    - authority.default_allowed_actions
    - authority.prohibited_actions
    - local_definitions

reject_mechanical:
  user_inputs:
    - "It can write code. That's it."
  expected_outcome: mechanical-refusal
  expected_refusal_reason: prohibited-actions-empty

reject_quality:
  user_inputs:
    - "Allowed: do useful things. Prohibited: don't do harmful things."
  expected_outcome: quality-refusal
  expected_refusal_reason: authority-not-operational
```

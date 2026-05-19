# Phase 2 — Roles and accountability

Operating model section: §1 (Roles and decision rights).

## What the dialog is doing

Phase 2 establishes the roles in the process and which one is accountable for outcomes. Accountability cannot be inferred — it must be named. Agents do not own accountability (operating model: "Autonomous system: executes bounded work but does not own accountability").

**This phase is hard-refuse.** No accountable human role named → stop.

## Accept exemplar

**User input:**

> "The tech_lead is accountable for merge decisions and release readiness. If something gets shipped broken, that's on them. Failure produces a PagerDuty alert; the on-call rotation pages the tech_lead. Vacation handoff is documented in our team runbook — the deputy is the staff_engineer. The merge bit can be revoked from their GitHub team membership if needed. The agent (role:agent) is autonomous and owns nothing — its accountability is `nothing`."

**Probes the dialog must fire:**

- "If tech_lead is accountable, what specifically can be revoked from them when this process fails?"
- "Who can actually page tech_lead at 2am? What's the route?"
- "What happens when tech_lead is on vacation? Who owns it then?"

**Why this passes:**

Accountability is concrete: named role, specific failure consequence (PagerDuty, revoke merge bit), defined handoff (deputy = staff_engineer). The user has clearly thought about what accountability *means* operationally, not just labelled someone with the word.

The agent role is correctly flagged `autonomous: true` with `accountable_for: nothing` — which the dialog has to recognize as the sentinel value for "explicitly no accountability."

## Reject exemplar 1 (mechanical refusal)

**User input:**

> "We have engineers, designers, and product managers. The agent will work with them."

**Why this fails (mechanical refusal):**

Roles are listed but no role has `accountable_for` set. The spec's core-set field `accountable_for` (at least one role must have a non-empty, non-`nothing` value) is missing. Hard stop.

The dialog explains: "Operating model §1 requires a named accountable human role. Without one, the operating model collapses — there's nobody to escalate to, nobody to revoke from, nobody who owns failure."

## Reject exemplar 2 (quality refusal)

**User input:**

> "The engineering team is accountable for everything in this process. They're a great team."

**Probes the dialog must fire:**

- "If 'engineering team' is accountable, who specifically gets paged when something fails?"
- "What can be revoked from 'the team'? Is there a single point of contact?"
- "What happens on weekends or when the team is at a conference?"

**Why this fails (quality refusal):**

`accountable_for` is populated, so it passes the mechanical check. But probes establish:
- No concrete paging route (a team isn't pageable)
- No revocation mechanism (a team isn't a permissions holder)
- No handoff (a team has no on-call rotation defined here)

Accountability isn't load-bearing if it can't be operationalized. The dialog records quality-refusal and offers help:

- Brainstorm: propose 2–3 candidate accountable roles drawn from the user's described structure (tech_lead, engineering_manager, on_call_engineer)
- Local research: read the repo's CODEOWNERS, runbooks, or existing skill governance for inspiration
- External research: common SDLC accountability patterns

## Test assertion

```yaml
phase: 2
hard_refuse: true

accept:
  user_inputs:
    - |
      The tech_lead is accountable for merge decisions and release readiness. If
      something gets shipped broken, that's on them. Failure produces a PagerDuty
      alert; the on-call rotation pages the tech_lead. Vacation handoff is
      documented in our team runbook — the deputy is the staff_engineer. The
      merge bit can be revoked from their GitHub team membership if needed. The
      agent is autonomous and owns nothing — its accountability is "nothing".
  expected_outcome: accept
  must_capture:
    - roles
    - "roles[].accountable_for non-empty for at least one role"

reject_mechanical:
  user_inputs:
    - "We have engineers, designers, and product managers. The agent will work with them."
  expected_outcome: mechanical-refusal
  expected_refusal_reason: no-accountable-role

reject_quality:
  user_inputs:
    - "The engineering team is accountable for everything in this process. They're a great team."
  expected_outcome: quality-refusal
  expected_refusal_reason: accountability-not-operational
```

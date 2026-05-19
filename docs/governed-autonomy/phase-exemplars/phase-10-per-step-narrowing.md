# Phase 10 — Per-step narrowing

Operating model section: spans §2 (authority), §4 (scope and execution boundaries).

## What the dialog is doing

Phase 10 walks each step from Phase 9 and applies step-specific narrowing where the step deviates from process default: `authority_overrides.allowed_actions`, `authority_overrides.prohibited_actions`, `authority_overrides.autonomy_tier`, optional `authority_overrides.justification`. Inheritance from process default is the default; this phase records the deviations.

Not hard-refuse, but more-permissive autonomy overrides without justification fire `W005`.

## Accept exemplar

**Ground-truth dialog outcome:** accept

**User stated answer (for the investigate-risk step from Phase 9):**

> "Investigate-risk step: overrides allowed_actions to only catalog:action:gather-context, catalog:action:read-repo-evidence, catalog:action:read-external-system-state. Investigation must be read-only — these are all data-plane-read. No autonomy override; inherits the process default of draft. No justification needed because this is *less* permissive than the process default."

**User stated answer (for the merge step):**

> "Merge step: overrides autonomy_tier to human_only. No allowed_actions override; inherits the process default but the human_only tier means the agent waits and the tech_lead acts. No justification needed because human_only is less permissive."

**Probes the dialog must fire:**

- "Step (2) is `step_kind: investigate` — its allowed actions are all `data-plane-read`. Good. What about local actions — any `local:` refs that might not be read-only?"
- "Step (5) is `human_only`. Its `requires_role` is `tech_lead` — a non-autonomous role. Good."
- "Any step where the autonomy override is MORE permissive than the process default? Those need a justification."

**Why this passes:**

Investigate-risk correctly narrows to read-only actions, matching its `step_kind: investigate`. Merge correctly downgrades to `human_only` and assigns a non-autonomous role. No more-permissive overrides exist, so no justification is required. The user understands inheritance and knows when to override.

## Reject exemplar (quality refusal)

**Ground-truth dialog outcome:** quality-refusal

**User stated answer:**

> "The implement step needs to be `autonomous_with_monitoring` because the agent should be able to push commits quickly without waiting for me. The justification is 'speed.'"

**Probes the dialog must fire:**

- "`autonomous_with_monitoring` for implement is two tiers more permissive than the process default of `draft`. What monitoring is actually in place?"
- "What does 'speed' mean operationally — what happens if you slow it down? Why is this the right tradeoff?"
- "If the agent acts autonomously, who's reading what it produces, and when?"

**Why this fails (quality refusal):**

The override is populated and has a justification, so `W005` doesn't fire mechanically. But the justification ("speed") doesn't survive probing:
- No monitoring is actually described
- "Speed" is not a governance argument
- The override would essentially remove human-in-the-loop for the implement step, contradicting the process's stated reliance on human review

The dialog records quality-refusal and offers help:

- Brainstorm: when is `autonomous_with_monitoring` legitimate, and what makes the monitoring actually catch failures
- Local research: existing skills with high-autonomy steps and what their monitoring looks like
- External research: SRE/MLOps patterns for autonomous-with-monitoring agent steps

## Test assertion

```yaml
phase: 10
hard_refuse: false

accept:
  user_inputs:
    - |
      Investigate-risk step: overrides allowed_actions to only
      catalog:action:gather-context, catalog:action:read-repo-evidence,
      catalog:action:read-external-system-state. Investigation must be
      read-only — these are all data-plane-read. No autonomy override;
      inherits the process default of draft. No justification needed
      because this is *less* permissive than the process default.
    - |
      Merge step: overrides autonomy_tier to human_only. No allowed_actions
      override; inherits the process default but the human_only tier means
      the agent waits and the tech_lead acts. No justification needed because
      human_only is less permissive.
  expected_outcome: accept
  must_capture:
    - "steps[].authority_overrides where applicable"
    - "no more-permissive overrides without justification"

reject_quality:
  user_inputs:
    - "The implement step needs to be autonomous_with_monitoring because the agent should be able to push commits quickly without waiting for me. The justification is 'speed.'"
  expected_outcome: quality-refusal
  expected_refusal_reason: justification-not-load-bearing
```

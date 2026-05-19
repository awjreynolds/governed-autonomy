# Phase 9 — Decomposition into steps

Operating model section: spans §1–§7 (steps inherit roles, authority, evidence, gates, escalation from process level).

## What the dialog is doing

Phase 9 breaks the process into discrete agent-executable steps. Each step gets `id`, `label`, `purpose`, `step_kind` (execute | investigate | decide | approve | monitor), `requires_role`, and optional `authority_overrides`. Investigation steps are read-only by definition.

Not hard-refuse, but `steps` must be non-empty (`E013`). A process with no steps is incoherent.

## Accept exemplar

**User input:**

> "Six steps: (1) design — produce a design record, step_kind: execute, requires_role: agent; (2) investigate-risk — read code paths and dependencies to identify reversibility constraints, step_kind: investigate, requires_role: agent, overrides allowed_actions to read-only; (3) implement — draft the code change and run verification, step_kind: execute, requires_role: agent; (4) review — read the diff and verify alignment with the design, step_kind: investigate, requires_role: tech_lead; (5) merge — merge after pre-merge gate passes, step_kind: approve, requires_role: tech_lead, autonomy_tier: human_only; (6) monitor-rollout — watch canary metrics, step_kind: monitor, requires_role: agent."

**Probes the dialog must fire:**

- "Each step is one agent-executable unit. Could 'design' actually be split — maybe research + draft + record? Or is it tight enough as one step?"
- "Investigation steps must be read-only. Step (2) is investigate — what's in its allowed_actions, and are any of them not data-plane-read?"
- "Step (5) is human_only — its requires_role is tech_lead. tech_lead is not autonomous. Good. But what does the agent do during this step? Nothing? Wait? Produce a draft?"

**Why this passes:**

Six discrete steps with distinct `step_kind` values. Investigation step is correctly restricted. Human-only step has a non-autonomous role assigned. The user is thinking about the decomposition at the right grain — not one mega-step, not 30 micro-steps. Each step would be a SKILL.md.

## Reject exemplar (quality refusal)

**User input:**

> "The agent does the work and the human approves. Two steps."

**Probes the dialog must fire:**

- "What does 'does the work' include — design, implement, test? All of those at once?"
- "Is the work a single agent call or a series of calls? What's the boundary between them?"
- "If something goes wrong mid-'work,' where does the process pause? At a sub-step?"

**Why this fails (quality refusal):**

Two steps is mechanically populated (passes `E013`) but the granularity is wrong:
- "Does the work" hides at least three or four real steps
- The agent can't actually execute "the work" as a single unit — there are real decision points inside it
- Failure handling and gates require finer granularity to be useful

The dialog records quality-refusal and offers help:

- Brainstorm: propose 5–7 candidate step decompositions for the described process
- Local research: existing GADD reference's 15-step structure for comparison
- External research: common SDLC workflow granularities

## Test assertion

```yaml
phase: 9
hard_refuse: false

accept:
  user_inputs:
    - |
      Six steps: (1) design — produce a design record, step_kind: execute,
      requires_role: agent; (2) investigate-risk — read code paths and
      dependencies, step_kind: investigate, requires_role: agent, overrides
      allowed_actions to read-only; (3) implement — draft and run verification,
      step_kind: execute, requires_role: agent; (4) review — read the diff,
      step_kind: investigate, requires_role: tech_lead; (5) merge — merge after
      pre-merge gate, step_kind: approve, requires_role: tech_lead,
      autonomy_tier: human_only; (6) monitor-rollout — watch canary metrics,
      step_kind: monitor, requires_role: agent.
  expected_outcome: accept
  must_capture:
    - steps
    - "len(steps) >= 2"
    - "every step has step_kind and requires_role"

reject_quality:
  user_inputs:
    - "The agent does the work and the human approves. Two steps."
  expected_outcome: quality-refusal
  expected_refusal_reason: decomposition-too-coarse
```

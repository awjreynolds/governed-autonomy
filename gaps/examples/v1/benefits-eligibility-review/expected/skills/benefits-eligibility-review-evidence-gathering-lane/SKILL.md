---
name: benefits-eligibility-review-evidence-gathering-lane
description: Request and collect supporting evidence within the service-standard time limit.
process: benefits-eligibility-review
lane: evidence_gathering_lane
generatedBy: gaps-v1-generator
doNotEditByHand: true
---

# Benefits eligibility review — Evidence gathering lane

## Purpose

Request and collect supporting evidence within the service-standard time limit.

## Input Quality Gate

Before acting in this lane, confirm every declared evidence input is present with the required fields.

| Evidence id         | Kind               | Required fields                      |
| ------------------- | ------------------ | ------------------------------------ |
| supporting-evidence | artifact-reference | evidenceType, sourcePath, receivedAt |
| time-limit-event    | risk-finding       | milestoneId, dueAt, observedAt       |

## Rules

**Authority plane:** `data_plane`  
**Autonomy tier:** `execute_with_approval`  
**Risk tier:** `medium`

### Allowed actions

- `request-evidence` — **Request additional evidence**. Ask for additional evidence to support a gate or decision.
- `request-clarification` — **Request clarification from a participant**. Ask a participant for additional input needed to proceed.
- `record-evidence` — **Record evidence**. Write an evidence item to canonical state. Append-only; supersedes via new evidence rather than mutation of prior records.
- `escalate-to-human` — **Escalate to a human**. Pause autonomous execution and request a human decision. Used when authority boundary is insufficient or evidence is unclear.

### Prohibited actions

- `approve-own-work` — **Approve own work**. The producer of an artifact also approves it. Always prohibited at any autonomous tier; allowed only when the role explicitly carries both producer and approver decision rights and a separate human attestation records the dual hat.
- `approve-gate` — **Approve a named gate**. Record explicit human approval of a defined gate. Promotes governed transitions on canonical state.
- `declare-final-classification` — **Declare a final classification authoritatively**. Declare an incident severity, customer impact, regulatory category, or similar classification as the final authoritative outcome.
- `infer-from-missing-evidence` — **Infer a fact from the absence of evidence**. Treat the absence of an evidence item as positive evidence of a conclusion.

## State Loop

### States

| State                 | Label               | Flags    |
| --------------------- | ------------------- | -------- |
| gathering_open        | Gathering open      | initial  |
| gathering_in_progress | In progress         | —        |
| gathering_breached    | Time-limit breached | —        |
| gathering_complete    | Complete            | terminal |
| gathering_abandoned   | Abandoned           | terminal |

### Transitions

| Transition                | From                  | To                    | Gate | Guard rules                  |
| ------------------------- | --------------------- | --------------------- | ---- | ---------------------------- |
| t-open-to-in-progress     | gathering_open        | gathering_in_progress | —    | defined(supporting-evidence) |
| t-in-progress-to-breached | gathering_in_progress | gathering_breached    | —    | defined(time-limit-event)    |
| t-in-progress-to-complete | gathering_in_progress | gathering_complete    | —    | defined(supporting-evidence) |
| t-breached-to-abandoned   | gathering_breached    | gathering_abandoned   | —    | defined(escalation-decision) |

## Gates

This lane does not own any gates directly. Refer to upstream lanes for approval gates that apply.

## Evidence To Produce

Produce the following evidence before leaving this lane. Use the spec's `evidenceModel.caseFileItems[]` shape exactly.

| Evidence id         | Kind               | Required fields                      | Retention  |
| ------------------- | ------------------ | ------------------------------------ | ---------- |
| supporting-evidence | artifact-reference | evidenceType, sourcePath, receivedAt | regulatory |

## Stop Conditions

- Lane reaches terminal state `gathering_complete` (Complete).
- Lane reaches terminal state `gathering_abandoned` (Abandoned).
- Transition `t-open-to-in-progress` from `gathering_open` is guarded; if no rule allows it, the lane stops and escalates.
- Transition `t-in-progress-to-breached` from `gathering_in_progress` is guarded; if no rule allows it, the lane stops and escalates.
- Transition `t-in-progress-to-complete` from `gathering_in_progress` is guarded; if no rule allows it, the lane stops and escalates.
- Transition `t-breached-to-abandoned` from `gathering_breached` is guarded; if no rule allows it, the lane stops and escalates.
- Gate `escalated_review_gate` is escalating; reaching it pauses the lane until human approval.

## Non-claim language

This skill is a generated artifact of a GAPS v1 process specification. It does not by itself constitute regulatory compliance, certification, legal sufficiency, or runtime execution. The spec is the source of truth; do not edit this file by hand — regenerate from the spec instead.

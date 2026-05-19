---
name: benefits-eligibility-review-assessment-lane
description: Draft the eligibility assessment using the gathered evidence.
process: benefits-eligibility-review
lane: assessment_lane
generatedBy: gaps-v1-generator
doNotEditByHand: true
---

# Benefits eligibility review — Assessment lane

## Purpose

Draft the eligibility assessment using the gathered evidence.

## Input Quality Gate

Before acting in this lane, confirm every declared evidence input is present with the required fields.

| Evidence id         | Kind               | Required fields                      |
| ------------------- | ------------------ | ------------------------------------ |
| supporting-evidence | artifact-reference | evidenceType, sourcePath, receivedAt |

## Rules

**Authority plane:** `data_plane`  
**Autonomy tier:** `draft`  
**Risk tier:** `medium`

### Allowed actions

- `draft-artifact` — **Draft a reviewable artifact**. Produce an artifact intended for human review. The artifact is not persisted as approved state until a gate approves it.
- `record-evidence` — **Record evidence**. Write an evidence item to canonical state. Append-only; supersedes via new evidence rather than mutation of prior records.
- `escalate-to-human` — **Escalate to a human**. Pause autonomous execution and request a human decision. Used when authority boundary is insufficient or evidence is unclear.

### Prohibited actions

- `approve-own-work` — **Approve own work**. The producer of an artifact also approves it. Always prohibited at any autonomous tier; allowed only when the role explicitly carries both producer and approver decision rights and a separate human attestation records the dual hat.
- `approve-gate` — **Approve a named gate**. Record explicit human approval of a defined gate. Promotes governed transitions on canonical state.
- `make-binding-policy-interpretation` — **Make a binding policy or legal interpretation**. Issue an interpretation of policy, regulation, or law that the organization will treat as authoritative.
- `declare-final-classification` — **Declare a final classification authoritatively**. Declare an incident severity, customer impact, regulatory category, or similar classification as the final authoritative outcome.

## State Loop

### States

| State                      | Label             | Flags    |
| -------------------------- | ----------------- | -------- |
| assessment_drafting        | Drafting          | initial  |
| assessment_awaiting_review | Awaiting reviewer | —        |
| assessment_complete        | Complete          | terminal |

### Transitions

| Transition             | From                       | To                         | Gate                     | Guard rules                  |
| ---------------------- | -------------------------- | -------------------------- | ------------------------ | ---------------------------- |
| t-drafting-to-awaiting | assessment_drafting        | assessment_awaiting_review | —                        | defined(assessment-draft)    |
| t-awaiting-to-complete | assessment_awaiting_review | assessment_complete        | assessment_decision_gate | defined(assessment-approval) |

## Gates

### Gate `assessment_decision_gate` — Senior reviewer decision gate

**Type:** `blocking`  
**Approval role:** `senior_reviewer`  
**Approval condition:** Reviewer confirms the assessment-draft is consistent with the recorded evidence and the published eligibility rules.  
**Escalation condition:** Reviewer cannot confirm without a policy interpretation that the senior reviewer is not authorized to make.

**Decision inputs:** assessment-draft, supporting-evidence

| When                                                       | Then     | Effect                                               |
| ---------------------------------------------------------- | -------- | ---------------------------------------------------- |
| defined(assessment-draft) and defined(supporting-evidence) | approve  | → `assessment_complete`; record: assessment-approval |
| undefined(assessment-draft)                                | escalate | —                                                    |
| undefined(supporting-evidence)                             | escalate | —                                                    |

**Else:** `escalate`

## Evidence To Produce

Produce the following evidence before leaving this lane. Use the spec's `evidenceModel.caseFileItems[]` shape exactly.

| Evidence id      | Kind               | Required fields              | Retention  |
| ---------------- | ------------------ | ---------------------------- | ---------- |
| assessment-draft | artifact-reference | path, contentHash, draftedAt | regulatory |

## Stop Conditions

- Lane reaches terminal state `assessment_complete` (Complete).
- Transition `t-drafting-to-awaiting` from `assessment_drafting` is guarded; if no rule allows it, the lane stops and escalates.
- Transition `t-awaiting-to-complete` from `assessment_awaiting_review` is guarded; if no rule allows it, the lane stops and escalates.
- Gate `escalated_review_gate` is escalating; reaching it pauses the lane until human approval.

## Non-claim language

This skill is a generated artifact of a GAPS v1 process specification. It does not by itself constitute regulatory compliance, certification, legal sufficiency, or runtime execution. The spec is the source of truth; do not edit this file by hand — regenerate from the spec instead.

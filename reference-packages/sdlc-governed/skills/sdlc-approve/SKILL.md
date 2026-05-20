---
name: sdlc-approve
governance:
  process: ../../governance.yml
  step: sdlc-approve
  inherits: [authority, evidence, escalation]
---
# SDLC Approve

Start with `${CLAUDE_PROJECT_DIR}/scripts/ga-enforce --start-step sdlc-approve`.

Only the Engineering Manager performs this step. Review the evidence and record approval or rejection in `evidence/approve/approval.md`. Do not approve work produced under the same role.

Mark completion with `ga-step done sdlc-approve`.

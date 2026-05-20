---
name: sdlc-plan
governance:
  process: ../../governance.yml
  step: sdlc-plan
  inherits: [authority, evidence, escalation]
---
# SDLC Plan

Start with `${CLAUDE_PROJECT_DIR}/scripts/ga-enforce --start-step sdlc-plan`.

Draft the implementation plan, verification commands, expected evidence, and rollback considerations. Write the plan to `evidence/plan/plan.md`.

Mark completion with `ga-step done sdlc-plan`.

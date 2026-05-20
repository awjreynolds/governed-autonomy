---
name: sdlc-scope
governance:
  process: ../../governance.yml
  step: sdlc-scope
  inherits: [authority, evidence, escalation]
---
# SDLC Scope

Start with `${CLAUDE_PROJECT_DIR}/scripts/ga-enforce --start-step sdlc-scope`.

Draft the product requirement, acceptance criteria, non-goals, and owner decisions. Write the intake record to `evidence/intake/intake.md` and the scoped requirement to `evidence/scope/prd.md`. Escalate scope changes to the Product Manager.

Mark completion with `ga-step done sdlc-scope`.

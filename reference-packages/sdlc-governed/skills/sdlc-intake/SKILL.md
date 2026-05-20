---
name: sdlc-intake
governance:
  process: ../../governance.yml
  step: sdlc-intake
  inherits: [authority, evidence, escalation]
---
# SDLC Intake

Start with `${CLAUDE_PROJECT_DIR}/scripts/ga-enforce --start-step sdlc-intake`.

Read the request, current repository state, and any linked issue. Do not write files in this step. Leave the intake record for `sdlc-scope`.

Mark completion with `ga-step done sdlc-intake`.

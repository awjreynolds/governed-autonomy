---
name: sdlc-decompose
governance:
  process: ../../governance.yml
  step: sdlc-decompose
  inherits: [authority, evidence, escalation]
---
# SDLC Decompose

Start with `${CLAUDE_PROJECT_DIR}/scripts/ga-enforce --start-step sdlc-decompose`.

Split the approved plan into bounded work items. Each item must name scope, expected files, tests, and evidence. Write the result to `evidence/decompose/work-items.md`.

Mark completion with `ga-step done sdlc-decompose`.

---
name: sdlc-design
governance:
  process: ../../governance.yml
  step: sdlc-design
  inherits: [authority, evidence, escalation]
---
# SDLC Design

Start with `${CLAUDE_PROJECT_DIR}/scripts/ga-enforce --start-step sdlc-design`.

Draft the technical design, boundaries, alternatives, and verification approach. Write the design to `evidence/design/sdd.md`. Escalate unclear technical boundaries to the Tech Lead.

Mark completion with `ga-step done sdlc-design`.

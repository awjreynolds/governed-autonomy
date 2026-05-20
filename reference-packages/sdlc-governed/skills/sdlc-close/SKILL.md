---
name: sdlc-close
governance:
  process: ../../governance.yml
  step: sdlc-close
  inherits: [authority, evidence, escalation]
---
# SDLC Close

Start with `${CLAUDE_PROJECT_DIR}/scripts/ga-enforce --start-step sdlc-close`.

Only close after approval. Record closure state, unresolved gaps, and archive readiness in `evidence/close/closure.md`.

Mark completion with `ga-step done sdlc-close`.

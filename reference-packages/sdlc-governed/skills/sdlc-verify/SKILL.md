---
name: sdlc-verify
governance:
  process: ../../governance.yml
  step: sdlc-verify
  inherits: [authority, evidence, escalation]
---
# SDLC Verify

Start with `${CLAUDE_PROJECT_DIR}/scripts/ga-enforce --start-step sdlc-verify`.

Run the verification commands named in the plan. Record command output, failures, retries, and residual risk in `evidence/verify/verification.md`. Escalate repeated verification failure.

Mark completion with `ga-step done sdlc-verify`.

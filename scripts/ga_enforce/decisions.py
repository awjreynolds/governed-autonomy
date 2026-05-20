"""Claude Code hook decisions for Governed Autonomy enforcement."""

from __future__ import annotations

import json
from typing import TypedDict


class HookResult(TypedDict):
    exit_code: int
    stdout: str


def _json(data: dict) -> str:
    return json.dumps(data, indent=2)


def allow() -> HookResult:
    return {"exit_code": 0, "stdout": ""}


def deny(reason: str) -> HookResult:
    # Hook contract source: https://code.claude.com/docs/en/hooks
    # Retrieved 2026-05-20. Command hooks receive JSON on stdin. PreToolUse
    # denies with hookSpecificOutput.permissionDecision. The same page says
    # exit 2 is the blocking exit-code path, while JSON is processed only on
    # exit 0; this prototype still prints JSON on exit 2 for deterministic
    # local inspection and uses exit 2 for enforcement.
    return {
        "exit_code": 2,
        "stdout": _json(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        ),
    }


def post_block(reason: str) -> HookResult:
    return {
        "exit_code": 2,
        "stdout": _json(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "decision": "block",
                    "reason": reason,
                }
            }
        ),
    }

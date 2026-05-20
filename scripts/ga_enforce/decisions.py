"""Claude Code hook decisions for Governed Autonomy enforcement."""

from __future__ import annotations

import json
from typing import TypedDict


class HookResult(TypedDict):
    exit_code: int
    stdout: str
    stderr: str


def _json(data: dict) -> str:
    return json.dumps(data, indent=2)


def allow() -> HookResult:
    return {"exit_code": 0, "stdout": "", "stderr": ""}


def deny(reason: str) -> HookResult:
    # Hook contract source: https://code.claude.com/docs/en/hooks
    # Retrieved 2026-05-20. Command hooks receive JSON on stdin. PreToolUse
    # blocks with exit 2 and stderr. JSON output is only processed on exit 0.
    return {
        "exit_code": 2,
        "stdout": "",
        "stderr": reason,
    }


def post_block(reason: str) -> HookResult:
    return {
        "exit_code": 0,
        "stdout": _json(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "decision": "block",
                    "reason": reason,
                }
            }
        ),
        "stderr": "",
    }

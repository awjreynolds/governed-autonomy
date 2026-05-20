"""Match Claude Code tool calls to governed action refs."""

from __future__ import annotations

import fnmatch
import json
from typing import Any


def _tool_input_text(tool_name: str, tool_input: dict[str, Any]) -> str:
    if tool_name == "Bash":
        return str(tool_input.get("command", ""))
    if "file_path" in tool_input:
        return str(tool_input.get("file_path", ""))
    return json.dumps(tool_input, sort_keys=True)


def _matches(pattern: str, tool_name: str, tool_input: dict[str, Any]) -> bool:
    if "(" in pattern and pattern.endswith(")"):
        name_pattern, input_pattern = pattern[:-1].split("(", 1)
        return fnmatch.fnmatchcase(tool_name, name_pattern) and fnmatch.fnmatchcase(_tool_input_text(tool_name, tool_input), input_pattern)
    return fnmatch.fnmatchcase(tool_name, pattern)


def match_tool_action(tool_action_map: dict[str, Any], hook_input: dict[str, Any]) -> str | None:
    tool_name = str(hook_input.get("tool_name", ""))
    tool_input = hook_input.get("tool_input") if isinstance(hook_input.get("tool_input"), dict) else {}
    for action_ref, patterns in tool_action_map.items():
        if not isinstance(action_ref, str) or not isinstance(patterns, list):
            continue
        for pattern in patterns:
            if isinstance(pattern, str) and _matches(pattern, tool_name, tool_input):
                return action_ref
    return None

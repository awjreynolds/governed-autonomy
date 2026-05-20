"""Command-line interface for ga-enforce."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.ga_enforce.action_map import match_tool_action
from scripts.ga_enforce.active_step import clear_active_step, read_active_step, write_active_step
from scripts.ga_enforce.decisions import HookResult, allow, deny, post_block
from scripts.ga_lint.discovery import discover_governance
from scripts.ga_lint.loader import load_yaml
from scripts.ga_lint.merge import effective_authority_for_step


WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ga-enforce")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--pre-tool", action="store_true", help="Evaluate a Claude Code PreToolUse event")
    mode.add_argument("--post-tool", action="store_true", help="Evaluate a Claude Code PostToolUse event")
    mode.add_argument("--verify", action="store_true", help="Verify enforcement configuration")
    mode.add_argument("--start-step", metavar="STEP_ID", help="Mark a governed step active")
    mode.add_argument("--clear-step", action="store_true", help="Clear the active governed step")
    parser.add_argument("--done-tool", default="Bash", help="Tool name that marks the active step done")
    parser.add_argument("--done-command-glob", help="Bash command glob that marks the active step done")
    return parser


def _emit(result: HookResult) -> int:
    if result["stdout"]:
        print(result["stdout"])
    if result["stderr"]:
        print(result["stderr"], file=sys.stderr)
    return result["exit_code"]


def _hook_input() -> dict[str, Any]:
    data = json.loads(sys.stdin.read() or "{}")
    return data if isinstance(data, dict) else {}


def _process_context(hook_input: dict[str, Any]) -> tuple[Path, Path, dict[str, Any]]:
    cwd = Path(str(hook_input.get("cwd") or Path.cwd()))
    governance_path = discover_governance(cwd)
    doc = load_yaml(governance_path)
    return governance_path.parent, governance_path, doc


def _active_step_doc(doc: dict[str, Any], step_id: str) -> dict[str, Any]:
    for step in doc.get("steps") or []:
        if isinstance(step, dict) and step.get("id") == step_id:
            return step
    return {}


def _pre_tool(hook_input: dict[str, Any]) -> HookResult:
    process_dir, _governance_path, doc = _process_context(hook_input)
    active = read_active_step(process_dir)
    step_id = active.get("step")
    if not isinstance(step_id, str):
        return allow()

    step = _active_step_doc(doc, step_id)
    if not step:
        return allow()

    effective = effective_authority_for_step(doc, step_id)
    enforcement = doc.get("enforcement") if isinstance(doc.get("enforcement"), dict) else {}
    tool_action_map = enforcement.get("tool_action_map") if isinstance(enforcement.get("tool_action_map"), dict) else {}
    if not tool_action_map:
        return allow()

    action = match_tool_action(tool_action_map, hook_input)
    if action and action in effective.prohibited_actions:
        return deny(f"{action} is prohibited for step:{step_id}")

    if step.get("step_kind") == "investigate" and str(hook_input.get("tool_name")) in WRITE_TOOLS:
        return deny(f"step:{step_id} is read-only; write tools are blocked")

    return allow()


def _done_marker_matches(active: dict[str, Any], hook_input: dict[str, Any]) -> bool:
    marker = active.get("done")
    if not isinstance(marker, dict):
        return False
    tool_name = marker.get("tool_name")
    if isinstance(tool_name, str) and tool_name != hook_input.get("tool_name"):
        return False
    command_glob = marker.get("command_glob")
    if isinstance(command_glob, str):
        from fnmatch import fnmatchcase

        command = str((hook_input.get("tool_input") or {}).get("command", ""))
        return fnmatchcase(command, command_glob)
    return True


def _required_evidence_paths(doc: dict[str, Any], step_id: str) -> list[str]:
    paths: list[str] = []
    evidence = doc.get("evidence") if isinstance(doc.get("evidence"), dict) else {}
    if evidence.get("destination") != "repo":
        return paths
    for item in evidence.get("items") or []:
        if isinstance(item, dict) and item.get("producer") == f"step:{step_id}":
            path = item.get("path")
            if isinstance(path, str) and path.strip():
                paths.append(path)
            else:
                paths.append(f"<missing path for evidence:{item.get('id', 'unknown')}>")
    return paths


def _post_tool(hook_input: dict[str, Any]) -> HookResult:
    process_dir, _governance_path, doc = _process_context(hook_input)
    active = read_active_step(process_dir)
    step_id = active.get("step")
    if not isinstance(step_id, str) or not _done_marker_matches(active, hook_input):
        return allow()

    missing: list[str] = []
    for evidence_path in _required_evidence_paths(doc, step_id):
        if evidence_path.startswith("<") or not (process_dir / evidence_path).exists():
            missing.append(evidence_path)
    if missing:
        return post_block(f"missing required evidence for step:{step_id}: {', '.join(missing)}")

    clear_active_step(process_dir)
    return allow()


def _start_step(step_id: str, done_tool: str, done_command_glob: str | None) -> HookResult:
    process_dir, _governance_path, doc = _process_context({"cwd": str(Path.cwd())})
    if not _active_step_doc(doc, step_id):
        return deny(f"unknown governed step: {step_id}")
    write_active_step(
        process_dir,
        {
            "step": step_id,
            "done": {
                "tool_name": done_tool,
                "command_glob": done_command_glob or f"ga-step done {step_id}",
            },
        },
    )
    return allow()


def _clear_step() -> HookResult:
    process_dir, _governance_path, _doc = _process_context({"cwd": str(Path.cwd())})
    clear_active_step(process_dir)
    return allow()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        hook_input = _hook_input()
        if args.pre_tool:
            return _emit(_pre_tool(hook_input))
        if args.post_tool:
            return _emit(_post_tool(hook_input))
        if args.start_step:
            return _emit(_start_step(args.start_step, args.done_tool, args.done_command_glob))
        if args.clear_step:
            return _emit(_clear_step())
        _process_context(hook_input)
        return _emit(allow())
    except Exception as exc:  # noqa: BLE001 - hook diagnostics must be clean
        print(f"ga-enforce: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate a GAPS v1 skill package from a generative-conformance spec."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.dont_write_bytecode = True

from gaps_v1_generator.adapters import agents_openai_yaml, command_md, command_toml  # noqa: E402
from gaps_v1_generator.context import build_context  # noqa: E402
from gaps_v1_generator.implementation_map import render_implementation_map  # noqa: E402
from gaps_v1_generator.manifests import agent_skills_json, claude_plugin_json, gemini_extension_json  # noqa: E402
from gaps_v1_generator.skill_md import compose_lane_skill  # noqa: E402


def _files_for_spec(spec_path: Path) -> list[tuple[str, str]]:
    ctx = build_context(spec_path)
    files: list[tuple[str, str]] = []
    skill_id_for_lane: dict[str, str] = {}

    for lane in ctx.spec.get("lanes", []) or []:
        skill_id, body = compose_lane_skill(ctx, lane)
        skill_id_for_lane[lane["id"]] = skill_id
        files.append((f"skills/{skill_id}/SKILL.md", body))
        files.append((f"skills/{skill_id}/agents/openai.yaml", agents_openai_yaml(ctx, lane, skill_id)))
        files.append((f"commands/{ctx.process_id}/{lane['id']}.md", command_md(ctx, lane, skill_id)))
        files.append((f"commands/{ctx.process_id}/{lane['id']}.toml", command_toml(ctx, lane, skill_id)))

    files.append(("agent-skills.json", agent_skills_json(ctx, skill_id_for_lane)))
    files.append((".claude-plugin/plugin.json", claude_plugin_json(ctx, skill_id_for_lane)))
    files.append(("gemini-extension.json", gemini_extension_json(ctx, skill_id_for_lane)))
    files.append(("implementation.v1.yml", render_implementation_map(ctx, skill_id_for_lane, files)))
    return files


def _write_or_check(target_root: Path, files: list[tuple[str, str]], check: bool) -> int:
    if not check:
        if target_root.exists():
            shutil.rmtree(target_root)
        target_root.mkdir(parents=True, exist_ok=True)
        for relative, body in files:
            path = target_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
            print(f"wrote {path}")
        return 0
    differ = False
    for relative, body in files:
        path = target_root / relative
        if not path.exists():
            print(f"MISSING: {path}", file=sys.stderr)
            differ = True
            continue
        existing = path.read_text(encoding="utf-8")
        if existing != body:
            print(f"DIFFER: {path}", file=sys.stderr)
            differ = True
    return 1 if differ else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to a generative-conformance ga-process.v1.yml")
    parser.add_argument("--output-root", type=Path, default=None,
                        help="Destination root. Default: gaps/generated/<process-id>/")
    parser.add_argument("--check", action="store_true", help="Fail if the generated output would differ from existing files.")
    parser.add_argument("--validate-after", action="store_true", help="Run validate-gaps-v1 on the spec at --level generative before generation.")
    args = parser.parse_args()

    if args.validate_after:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "validate-gaps-v1.py"), str(args.spec), "--level", "generative"],
            cwd=REPO_ROOT,
            check=False,
        )
        if result.returncode != 0:
            print("FAIL: spec does not meet generative conformance; refusing to generate.", file=sys.stderr)
            return 1

    files = _files_for_spec(args.spec)
    output_root = args.output_root or (REPO_ROOT / "gaps" / "generated" / args.spec.parent.name)
    return _write_or_check(output_root, files, args.check)


if __name__ == "__main__":
    raise SystemExit(main())

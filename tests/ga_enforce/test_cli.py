from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.ga_enforce.active_step import write_active_step


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "reference-packages" / "enforced-sample"


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT)
        self.process = Path(self.tmp.name) / "enforced-sample"
        shutil.copytree(FIXTURE, self.process)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, mode: str, payload: dict) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)
        return subprocess.run(
            ["python3", "-m", "scripts.ga_enforce.cli", mode],
            cwd=self.process,
            env=env,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )

    def run_command(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)
        return subprocess.run(
            ["python3", "-m", "scripts.ga_enforce.cli", *args],
            cwd=self.process,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_wrapper_runs_from_process_directory(self) -> None:
        result = subprocess.run(
            [str(ROOT / "scripts" / "ga-enforce"), "--verify"],
            cwd=self.process,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_start_and_clear_step_manage_active_step_marker(self) -> None:
        started = self.run_command("--start-step", "draft")

        self.assertEqual(started.returncode, 0, started.stderr + started.stdout)
        marker = self.process / ".governance" / "active-step.yml"
        self.assertTrue(marker.exists())
        self.assertIn("step: draft", marker.read_text(encoding="utf-8"))
        self.assertIn("command_glob: ga-step done draft", marker.read_text(encoding="utf-8"))

        cleared = self.run_command("--clear-step")

        self.assertEqual(cleared.returncode, 0, cleared.stderr + cleared.stdout)
        self.assertFalse(marker.exists())

    def test_pre_tool_blocks_mapped_prohibited_action(self) -> None:
        write_active_step(self.process, {"step": "draft"})

        result = self.run_cli(
            "--pre-tool",
            {"cwd": str(self.process), "hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push origin main"}},
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("prohibited", result.stderr)

    def test_pre_tool_blocks_write_tool_during_investigate_step(self) -> None:
        write_active_step(self.process, {"step": "investigate"})

        result = self.run_cli(
            "--pre-tool",
            {"cwd": str(self.process), "hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": "notes.md", "content": "x"}},
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("read-only", result.stderr)

    def test_pre_tool_is_advisory_when_tool_action_map_absent(self) -> None:
        governance = self.process / "governance.yml"
        governance.write_text(governance.read_text(encoding="utf-8").replace("enforcement:\n  tool_action_map:\n    catalog:action:approve-own-work:\n      - \"Bash(git push *)\"\n    catalog:action:draft-artifact:\n      - \"Write\"\n      - \"Edit(*)\"\n", ""), encoding="utf-8")
        write_active_step(self.process, {"step": "investigate"})

        result = self.run_cli(
            "--pre-tool",
            {"cwd": str(self.process), "hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": "notes.md", "content": "x"}},
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_post_tool_blocks_done_with_missing_evidence_then_clears_when_present(self) -> None:
        active = {"step": "draft", "done": {"tool_name": "Bash", "command_glob": "ga-step done draft"}}
        write_active_step(self.process, active)
        payload = {
            "cwd": str(self.process),
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ga-step done draft"},
            "tool_response": {"stdout": "", "stderr": "", "interrupted": False, "isImage": False},
        }

        missing = self.run_cli("--post-tool", payload)

        self.assertEqual(missing.returncode, 0, missing.stderr + missing.stdout)
        decision = json.loads(missing.stdout)
        self.assertEqual(decision["hookSpecificOutput"]["decision"], "block")
        self.assertIn("missing required evidence", decision["hookSpecificOutput"]["reason"])
        self.assertTrue((self.process / ".governance" / "active-step.yml").exists())

        (self.process / "evidence").mkdir()
        (self.process / "evidence" / "draft.md").write_text("evidence\n", encoding="utf-8")
        present = self.run_cli("--post-tool", payload)

        self.assertEqual(present.returncode, 0, present.stderr + present.stdout)
        self.assertFalse((self.process / ".governance" / "active-step.yml").exists())

    def test_post_tool_does_not_apply_repo_file_check_to_external_evidence(self) -> None:
        governance = self.process / "governance.yml"
        governance.write_text(governance.read_text(encoding="utf-8").replace("destination: repo", "destination: tracker"), encoding="utf-8")
        active = {"step": "draft", "done": {"tool_name": "Bash", "command_glob": "ga-step done draft"}}
        write_active_step(self.process, active)

        result = self.run_cli(
            "--post-tool",
            {
                "cwd": str(self.process),
                "hook_event_name": "PostToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "ga-step done draft"},
                "tool_response": {"stdout": "", "stderr": "", "interrupted": False, "isImage": False},
            },
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertFalse((self.process / ".governance" / "active-step.yml").exists())


if __name__ == "__main__":
    unittest.main()

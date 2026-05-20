from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "reference-packages" / "sdlc-governed"
EXPECTED_STEPS = [
    "sdlc-intake",
    "sdlc-scope",
    "sdlc-design",
    "sdlc-plan",
    "sdlc-decompose",
    "sdlc-implement",
    "sdlc-verify",
    "sdlc-approve",
    "sdlc-close",
]


class SdlcFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT)
        self.process = Path(self.tmp.name) / "sdlc-governed"
        shutil.copytree(FIXTURE, self.process)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_wrapper(self, *args: str, payload: dict | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(ROOT / "scripts" / "ga-enforce"), *args],
            cwd=self.process,
            input=json.dumps(payload) if payload is not None else None,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_fixture_lints_and_contains_full_sdlc_skill_set(self) -> None:
        lint = subprocess.run(
            [str(ROOT / "scripts" / "ga-lint"), str(self.process / "governance.yml")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(lint.returncode, 0, lint.stderr + lint.stdout)
        for step_id in EXPECTED_STEPS:
            skill = self.process / "skills" / step_id / "SKILL.md"
            self.assertTrue(skill.exists(), f"missing {skill}")
            frontmatter = skill.read_text(encoding="utf-8").split("---", 2)[1]
            self.assertIn("process: ../../governance.yml", frontmatter)
            self.assertIn(f"step: {step_id}", frontmatter)

    def test_fixture_registers_pre_and_post_tool_hooks(self) -> None:
        settings = json.loads((self.process / ".claude" / "settings.json").read_text(encoding="utf-8"))
        pre_commands = [hook["command"] for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]
        post_commands = [hook["command"] for group in settings["hooks"]["PostToolUse"] for hook in group["hooks"]]

        self.assertIn("${CLAUDE_PROJECT_DIR}/scripts/ga-enforce --pre-tool", pre_commands)
        self.assertIn("${CLAUDE_PROJECT_DIR}/scripts/ga-enforce --post-tool", post_commands)

    def test_simulated_subagent_lifecycle_blocks_and_clears(self) -> None:
        started = self.run_wrapper("--start-step", "sdlc-design")
        self.assertEqual(started.returncode, 0, started.stderr + started.stdout)

        blocked = self.run_wrapper(
            "--pre-tool",
            payload={
                "cwd": str(self.process),
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "git push origin main"},
            },
        )
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("prohibited", blocked.stderr)

        allowed = self.run_wrapper(
            "--pre-tool",
            payload={
                "cwd": str(self.process),
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_input": {"file_path": "governance.yml"},
            },
        )
        self.assertEqual(allowed.returncode, 0, allowed.stderr + allowed.stdout)

        done_payload = {
            "cwd": str(self.process),
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ga-step done sdlc-design"},
            "tool_response": {"stdout": "", "stderr": "", "interrupted": False, "isImage": False},
        }
        missing = self.run_wrapper("--post-tool", payload=done_payload)
        self.assertEqual(missing.returncode, 0, missing.stderr + missing.stdout)
        decision = json.loads(missing.stdout)
        self.assertEqual(decision["hookSpecificOutput"]["decision"], "block")
        self.assertTrue((self.process / ".governance" / "active-step.yml").exists())

        (self.process / "evidence" / "design").mkdir(parents=True)
        (self.process / "evidence" / "design" / "sdd.md").write_text("# SDD\n", encoding="utf-8")
        present = self.run_wrapper("--post-tool", payload=done_payload)

        self.assertEqual(present.returncode, 0, present.stderr + present.stdout)
        self.assertEqual(present.stdout, "")
        self.assertFalse((self.process / ".governance" / "active-step.yml").exists())

        implement_started = self.run_wrapper("--start-step", "sdlc-implement")
        self.assertEqual(implement_started.returncode, 0, implement_started.stderr + implement_started.stdout)
        implement_done = {
            "cwd": str(self.process),
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ga-step done sdlc-implement"},
            "tool_response": {"stdout": "", "stderr": "", "interrupted": False, "isImage": False},
        }
        missing_implement = self.run_wrapper("--post-tool", payload=implement_done)
        self.assertEqual(missing_implement.returncode, 0, missing_implement.stderr + missing_implement.stdout)
        implement_decision = json.loads(missing_implement.stdout)
        self.assertEqual(implement_decision["hookSpecificOutput"]["decision"], "block")
        self.assertIn("evidence/implement/implementation.md", implement_decision["hookSpecificOutput"]["reason"])

        (self.process / "evidence" / "implement").mkdir(parents=True)
        (self.process / "evidence" / "implement" / "implementation.md").write_text(
            "# Implementation\n",
            encoding="utf-8",
        )
        present_implement = self.run_wrapper("--post-tool", payload=implement_done)
        self.assertEqual(present_implement.returncode, 0, present_implement.stderr + present_implement.stdout)
        self.assertEqual(present_implement.stdout, "")
        self.assertFalse((self.process / ".governance" / "active-step.yml").exists())

    def test_scope_step_requires_intake_and_prd_evidence(self) -> None:
        started = self.run_wrapper("--start-step", "sdlc-scope")
        self.assertEqual(started.returncode, 0, started.stderr + started.stdout)

        done_payload = {
            "cwd": str(self.process),
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ga-step done sdlc-scope"},
            "tool_response": {"stdout": "", "stderr": "", "interrupted": False, "isImage": False},
        }
        missing = self.run_wrapper("--post-tool", payload=done_payload)
        self.assertEqual(missing.returncode, 0, missing.stderr + missing.stdout)
        decision = json.loads(missing.stdout)
        self.assertEqual(decision["hookSpecificOutput"]["decision"], "block")
        self.assertIn("evidence/intake/intake.md", decision["hookSpecificOutput"]["reason"])
        self.assertIn("evidence/scope/prd.md", decision["hookSpecificOutput"]["reason"])

        (self.process / "evidence" / "intake").mkdir(parents=True)
        (self.process / "evidence" / "scope").mkdir(parents=True)
        (self.process / "evidence" / "intake" / "intake.md").write_text("# Intake\n", encoding="utf-8")
        (self.process / "evidence" / "scope" / "prd.md").write_text("# PRD\n", encoding="utf-8")
        present = self.run_wrapper("--post-tool", payload=done_payload)

        self.assertEqual(present.returncode, 0, present.stderr + present.stdout)
        self.assertEqual(present.stdout, "")
        self.assertFalse((self.process / ".governance" / "active-step.yml").exists())

    def test_investigation_step_blocks_write_tools(self) -> None:
        started = self.run_wrapper("--start-step", "sdlc-intake")
        self.assertEqual(started.returncode, 0, started.stderr + started.stdout)

        write = self.run_wrapper(
            "--pre-tool",
            payload={
                "cwd": str(self.process),
                "hook_event_name": "PreToolUse",
                "tool_name": "Write",
                "tool_input": {"file_path": "notes.md", "content": "not allowed"},
            },
        )

        self.assertEqual(write.returncode, 2)
        self.assertIn("read-only", write.stderr)

        done_payload = {
            "cwd": str(self.process),
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ga-step done sdlc-intake"},
            "tool_response": {"stdout": "", "stderr": "", "interrupted": False, "isImage": False},
        }
        done = self.run_wrapper("--post-tool", payload=done_payload)
        self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
        self.assertEqual(done.stdout, "")
        self.assertFalse((self.process / ".governance" / "active-step.yml").exists())


if __name__ == "__main__":
    unittest.main()

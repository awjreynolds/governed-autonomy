"""Tests for cross_refs.check."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-gaps-v1.py"
FIXTURES = ROOT / "tests" / "gaps" / "v1" / "fixtures" / "invalid"


def run(spec: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(spec)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class CrossRefsTests(unittest.TestCase):
    def test_unresolved_role_fails(self) -> None:
        result = run(FIXTURES / "unresolved_role.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("approvalRole", result.stderr)
        self.assertIn("does not resolve", result.stderr)

    def test_orphan_state_fails(self) -> None:
        result = run(FIXTURES / "orphan_state.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("transition", result.stderr)
        self.assertIn("does not resolve", result.stderr)

    def test_duplicate_gate_id_fails(self) -> None:
        result = run(FIXTURES / "duplicate_gate_id.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate gate id", result.stderr)


if __name__ == "__main__":
    unittest.main()

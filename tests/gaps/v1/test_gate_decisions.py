"""Tests for gate_decisions.check."""

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


class GateDecisionsTests(unittest.TestCase):
    def test_incomplete_decision_fails(self) -> None:
        result = run(FIXTURES / "incomplete_decision.yml")
        self.assertNotEqual(result.returncode, 0)
        combined = result.stderr + result.stdout
        self.assertTrue(
            "undeclared input" in combined.lower() or "missing else" in combined.lower(),
            combined,
        )


if __name__ == "__main__":
    unittest.main()

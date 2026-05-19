"""Tests for catalog_refs.check."""

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


class CatalogRefsTests(unittest.TestCase):
    def test_unresolved_action_fails(self) -> None:
        result = run(FIXTURES / "unresolved_action.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not-a-real-action", result.stderr)
        self.assertIn("action catalog", result.stderr)

    def test_action_in_allowed_and_prohibited_fails(self) -> None:
        result = run(FIXTURES / "contradictory_actions.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("both allowed and prohibited", result.stderr)


if __name__ == "__main__":
    unittest.main()

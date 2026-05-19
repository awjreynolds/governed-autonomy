"""Tests for authority.check."""

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


class AuthorityTests(unittest.TestCase):
    def test_external_system_unmarked_fails(self) -> None:
        result = run(FIXTURES / "external_system_unmarked.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mutationRequiresApproval", result.stderr)


if __name__ == "__main__":
    unittest.main()

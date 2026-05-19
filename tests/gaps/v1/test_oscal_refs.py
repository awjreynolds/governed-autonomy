"""Tests for oscal_refs.check."""

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


class OscalRefsTests(unittest.TestCase):
    def test_unknown_control_id_fails(self) -> None:
        result = run(FIXTURES / "oscal_control_not_in_catalog.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BOGUS-1.1", result.stderr)
        self.assertIn("not in any referenced catalog", result.stderr)


if __name__ == "__main__":
    unittest.main()

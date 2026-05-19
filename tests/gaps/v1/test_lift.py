"""Tests for gaps-lift."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIFT_SCRIPT = ROOT / "scripts" / "gaps-lift.py"
PACKAGE = ROOT / "gaps" / "examples" / "v1" / "benefits-eligibility-review" / "expected"


class LiftTests(unittest.TestCase):
    def test_lift_emits_yaml(self) -> None:
        result = subprocess.run(
            [sys.executable, str(LIFT_SCRIPT), str(PACKAGE)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("processId", result.stdout)
        self.assertIn("fingerprint", result.stdout)

    def test_lift_refuses_non_generated_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(LIFT_SCRIPT), tmp],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("implementation.v1.yml", result.stderr)


if __name__ == "__main__":
    unittest.main()

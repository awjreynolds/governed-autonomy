"""End-to-end validator coverage on the comprehensive fixture."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-gaps-v1.py"
COMPREHENSIVE = ROOT / "gaps" / "examples" / "v1" / "comprehensive" / "ga-process.v1.yml"


class EndToEndTests(unittest.TestCase):
    def test_comprehensive_fixture_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(COMPREHENSIVE)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_comprehensive_fixture_passes_at_machine_validatable(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(COMPREHENSIVE), "--level", "machine-validatable"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_comprehensive_fixture_fails_at_generative(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(COMPREHENSIVE), "--level", "generative"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        # This fixture is intentionally not generative because evidenceModel
        # case file items used as evidenceInputs do not all have shape.required
        # in a way generative requires across both lanes. Expect failure.
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()

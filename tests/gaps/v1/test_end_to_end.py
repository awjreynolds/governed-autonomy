"""End-to-end validator coverage on the retained GADD fixture."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-gaps-v1.py"
GADD = ROOT / "gaps" / "examples" / "v1" / "gadd" / "ga-process.v1.yml"


class EndToEndTests(unittest.TestCase):
    def test_comprehensive_fixture_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(GADD)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_comprehensive_fixture_passes_at_machine_validatable(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(GADD), "--level", "machine-validatable"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_comprehensive_fixture_fails_at_generative(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(GADD), "--level", "generative"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        # This retained fixture is intentionally not generative; it preserves
        # the descriptive GADD process while --emit-spec remains internal.
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()

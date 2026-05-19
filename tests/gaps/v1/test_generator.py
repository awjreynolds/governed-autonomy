"""Tests for the GAPS v1 generator."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "generate-gaps-skill-package-v1.py"
PILOT_SPEC = ROOT / "gaps" / "examples" / "v1" / "benefits-eligibility-review" / "ga-process.v1.yml"
EXPECTED_ROOT = ROOT / "gaps" / "examples" / "v1" / "benefits-eligibility-review" / "expected"


class GeneratorTests(unittest.TestCase):
    def test_check_mode_matches_snapshot(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(PILOT_SPEC), "--output-root", str(EXPECTED_ROOT), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_deterministic_regeneration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(PILOT_SPEC), "--output-root", tmp],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            diff = subprocess.run(["diff", "-r", str(EXPECTED_ROOT), tmp], capture_output=True, text=True, check=False)
            self.assertEqual(diff.returncode, 0, f"snapshots diverge:\n{diff.stdout}")

    def test_generator_refuses_non_generative_with_validate_after(self) -> None:
        non_generative = ROOT / "gaps" / "examples" / "v1" / "minimal" / "ga-process.v1.yml"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(non_generative), "--output-root", str(EXPECTED_ROOT) + "-tmp", "--validate-after"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("generative conformance", result.stderr.lower() + result.stdout.lower())


if __name__ == "__main__":
    unittest.main()

"""Tests for conformance.check."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-gaps-v1.py"
FIXTURES = ROOT / "tests" / "gaps" / "v1" / "fixtures" / "invalid"
MINIMAL = ROOT / "gaps" / "examples" / "v1" / "minimal" / "ga-process.v1.yml"


def run(spec: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(spec), *extra],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ConformanceTests(unittest.TestCase):
    def test_minimal_descriptive_passes(self) -> None:
        result = run(MINIMAL)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_minimal_with_generative_override_fails(self) -> None:
        result = run(MINIMAL, "--level", "generative")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stateModel", result.stderr)

    def test_explicit_generative_without_state_model_fails(self) -> None:
        result = run(FIXTURES / "generative_without_state_model.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("generative", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()

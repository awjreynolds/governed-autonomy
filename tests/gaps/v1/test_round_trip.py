"""Tests for gaps-round-trip."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "gaps-round-trip.py"
PILOT = ROOT / "gaps" / "examples" / "v1" / "benefits-eligibility-review" / "ga-process.v1.yml"


class RoundTripTests(unittest.TestCase):
    def test_pilot_round_trips(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(PILOT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Round-trip ok", result.stdout)

    def test_round_trip_fails_for_non_generative(self) -> None:
        non_generative = ROOT / "gaps" / "examples" / "v1" / "minimal" / "ga-process.v1.yml"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(non_generative)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()

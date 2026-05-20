from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ValidationScriptTests(unittest.TestCase):
    def test_governed_autonomy_validation_runs_ga_enforce_tests(self) -> None:
        script = (ROOT / "scripts" / "validate-governed-autonomy.sh").read_text(encoding="utf-8")

        self.assertIn("tests/ga_enforce", script)


if __name__ == "__main__":
    unittest.main()

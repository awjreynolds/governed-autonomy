"""Tests for scripts/validate-gaps-v1.py (structural schema validation)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-gaps-v1.py"
MINIMAL_FIXTURE = ROOT / "gaps" / "examples" / "v1" / "minimal" / "ga-process.v1.yml"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ValidateGapsV1Tests(unittest.TestCase):
    def test_minimal_fixture_passes(self) -> None:
        result = run(str(MINIMAL_FIXTURE))
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_missing_required_field_fails(self) -> None:
        import tempfile
        import textwrap

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as handle:
            handle.write(textwrap.dedent(
                """\
                gapsVersion: "1.0.0"
                specStatus: draft
                conformanceLevel: descriptive
                """
            ))
            broken = Path(handle.name)
        try:
            result = run(str(broken))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required key", result.stderr.lower() + result.stdout.lower())
        finally:
            broken.unlink(missing_ok=True)

    def test_unknown_top_level_field_fails(self) -> None:
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as handle:
            handle.write(MINIMAL_FIXTURE.read_text() + "\nrogueField: nope\n")
            broken = Path(handle.name)
        try:
            result = run(str(broken))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected key", result.stderr.lower() + result.stdout.lower())
        finally:
            broken.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

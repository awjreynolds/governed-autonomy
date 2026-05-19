"""Tests for scripts/build-oscal-catalogs.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "build-oscal-catalogs.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class BuildOscalCatalogsTests(unittest.TestCase):
    def test_check_mode_passes_for_committed_outputs(self) -> None:
        result = run("--check")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_rebuild_is_byte_identical(self) -> None:
        existing = {
            path.name: path.read_text(encoding="utf-8")
            for path in (ROOT / "gaps" / "catalogs" / "v1" / "controls").glob("*.json")
        }
        self.assertGreater(len(existing), 0, "expected committed OSCAL JSON files")
        result = run()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        for name, prior in existing.items():
            current = (ROOT / "gaps" / "catalogs" / "v1" / "controls" / name).read_text(encoding="utf-8")
            self.assertEqual(prior, current, f"{name} changed on rebuild")

    def test_uuids_are_stable_across_runs(self) -> None:
        first_uuids = {}
        for path in (ROOT / "gaps" / "catalogs" / "v1" / "controls").glob("*.json"):
            first_uuids[path.name] = json.loads(path.read_text(encoding="utf-8"))["catalog"]["uuid"]
        result = run()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        second_uuids = {}
        for path in (ROOT / "gaps" / "catalogs" / "v1" / "controls").glob("*.json"):
            second_uuids[path.name] = json.loads(path.read_text(encoding="utf-8"))["catalog"]["uuid"]
        self.assertEqual(first_uuids, second_uuids)


if __name__ == "__main__":
    unittest.main()

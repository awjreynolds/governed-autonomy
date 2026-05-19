"""Tests for scripts/validate-catalogs.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-catalogs.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ValidateCatalogsTests(unittest.TestCase):
    def test_default_run_passes(self) -> None:
        result = run()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_missing_catalog_fails(self) -> None:
        result = run("--catalogs-root", "gaps/catalogs/v1/does-not-exist")
        self.assertNotEqual(result.returncode, 0)

    def test_evidence_kind_reference_resolves(self) -> None:
        risk = json.loads(
            subprocess.check_output(
                [
                    "ruby",
                    "-ryaml",
                    "-rjson",
                    "-e",
                    "print YAML.load_file(ARGV[0]).to_json",
                    str(ROOT / "gaps" / "catalogs" / "v1" / "risk-patterns.yml"),
                ],
                text=True,
            )
        )
        evidence = json.loads(
            subprocess.check_output(
                [
                    "ruby",
                    "-ryaml",
                    "-rjson",
                    "-e",
                    "print YAML.load_file(ARGV[0]).to_json",
                    str(ROOT / "gaps" / "catalogs" / "v1" / "evidence-kinds.yml"),
                ],
                text=True,
            )
        )
        evidence_ids = {entry["id"] for entry in evidence["evidenceKinds"]}
        for pattern in risk["riskPatterns"]:
            for kind in pattern.get("exampleEvidenceKinds", []):
                self.assertIn(kind, evidence_ids, f"pattern {pattern['id']} references unknown evidence kind {kind}")


if __name__ == "__main__":
    unittest.main()

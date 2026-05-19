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


class OscalCatalogValidationTests(unittest.TestCase):
    def test_oscal_catalogs_are_validated(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("validated", result.stdout)

    def test_duplicate_control_id_fails(self) -> None:
        catalog_path = ROOT / "gaps" / "catalogs" / "v1" / "controls" / "nist-ai-rmf.json"
        original = catalog_path.read_text(encoding="utf-8")
        broken_payload = json.loads(original)
        first_group = broken_payload["catalog"]["groups"][0]
        # Duplicate the first control id within the first group.
        duplicate = dict(first_group["controls"][0])
        first_group["controls"].append(duplicate)
        catalog_path.write_text(json.dumps(broken_payload, indent=2) + "\n", encoding="utf-8")
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate control id", result.stderr.lower())
        finally:
            catalog_path.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()

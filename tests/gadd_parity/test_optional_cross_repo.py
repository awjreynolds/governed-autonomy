from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path


class OptionalGaddCrossRepoTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_path = os.environ.get("GADD_REPO_PATH")
        if not repo_path:
            self.skipTest("GADD_REPO_PATH is not set")
        self.repo = Path(repo_path).expanduser().resolve()

    def run_in_gadd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(args),
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )

    def assert_clean_checkout(self, label: str) -> None:
        status = self.run_in_gadd("git", "status", "--porcelain")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual("", status.stdout, f"GADD checkout is dirty {label}:\n{status.stdout}")

    def test_gadd_generated_package_oracle_passes(self) -> None:
        script = self.repo / "scripts" / "validate-generated-gadd-package.py"
        self.assertTrue(script.is_file(), f"missing GADD oracle script: {script}")

        commit = self.run_in_gadd("git", "rev-parse", "--short", "HEAD")
        self.assertEqual(commit.returncode, 0, commit.stderr)
        self.assert_clean_checkout("before oracle run")

        result = self.run_in_gadd("python3", "scripts/validate-generated-gadd-package.py")

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("GADD Level 1 workflow scenarios validated", result.stdout)
        self.assertIn("GADD Level 2 live-style scenarios validated", result.stdout)
        self.assertIn("GADD Level 3 scenarios evaluated: 0 Level 3 findings", result.stdout)
        self.assertIn("Generated GADD package behavior validation passed", result.stdout)
        self.assert_clean_checkout(f"after oracle run at {commit.stdout.strip()}")


if __name__ == "__main__":
    unittest.main()

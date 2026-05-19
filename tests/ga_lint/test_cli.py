from __future__ import annotations

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


VALID_GOVERNANCE = """
governanceVersion: "1"
process:
  id: sample
  name: Sample
roles:
  - id: tech_lead
    accountable_for: Merge decisions.
  - id: agent
    autonomous: true
    accountable_for: nothing
authority:
  default_autonomy_tier: draft
  default_allowed_actions: ["catalog:action:draft-artifact"]
  prohibited_actions: ["catalog:action:approve-own-work"]
risk:
  blast_radius: repository
evidence:
  destination: repo
  items:
    - id: design-record
      kind: "catalog:evidence:design-decision"
      producer: "step:design"
      consumer: ["role:tech_lead"]
gates:
  - id: pre-merge
    requires_role: "role:tech_lead"
    requires_evidence: ["evidence:design-record"]
    blocks_steps: ["step:approve"]
escalation:
  - condition: verification-fails
    to: "role:tech_lead"
state:
  canonical: repo
  projections: [tracker]
freshness:
  drift_policy: Review when authority changes.
steps:
  - id: design
    purpose: Draft a design record for human approval.
    step_kind: execute
    requires_role: "role:agent"
  - id: approve
    purpose: Approve the design record after review.
    step_kind: approve
    requires_role: "role:tech_lead"
    authority_overrides:
      autonomy_tier: human_only
"""


def write_fixture(root: Path, governance: str = VALID_GOVERNANCE) -> Path:
    process = root / "process"
    process.mkdir()
    (process / "governance.yml").write_text(textwrap.dedent(governance), encoding="utf-8")
    for step_id in ("design", "approve"):
        skill = process / "skills" / step_id
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: sample-{step_id}\ngovernance:\n  process: ../../governance.yml\n  step: {step_id}\n---\n# {step_id}\n",
            encoding="utf-8",
        )
    return process


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)
        return subprocess.run(
            ["python3", "-m", "scripts.ga_lint.cli", *args],
            cwd=cwd or ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_valid_file_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            process = write_fixture(Path(tmp))
            result = self.run_cli(str(process / "governance.yml"))
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_error_exits_nonzero_and_json_is_valid(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            process = write_fixture(Path(tmp), VALID_GOVERNANCE.replace('prohibited_actions: ["catalog:action:approve-own-work"]', "prohibited_actions: []"))
            result = self.run_cli("--json", str(process / "governance.yml"))
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["errors"], 1)
            self.assertEqual(payload["issues"][0]["rule"], "E001")

    def test_discovers_governance_from_child_directory(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            process = write_fixture(Path(tmp))
            child = process / "skills" / "design"
            result = self.run_cli(cwd=child)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from typing import Any

from scripts.ga_lint.catalog import load_catalogs
from scripts.ga_lint.loader import find_repo_root
from scripts.ga_lint.rules import lint


ROOT = Path(__file__).resolve().parents[2]
CATALOG = load_catalogs(ROOT)


def base_doc() -> dict[str, Any]:
    return {
        "governanceVersion": "1",
        "process": {"id": "sample", "name": "Sample process", "purpose": "Exercise governed autonomy."},
        "roles": [
            {"id": "tech_lead", "label": "Tech lead", "accountable_for": "Merge decisions and release readiness."},
            {"id": "agent", "label": "Agent", "autonomous": True, "accountable_for": "nothing"},
        ],
        "authority": {
            "default_autonomy_tier": "draft",
            "default_allowed_actions": ["catalog:action:draft-artifact"],
            "prohibited_actions": ["catalog:action:approve-own-work"],
        },
        "local_definitions": {
            "write-prod": {
                "definition": "Write to a production state store outside the approved boundary.",
                "category": "data-plane-persist",
            }
        },
        "risk": {"patterns": ["catalog:risk:scope-creep-at-machine-speed"], "blast_radius": "repository"},
        "evidence": {
            "destination": "repo",
            "items": [
                {
                    "id": "design-record",
                    "kind": "catalog:evidence:design-decision",
                    "producer": "step:design",
                    "consumer": ["role:tech_lead"],
                }
            ],
        },
        "gates": [
            {
                "id": "pre-merge",
                "requires_role": "role:tech_lead",
                "requires_evidence": ["evidence:design-record"],
                "blocks_steps": ["step:approve"],
            }
        ],
        "escalation": [{"condition": "verification-fails", "to": "role:tech_lead"}],
        "state": {"canonical": "repo", "projections": ["tracker"]},
        "freshness": {"drift_policy": "Review when authority changes."},
        "steps": [
            {
                "id": "design",
                "label": "Design",
                "purpose": "Draft a design record for human approval.",
                "step_kind": "execute",
                "requires_role": "role:agent",
            },
            {
                "id": "approve",
                "label": "Approve",
                "purpose": "Approve the design record after review.",
                "step_kind": "approve",
                "requires_role": "role:tech_lead",
                "authority_overrides": {"autonomy_tier": "human_only"},
            },
        ],
    }


def write_skills(root: Path, *ids: str, mismatch: bool = False) -> Path:
    skills = root / "skills"
    for step_id in ids:
        directory = skills / step_id
        directory.mkdir(parents=True)
        frontmatter_step = "wrong" if mismatch else step_id
        (directory / "SKILL.md").write_text(
            f"---\nname: sample-{step_id}\ngovernance:\n  process: ../../governance.yml\n  step: {frontmatter_step}\n---\n# {step_id}\n",
            encoding="utf-8",
        )
    return skills


def rules_for(doc: dict[str, Any], skills: Path) -> set[str]:
    return {issue.rule for issue in lint(doc, skills.parent / "governance.yml", CATALOG, skills)}


class RuleTests(unittest.TestCase):
    def check_rule(self, rule: str, mutate) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills = write_skills(root, "design", "approve")
            clean = base_doc()
            self.assertNotIn(rule, rules_for(clean, skills))
            dirty = copy.deepcopy(clean)
            mutate(dirty, root)
            self.assertIn(rule, rules_for(dirty, skills))

    def test_e001_core_field_missing(self) -> None:
        self.check_rule("E001", lambda doc, _root: doc["authority"].update({"prohibited_actions": []}))

    def test_e002_accountable_role_absent(self) -> None:
        self.check_rule("E002", lambda doc, _root: [role.update({"accountable_for": "nothing"}) for role in doc["roles"]])

    def test_e003a_catalog_ref_missing(self) -> None:
        self.check_rule("E003a", lambda doc, _root: doc["authority"]["default_allowed_actions"].append("catalog:action:not-real"))

    def test_e003b_local_ref_undefined(self) -> None:
        self.check_rule("E003b", lambda doc, _root: doc["authority"]["default_allowed_actions"].append("local:not-defined"))

    def test_e003c_internal_ref_missing(self) -> None:
        self.check_rule("E003c", lambda doc, _root: doc["escalation"].append({"condition": "x", "to": "role:nope"}))

    def test_e004_self_approval(self) -> None:
        self.check_rule("E004", lambda doc, _root: doc["gates"][0].update({"requires_role": "role:agent"}))

    def test_e005_action_conflict(self) -> None:
        self.check_rule("E005", lambda doc, _root: doc["authority"]["prohibited_actions"].append("catalog:action:draft-artifact"))

    def test_e006_step_without_skill(self) -> None:
        self.check_rule("E006", lambda doc, root: (root / "skills" / "approve" / "SKILL.md").unlink())

    def test_e007_skill_without_step(self) -> None:
        self.check_rule("E007", lambda doc, root: write_skills(root, "extra"))

    def test_e008_frontmatter_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills = write_skills(root, "design", "approve", mismatch=True)
            self.assertIn("E008", rules_for(base_doc(), skills))

    def test_e009_agent_accountable(self) -> None:
        self.check_rule("E009", lambda doc, _root: doc["roles"][1].update({"accountable_for": "Delivery outcomes."}))

    def test_e010_dead_gate(self) -> None:
        self.check_rule("E010", lambda doc, _root: doc["evidence"]["items"][0].update({"producer": "step:nope"}))

    def test_e011_investigate_with_write(self) -> None:
        def mutate(doc, _root):
            doc["steps"][0].update({"step_kind": "investigate"})

        self.check_rule("E011", mutate)

    def test_e012_step_role_missing(self) -> None:
        self.check_rule("E012", lambda doc, _root: doc["steps"][0].pop("requires_role"))

    def test_e013_steps_missing(self) -> None:
        self.check_rule("E013", lambda doc, _root: doc.update({"steps": []}))

    def test_e014_step_kind_invalid(self) -> None:
        self.check_rule("E014", lambda doc, _root: doc["steps"][0].update({"step_kind": "teleport"}))

    def test_e015_enforcement_block_malformed(self) -> None:
        self.check_rule("E015", lambda doc, _root: doc.update({"enforcement": {"tool_action_map": {"catalog:action:draft-artifact": "Write"}}}))

    def test_warnings(self) -> None:
        mutations = {
            "W001": lambda doc: doc.pop("freshness"),
            "W002": lambda doc: doc["risk"].update({"blast_radius": "unknown"}),
            "W003": lambda doc: doc["evidence"]["items"][0].pop("consumer"),
            "W004": lambda doc: doc["steps"][0].update({"purpose": "short"}),
            "W005": lambda doc: doc["steps"][0].update({"authority_overrides": {"autonomy_tier": "execute_within_limits"}}),
            "W007": lambda doc: doc["gates"][0].update({"blocks_steps": []}),
            "W008": lambda doc: doc["state"].update({"projections": ["repo"]}),
            "W009": lambda doc: doc["steps"][0].update({"authority_overrides": {"autonomy_tier": "human_only"}}),
            "W010": lambda doc: doc["escalation"][0].update({"condition": "unknown"}),
        }
        for rule, mutate in mutations.items():
            with self.subTest(rule=rule), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                skills = write_skills(root, "design", "approve")
                doc = base_doc()
                mutate(doc)
                self.assertIn(rule, rules_for(doc, skills))


if __name__ == "__main__":
    unittest.main()

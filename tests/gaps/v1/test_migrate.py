"""Tests for the v0.1 -> v1 migrator components."""

from __future__ import annotations

import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from gaps_v1_migrator.match import fuzzy_action_match  # noqa: E402
from gaps_v1_migrator.render import render  # noqa: E402


CATALOG = [
    {"id": "draft-artifact", "label": "Draft a reviewable artifact", "definition": "Produce an artifact intended for human review."},
    {"id": "mutate-external-system", "label": "Mutate state in an external system", "definition": "Change state in an external tracker."},
    {"id": "approve-own-work", "label": "Approve own work", "definition": "The producer of an artifact also approves it."},
    {"id": "edit-repository-file-in-boundary", "label": "Edit repository file within approved boundary", "definition": "Modify code, configuration, or documentation files within an approved boundary."},
    {"id": "run-verification", "label": "Run verification commands", "definition": "Execute tests, linters, type checkers, security scanners."},
]


class FuzzyActionMatchTests(unittest.TestCase):
    def test_exact_label_match(self) -> None:
        match, score = fuzzy_action_match("Draft a reviewable artifact", CATALOG)
        self.assertEqual(match, "draft-artifact")
        self.assertGreater(score, 0.5)

    def test_phrase_overlap(self) -> None:
        match, score = fuzzy_action_match("draft research and PRD artifacts", CATALOG)
        self.assertEqual(match, "draft-artifact")

    def test_external_mutation(self) -> None:
        match, _ = fuzzy_action_match("mutate external issues without human approval", CATALOG)
        self.assertEqual(match, "mutate-external-system")

    def test_approve_own_work(self) -> None:
        match, _ = fuzzy_action_match("approve its own work for closure", CATALOG)
        self.assertEqual(match, "approve-own-work")

    def test_run_tests(self) -> None:
        match, _ = fuzzy_action_match("run tests and local verification commands", CATALOG)
        self.assertEqual(match, "run-verification")

    def test_no_match_returns_none(self) -> None:
        match, score = fuzzy_action_match("xylophone purple wombat hatstand", CATALOG)
        self.assertIsNone(match)
        self.assertLess(score, 0.2)


class RendererTests(unittest.TestCase):
    def test_renderer_uses_canonical_key_order_for_nested_documents(self) -> None:
        rendered = render({
            "process": {
                "scope": {
                    "excludes": [],
                    "includes": ["a", "b"],
                },
                "id": "demo",
            },
            "gapsVersion": "1.0.0",
        })
        self.assertEqual(
            rendered,
            "gapsVersion: 1.0.0\n"
            "process:\n"
            "  id: demo\n"
            "  scope:\n"
            "    includes:\n"
            "      - a\n"
            "      - b\n"
            "    excludes: []\n",
        )


if __name__ == "__main__":
    unittest.main()

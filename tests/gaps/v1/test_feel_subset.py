"""Tests for feel_subset parser."""

from __future__ import annotations

import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from gaps_v1_validator.feel_subset import FeelParseError, idents_used, parse  # noqa: E402


class FeelSubsetTests(unittest.TestCase):
    def test_parse_simple_comparison(self) -> None:
        node = parse('status == "open"')
        self.assertEqual(node.kind, "comparison")

    def test_parse_defined(self) -> None:
        node = parse("defined(approval_attestation)")
        self.assertEqual(node.kind, "predicate")

    def test_parse_boolean_combinator(self) -> None:
        node = parse("defined(prd) and prd.approved == true")
        self.assertEqual(node.kind, "and")

    def test_parse_not(self) -> None:
        node = parse("not undefined(x)")
        self.assertEqual(node.kind, "not")

    def test_parse_syntax_error(self) -> None:
        with self.assertRaises(FeelParseError):
            parse("status ==")

    def test_idents_used_extracts_top_level_names(self) -> None:
        names = idents_used(parse('status == "open" and defined(prd) and budget > 1000'))
        self.assertEqual({"status", "prd", "budget"}, names)


if __name__ == "__main__":
    unittest.main()

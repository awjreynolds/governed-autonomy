#!/usr/bin/env python3
"""Validate a GAPS v1 ga-process YAML against schema and semantic rules."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.dont_write_bytecode = True

from gaps_v1_validator.errors import ValidationReport  # noqa: E402
from gaps_v1_validator.loader import load_json, load_yaml  # noqa: E402
from gaps_v1_validator.schema_check import validate_schema  # noqa: E402

DEFAULT_SCHEMA = REPO_ROOT / "gaps" / "schema" / "v1" / "ga-process.schema.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument(
        "--level",
        choices=["descriptive", "machine-validatable", "generative"],
        default=None,
        help="Override the conformance level declared in the spec.",
    )
    args = parser.parse_args()

    report = ValidationReport()
    try:
        spec = load_yaml(args.spec)
        schema = load_json(args.schema)
    except (FileNotFoundError, RuntimeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    validate_schema(spec, schema, report)

    from gaps_v1_validator import authority, catalog_refs, conformance, cross_refs, gate_decisions, oscal_refs, state_machine

    cross_refs.check(spec, report)
    catalog_refs.check(spec, args.spec, report)
    state_machine.check(spec, report)
    gate_decisions.check(spec, report)
    authority.check(spec, report, args.spec)
    oscal_refs.check(spec, args.spec, report)
    conformance.check(spec, args.level, report)

    if not report.ok:
        print(report.render(), file=sys.stderr)
        print(f"FAIL {args.spec}: {len(report.issues)} issue(s)", file=sys.stderr)
        return 1
    print(f"GAPS v1 spec validated: {args.spec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

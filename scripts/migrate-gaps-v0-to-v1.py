#!/usr/bin/env python3
"""Migrate a GAPS v0.1 ga-process YAML to a v1 ga-process YAML."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.dont_write_bytecode = True

from gaps_v1_migrator.render import render  # noqa: E402
from gaps_v1_migrator.translate import translate  # noqa: E402
from gaps_v1_validator.loader import load_yaml  # noqa: E402

ACTION_CATALOG_PATH = REPO_ROOT / "gaps" / "catalogs" / "v1" / "actions.yml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to a v0.1 ga-process.yml file.")
    parser.add_argument("--out", type=Path, default=None, help="Destination path; default writes next to source as ga-process.v1.yml.")
    parser.add_argument("--stdout", action="store_true", help="Write to stdout instead of a file.")
    args = parser.parse_args()

    v0 = load_yaml(args.source)
    catalog = load_yaml(ACTION_CATALOG_PATH).get("actions", [])
    v1 = translate(v0, catalog, args.source.resolve())
    rendered = render(v1)

    if args.stdout:
        sys.stdout.write(rendered)
        return 0
    destination = args.out or (args.source.parent / "ga-process.v1.yml")
    destination.write_text(rendered, encoding="utf-8")
    print(f"wrote {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

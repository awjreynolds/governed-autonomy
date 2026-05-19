#!/usr/bin/env python3
"""Lift a generated v1 skill package back into a structural spec representation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.dont_write_bytecode = True

from gaps_v1_lift.recover import LiftError, lift_package  # noqa: E402
from gaps_v1_migrator.render import render  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_root", type=Path, help="Path to a generated skill package root.")
    parser.add_argument("--out", type=Path, default=None, help="Destination YAML. Default: stdout.")
    args = parser.parse_args()

    try:
        lifted = lift_package(args.package_root)
    except LiftError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    rendered = render(
        {
            "liftVersion": "1.0",
            "packageRoot": str(args.package_root),
            "fingerprint": lifted["fingerprint"],
            "implementation": lifted["implementation"],
            "lanes": [
                {
                    "laneId": lane["laneId"],
                    "skill": lane["skill"],
                    "states": lane["states"],
                    "transitions": lane["transitions"],
                    "gates": lane["gates"],
                    "evidenceInputs": lane["evidenceInputs"],
                    "evidenceOutputs": lane["evidenceOutputs"],
                }
                for lane in lifted["lanes"]
            ],
        }
    )

    if args.out:
        args.out.write_text(rendered, encoding="utf-8")
        print(f"wrote {args.out}")
        return 0
    sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

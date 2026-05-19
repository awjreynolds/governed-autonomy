#!/usr/bin/env python3
"""Round-trip a v1 spec: generate -> lift -> structural diff."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.dont_write_bytecode = True

from gaps_v1_lift.diff import diff_skeletons, lift_skeleton, spec_skeleton  # noqa: E402
from gaps_v1_lift.recover import LiftError, lift_package  # noqa: E402
from gaps_v1_validator.loader import load_yaml  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "generate-gaps-skill-package-v1.py"),
                str(args.spec),
                "--output-root",
                tmp,
                "--validate-after",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(result.stderr or result.stdout, file=sys.stderr)
            print(f"FAIL: generator refused spec {args.spec}", file=sys.stderr)
            return 1
        try:
            lifted = lift_package(Path(tmp))
        except LiftError as error:
            print(f"FAIL: {error}", file=sys.stderr)
            return 1
        spec = load_yaml(args.spec)
        issues = diff_skeletons(spec_skeleton(spec), lift_skeleton(lifted))
        if issues:
            print("Round-trip diff:", file=sys.stderr)
            for issue in issues:
                print(f"  - {issue}", file=sys.stderr)
            print(f"FAIL: round-trip detected {len(issues)} structural difference(s)", file=sys.stderr)
            return 1
    print(f"Round-trip ok: {args.spec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

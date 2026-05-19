"""Command-line interface for ga-lint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .catalog import load_catalogs
from .discovery import discover_governance
from .errors import ValidationReport
from .loader import find_repo_root, load_yaml
from .rules import lint


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ga-lint")
    parser.add_argument("path", nargs="?", help="Path to governance.yml or a directory to discover from")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        target = discover_governance(Path(args.path) if args.path else Path.cwd())
        doc = load_yaml(target)
        report = ValidationReport(lint(doc, target, load_catalogs(find_repo_root(target))))
    except Exception as exc:  # noqa: BLE001 - CLI should return clean diagnostics
        if args.json:
            print(json.dumps({"ok": False, "errors": [{"message": str(exc)}], "issues": []}, indent=2))
        else:
            print(f"ga-lint: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(
            json.dumps(
                {
                    "ok": report.ok,
                    "errors": len(report.errors),
                    "warnings": len(report.warnings),
                    "issues": [issue.to_dict() for issue in report.issues],
                },
                indent=2,
            )
        )
    elif report.issues:
        print(report.render())
        print(f"\n{len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    else:
        print(f"{target}: ok")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())


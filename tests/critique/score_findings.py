#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


FINDING_RE = re.compile(r"\b(F\d{3})\s+(blocking|significant|advisory)\b")


def parse(path: Path) -> set[tuple[str, str]]:
    text = path.read_text(encoding="utf-8")
    return {(match.group(1), match.group(2)) for match in FINDING_RE.finditer(text)}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: score_findings.py <fixture-dir>", file=sys.stderr)
        return 2
    fixture = Path(argv[1])
    expected = parse(fixture / "governance-review.md.expected")
    actual = parse(fixture / "governance-review.md")
    if not expected:
        print("no expected findings", file=sys.stderr)
        return 2
    matched = expected & actual
    score = len(matched) / len(expected)
    print(f"{fixture}: {len(matched)}/{len(expected)} expected findings matched ({score:.0%})")
    return 0 if score >= 0.8 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


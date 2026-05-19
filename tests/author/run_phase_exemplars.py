#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXEMPLARS = ROOT / "docs" / "governed-autonomy" / "phase-exemplars"
HARD_REFUSE = {"phase-02", "phase-03", "phase-06", "phase-07"}
OUTCOME_RE = re.compile(r"Ground-truth dialog outcome\*{0,2}:\*{0,2}\s*`?(accept|quality-refusal|mechanical-refusal)`?", re.I)


def main() -> int:
    files = sorted(EXEMPLARS.glob("phase-*.md"))
    if len(files) != 10:
        print(f"expected 10 exemplar files, found {len(files)}", file=sys.stderr)
        return 1
    for path in files:
        text = path.read_text(encoding="utf-8")
        outcomes = {match.group(1).lower() for match in OUTCOME_RE.finditer(text)}
        missing = [label for label in ("User stated answer", "Probes the dialog must fire", "Ground-truth dialog outcome") if label not in text]
        if missing:
            print(f"{path}: missing {missing}", file=sys.stderr)
            return 1
        if "accept" not in outcomes or not ({"quality-refusal", "mechanical-refusal"} & outcomes):
            print(f"{path}: must include accept and reject outcomes", file=sys.stderr)
            return 1
        if any(path.name.startswith(prefix) for prefix in HARD_REFUSE):
            if not {"quality-refusal", "mechanical-refusal"} <= outcomes:
                print(f"{path}: hard-refuse phase must include both reject tiers", file=sys.stderr)
                return 1
    print("phase exemplar contracts ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

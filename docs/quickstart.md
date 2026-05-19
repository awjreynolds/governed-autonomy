---
layout: page
title: Quickstart
---

# Quickstart

Clone the repository:

```bash
git clone https://github.com/awjreynolds/governed-autonomy.git
cd governed-autonomy
```

Author a governed skill set through the operating-model dialog:

```text
/governed-autonomy:author
```

Review an existing skill, skill set, or process directory without modifying it:

```text
/governed-autonomy:critique <path>
```

Run deterministic sidecar lint:

```bash
scripts/ga-lint <process-dir>/governance.yml
scripts/ga-lint --json <process-dir>/governance.yml
```

Run the full validation suite:

```bash
./scripts/validate-governed-autonomy.sh
```

## GAPS v1 Internals

GAPS v1 remains available only as internal `--emit-spec` plumbing:

```bash
python3 scripts/validate-gaps-v1.py gaps/examples/v1/gadd/ga-process.v1.yml
```

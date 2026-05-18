#!/usr/bin/env bash
set -euo pipefail

python3 scripts/validate-gaps.py
python3 scripts/validate-gaps-implementation.py
python3 -m unittest discover tests/gaps

python3 scripts/generate-gaps-skill-package.py tests/gaps/fixtures/tiny-process/ga-process.yml --output-root /tmp/governed-autonomy-generator-check
python3 scripts/generate-gaps-skill-package.py gaps/examples/gadd/ga-process.yml --output-root /tmp/governed-autonomy-gadd-generator-check
python3 scripts/validate-gaps-implementation.py /tmp/governed-autonomy-gadd-generator-check/gaps/generated/gadd/implementation.yml

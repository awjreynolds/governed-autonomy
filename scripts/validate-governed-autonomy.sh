#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Validating GAPS v0.1 reference specs"
python3 scripts/validate-gaps.py

echo "==> Validating GAPS v0.1 GADD implementation map"
python3 scripts/validate-gaps-implementation.py

echo "==> Checking GAPS v1 OSCAL catalogs are up to date with sources"
python3 scripts/build-oscal-catalogs.py --check

echo "==> Validating GAPS v1 catalogs"
python3 scripts/validate-catalogs.py

echo "==> Validating GAPS v1 reference specs"
for spec in gaps/examples/v1/*/ga-process.v1.yml; do
  [ -e "$spec" ] || continue
  python3 scripts/validate-gaps-v1.py "$spec"
done

echo "==> Smoke-testing v0.1 to v1 migrator"
SMOKE_SPEC="$(mktemp "$ROOT/gaps-migrate-smoke.XXXXXX")"
trap 'rm -f "$SMOKE_SPEC"' EXIT
python3 scripts/migrate-gaps-v0-to-v1.py gaps/examples/gadd/ga-process.yml --stdout > "$SMOKE_SPEC"
python3 scripts/validate-gaps-v1.py "$SMOKE_SPEC"
rm -f "$SMOKE_SPEC"
trap - EXIT

echo "==> Running test suites"
python3 -m unittest discover tests/gaps -v

echo "==> Generating GAPS v0.1 package previews"
python3 scripts/generate-gaps-skill-package.py tests/gaps/fixtures/tiny-process/ga-process.yml --output-root /tmp/governed-autonomy-generator-check
python3 scripts/generate-gaps-skill-package.py gaps/examples/compliance-review/ga-process.yml --output-root /tmp/governed-autonomy-compliance-review-generator-check
python3 scripts/generate-gaps-skill-package.py gaps/examples/incident-response/ga-process.yml --output-root /tmp/governed-autonomy-incident-response-generator-check
python3 scripts/generate-gaps-skill-package.py gaps/examples/procurement-approval/ga-process.yml --output-root /tmp/governed-autonomy-procurement-approval-generator-check
python3 scripts/generate-gaps-skill-package.py gaps/examples/gadd/ga-process.yml --output-root /tmp/governed-autonomy-gadd-generator-check
python3 scripts/validate-gaps-implementation.py /tmp/governed-autonomy-gadd-generator-check/gaps/generated/gadd/implementation.yml

echo "All Governed Autonomy validation checks passed."

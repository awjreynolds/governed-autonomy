#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Checking GAPS v1 OSCAL catalogs are up to date with sources"
python3 scripts/build-oscal-catalogs.py --check

echo "==> Validating GAPS v1 catalogs"
python3 scripts/validate-catalogs.py

echo "==> Validating retained GAPS v1 reference specs"
python3 scripts/validate-gaps-v1.py gaps/examples/v1/gadd/ga-process.v1.yml
python3 scripts/validate-gaps-v1.py gaps/examples/v1/incident-response/ga-process.v1.yml

echo "==> Running ga-lint tests"
python3 -m unittest discover tests/ga_lint -v

echo "==> Running ga-enforce tests"
python3 -m unittest discover tests/ga_enforce -v

echo "==> Running GADD parity tests"
python3 -m unittest discover tests/gadd_parity -v

echo "==> Running author exemplar harness"
python3 tests/author/run_phase_exemplars.py

echo "==> Scoring critique fixtures"
python3 tests/critique/score_findings.py tests/critique/fixtures/v1-gadd
python3 tests/critique/score_findings.py tests/critique/fixtures/reference-gadd
python3 tests/critique/score_findings.py tests/critique/fixtures/external-skill

echo "==> Running retained GAPS v1 validator tests"
python3 -m unittest discover -s tests/gaps/v1 -v

echo "All Governed Autonomy validation checks passed."

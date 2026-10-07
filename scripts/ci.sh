#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
bash "$root/scripts/phase0/ci.sh"
bash "$root/scripts/phase1/fetch_model.sh"
bash "$root/scripts/phase1/build_test.sh"
bash "$root/scripts/phase2/ci.sh"
python3 "$root/tests/analysis/test_paired_statistics.py"

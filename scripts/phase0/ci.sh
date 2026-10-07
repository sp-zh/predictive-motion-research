#!/usr/bin/env bash
set -euo pipefail
bash "$(dirname "$0")/fetch_vendor.sh"
bash "$(dirname "$0")/build_test.sh"

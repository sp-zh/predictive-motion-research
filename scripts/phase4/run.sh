#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
source /opt/ros/jazzy/setup.bash
source install/setup.bash
source install-phase4-math/setup.bash
export MUJOCO_ROOT="$root/.vendor/mujoco-3.3.7"
export LD_LIBRARY_PATH="$MUJOCO_ROOT/lib:$LD_LIBRARY_PATH"
test $# -eq 2 || { echo 'Usage: run.sh RAW_OUTPUT_ROOT FRESH_EPOCH'; exit 2; }
python3 scripts/phase4/run_all.py "$root" "$1" "$2"

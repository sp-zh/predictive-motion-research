#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export MAKEFLAGS=-j2
colcon --log-base log/phase3-math-only build --build-base build/phase3-math-only --install-base install/phase3-math-only --packages-select predictive_motion_control --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_BENCHMARKS=OFF -DBUILD_TESTING=ON 2>&1 | tee results/phase3/math-only-build.log
colcon --log-base log/phase3-math-only test --build-base build/phase3-math-only --install-base install/phase3-math-only --packages-select predictive_motion_control --event-handlers console_direct+ 2>&1 | tee results/phase3/math-only-test.log
colcon test-result --test-result-base build/phase3-math-only/predictive_motion_control --verbose 2>&1 | tee results/phase3/math-only-test-results.log
python3 scripts/phase3/audit_evidence.py | tee results/phase3/evidence-audit.log
python3 scripts/phase3/plot_evidence.py | tee results/phase3/plots.log

#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export MAKEFLAGS=-j2
cmake -S tests/integration/control_consumer -B build/control_consumer 2>&1 | tee results/phase2/consumer-build.log
cmake --build build/control_consumer --parallel 2 2>&1 | tee -a results/phase2/consumer-build.log
(cd /tmp; "$root/build/control_consumer/control_consumer") | tee results/phase2/consumer.log
ldd build/control_consumer/control_consumer | tee results/phase2/consumer-runtime-libraries.log
colcon --log-base log/phase2-math-only build --build-base build/phase2-math-only --install-base install/phase2-math-only --packages-select predictive_motion_control --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_BENCHMARKS=OFF -DBUILD_TESTING=ON 2>&1 | tee results/phase2/math-only-build.log
colcon --log-base log/phase2-math-only test --build-base build/phase2-math-only --install-base install/phase2-math-only --packages-select predictive_motion_control --event-handlers console_direct+ 2>&1 | tee results/phase2/math-only-test.log
colcon test-result --test-result-base build/phase2-math-only/predictive_motion_control --verbose 2>&1 | tee results/phase2/math-only-test-results.log
python3 scripts/phase2/audit_evidence.py 2>&1 | tee results/phase2/evidence-audit.log
python3 scripts/phase2/plot_evidence.py 2>&1 | tee results/phase2/plots.log

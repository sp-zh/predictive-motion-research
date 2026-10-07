#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"
source /opt/ros/jazzy/setup.bash
source "$root/install/setup.bash"
export MAKEFLAGS=-j2
out="$root/results/phase3/root-independent"
mkdir -p "$out"
colcon --log-base log/root-review-phase3 build --build-base build/root-review-phase3 --install-base install/root-review-phase3 --packages-select predictive_motion_control --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_TESTING=ON -DBUILD_BENCHMARKS=OFF > "$out/build.log" 2>&1
source install/root-review-phase3/setup.bash
colcon --log-base log/root-review-phase3 test --build-base build/root-review-phase3 --install-base install/root-review-phase3 --packages-select predictive_motion_control --event-handlers console_direct+ > "$out/test.log" 2>&1
colcon test-result --test-result-base build/root-review-phase3 --verbose > "$out/test-results.log" 2>&1
cmake -S tests/integration/nullspace_consumer -B build/root-review-nullspace-consumer > "$out/consumer-build.log" 2>&1
cmake --build build/root-review-nullspace-consumer --parallel 2 >> "$out/consumer-build.log" 2>&1
(cd /tmp; "$root/build/root-review-nullspace-consumer/nullspace_consumer") > "$out/consumer.log" 2>&1
ldd build/root-review-nullspace-consumer/nullspace_consumer > "$out/runtime-libraries.log"
echo 'ROOT_PHASE3_MATH_BUILD_TEST_CONSUMER_PASS'

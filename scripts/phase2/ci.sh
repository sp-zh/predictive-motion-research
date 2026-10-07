#!/usr/bin/env bash
# Fast baseline CI gate; full executed diagnostics remain scripts/phase2/run.sh.
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export MUJOCO_ROOT="$root/.vendor/mujoco-3.3.7"
export MAKEFLAGS=-j2
colcon build --packages-select predictive_motion_control --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_TESTING=ON -DBUILD_BENCHMARKS=ON
# A first build adds this package to the workspace; the pre-build setup did not
# expose its prefix. Refresh before exercising find_package from another project.
source install/setup.bash
colcon test --packages-select predictive_motion_control --event-handlers console_direct+
colcon test-result --test-result-base build/predictive_motion_control --verbose
cmake -S tests/integration/control_consumer -B build/ci-control-consumer
cmake --build build/ci-control-consumer --parallel 2
(cd /tmp; "$root/build/ci-control-consumer/control_consumer")
cmake -S tests/integration/nullspace_consumer -B build/ci-nullspace-consumer
cmake --build build/ci-nullspace-consumer --parallel 2
(cd /tmp; "$root/build/ci-nullspace-consumer/nullspace_consumer")

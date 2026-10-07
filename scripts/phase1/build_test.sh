#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
source /opt/ros/jazzy/setup.bash
export MUJOCO_ROOT="$root/.vendor/mujoco-3.3.7"
export KINEMATICS_CONFIG="$root/src/predictive_motion_kinematics/config/fr3.yaml"
export MAKEFLAGS=-j2
mkdir -p results/phase1
colcon build --packages-select predictive_motion_kinematics --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_TESTING=ON 2>&1 | tee results/phase1/build.log
source install/setup.bash
colcon test --packages-select predictive_motion_kinematics --event-handlers console_direct+ 2>&1 | tee results/phase1/test.log
colcon test-result --test-result-base build/predictive_motion_kinematics --verbose 2>&1 | tee results/phase1/test-results.log
timeout 180 ros2 run predictive_motion_kinematics numerical_validation "$KINEMATICS_CONFIG" "$root/.vendor/menagerie/franka_fr3/scene.xml" "$root/results/phase1/numerical" 2>&1 | tee results/phase1/numerical.log
installed="$root/install/predictive_motion_kinematics/share/predictive_motion_kinematics/config/fr3.yaml"
(cd /tmp; ros2 run predictive_motion_kinematics kinematics_smoke "$installed") | tee results/phase1/installed-smoke.log
cmake -S tests/integration/kinematics_consumer -B build/kinematics_consumer 2>&1 | tee results/phase1/consumer-build.log
cmake --build build/kinematics_consumer --parallel 2 2>&1 | tee -a results/phase1/consumer-build.log
(cd /tmp; "$root/build/kinematics_consumer/kinematics_consumer" "$installed") | tee results/phase1/consumer.log

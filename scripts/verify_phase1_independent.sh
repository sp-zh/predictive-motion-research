#!/usr/bin/env bash
# Reviewer build uses separate install/build outputs and installed configuration.
set -eo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"
source /opt/ros/jazzy/setup.bash
export MUJOCO_ROOT="$root/.vendor/mujoco-3.3.7"
export KINEMATICS_CONFIG="$root/src/predictive_motion_kinematics/config/fr3.yaml"
export MAKEFLAGS=-j2
out="$root/results/phase1/root-independent"
mkdir -p "$out"
colcon build --build-base build/root-review-phase1 --install-base install/root-review-phase1 --packages-select predictive_motion_kinematics --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_TESTING=ON > "$out/build.log" 2>&1
source install/root-review-phase1/setup.bash
colcon test --build-base build/root-review-phase1 --install-base install/root-review-phase1 --packages-select predictive_motion_kinematics --event-handlers console_direct+ > "$out/test.log" 2>&1
colcon test-result --test-result-base build/root-review-phase1 --verbose > "$out/test-results.log" 2>&1
installed="$root/install/root-review-phase1/predictive_motion_kinematics/share/predictive_motion_kinematics/config/fr3.yaml"
(cd /tmp; ros2 run predictive_motion_kinematics kinematics_smoke "$installed") > "$out/installed-smoke.log" 2>&1
(cd /tmp; timeout 180 ros2 run predictive_motion_kinematics numerical_validation "$installed" "$root/.vendor/menagerie/franka_fr3/scene.xml" "$out/numerical") > "$out/numerical.log" 2>&1
cmp results/phase1/numerical/samples.csv "$out/numerical/samples.csv"
echo 'INDEPENDENT_BUILD_TEST_INSTALLED_CONFIG_AND_REPLAY_PASS'

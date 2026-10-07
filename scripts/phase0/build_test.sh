#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
source /opt/ros/jazzy/setup.bash
export MUJOCO_ROOT="$root/.vendor/mujoco-3.3.7"
export FR3_MODEL="$root/.vendor/menagerie/franka_fr3/scene.xml"
mkdir -p results/phase0
colcon build --packages-select predictive_motion_description predictive_motion_sim --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_TESTING=ON --parallel-workers 2 2>&1 | tee results/phase0/build.log
source install/setup.bash
colcon test --packages-select predictive_motion_sim --event-handlers console_direct+ 2>&1 | tee results/phase0/test.log
colcon test-result --verbose 2>&1 | tee results/phase0/test-results.log
ros2 run predictive_motion_sim pinocchio_probe | tee results/phase0/pinocchio.log
bash tests/integration/phase0_ros.sh 2>&1 | tee results/phase0/ros-integration.log
cmake -S tests/integration/plant_consumer -B build/plant_consumer 2>&1 | tee results/phase0/consumer-build.log
cmake --build build/plant_consumer --parallel 2 2>&1 | tee -a results/phase0/consumer-build.log
build/plant_consumer/plant_consumer "$FR3_MODEL" | tee results/phase0/consumer.log

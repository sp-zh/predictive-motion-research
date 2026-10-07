#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
source /opt/ros/jazzy/setup.bash
source "$root/install/setup.bash"
export ROS_DOMAIN_ID=${PM_TEST_DOMAIN:-83}
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
model=${FR3_MODEL:-$root/.vendor/menagerie/franka_fr3/scene.xml}
ros2 run predictive_motion_sim state_bridge --ros-args -p model_path:="$model" -p seed:=42 > "$root/results/phase0/bridge.log" 2>&1 &
bridge_pid=$!
trap 'kill "$bridge_pid" 2>/dev/null || true; wait "$bridge_pid" 2>/dev/null || true' EXIT
timeout 15 ros2 run predictive_motion_sim bridge_probe

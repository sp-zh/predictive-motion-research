#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"
source /opt/ros/jazzy/setup.bash
source "$root/install/setup.bash"
out=results/phase2-observation-sync/root-observer-consumer
mkdir -p "$out"
cmake -S tests/integration/observation_consumer -B build/root-observer-consumer -DCMAKE_BUILD_TYPE=RelWithDebInfo > "$out/build.log" 2>&1
cmake --build build/root-observer-consumer --target observation_contract --parallel 2 >> "$out/build.log" 2>&1
build/root-observer-consumer/observation_contract src/predictive_motion_kinematics/config/fr3.yaml .vendor/menagerie/franka_fr3/scene.xml "$out/contract.csv" | tee "$out/contract.log"

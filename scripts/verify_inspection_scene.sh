#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"
source /opt/ros/jazzy/setup.bash
source install/setup.bash
python3 cad/scripts/assemble_scene.py
mkdir -p results/cad
cmake -S tests/integration/inspection_scene -B build/inspection_scene -DCMAKE_BUILD_TYPE=RelWithDebInfo > results/cad/scene-build.log 2>&1
cmake --build build/inspection_scene --parallel 2 >> results/cad/scene-build.log 2>&1
build/inspection_scene/inspection_scene_probe experiments/generated/inspection/scene.xml src/predictive_motion_kinematics/config/fr3.yaml cad/source/inspection.json results/cad/scene_evidence.json | tee results/cad/scene-probe.log

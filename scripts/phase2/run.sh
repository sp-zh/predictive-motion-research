#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
source /opt/ros/jazzy/setup.bash
export MUJOCO_ROOT="$root/.vendor/mujoco-3.3.7"
export MAKEFLAGS=-j2
mkdir -p results/phase2
python3 scripts/phase2/audit_velocity.py src/predictive_motion_kinematics/config/fr3.yaml config/phase2.yaml | tee results/phase2/velocity-provenance.log
colcon build --packages-select predictive_motion_control --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_TESTING=ON 2>&1 | tee results/phase2/build.log
source install/setup.bash
colcon test --packages-select predictive_motion_control --event-handlers console_direct+ 2>&1 | tee results/phase2/test.log
colcon test-result --test-result-base build/predictive_motion_control --verbose 2>&1 | tee results/phase2/test-results.log
cp config/phase2.yaml results/phase2/frozen_design.yaml
sha256sum config/phase2.yaml > results/phase2/design.sha256
sha256sum docs/phase2_protocol.md > results/phase2/protocol.sha256
date -u +%FT%TZ > results/phase2/design_frozen_at.txt
design_hash=$(sha256sum config/phase2.yaml | cut -d ' ' -f1)
runner="$root/install/predictive_motion_control/lib/predictive_motion_control/phase2_benchmark"
robot="$root/src/predictive_motion_kinematics/config/fr3.yaml"
scene="$root/.vendor/menagerie/franka_fr3/scene.xml"
"$runner" "$robot" "$scene" config/phase2.yaml results/phase2/development development results/phase2/selection.yaml "$design_hash" 2>&1 | tee results/phase2/development.log
sha256sum results/phase2/selection.yaml > results/phase2/selection.sha256
date -u +%FT%TZ > results/phase2/selection_frozen_at.txt
"$runner" "$robot" "$scene" config/phase2.yaml results/phase2/evaluation evaluation results/phase2/selection.yaml "$design_hash" 2>&1 | tee results/phase2/evaluation.log
bash scripts/phase2/run_weak.sh
python3 scripts/phase2/diagnostics.py 2>&1 | tee results/phase2/diagnostics.log
bash scripts/phase2/check_artifacts.sh

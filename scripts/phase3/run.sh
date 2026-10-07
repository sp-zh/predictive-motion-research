#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export MUJOCO_ROOT="$root/.vendor/mujoco-3.3.7"
export MAKEFLAGS=-j2
mkdir -p results/phase3
python3 scripts/phase2/audit_velocity.py src/predictive_motion_kinematics/config/fr3.yaml config/phase3.yaml | tee results/phase3/velocity-provenance.log
colcon build --packages-select predictive_motion_control --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_BENCHMARKS=ON -DBUILD_TESTING=ON 2>&1 | tee results/phase3/build.log
source install/setup.bash
colcon test --packages-select predictive_motion_control --event-handlers console_direct+ 2>&1 | tee results/phase3/test.log
colcon test-result --test-result-base build/predictive_motion_control --verbose 2>&1 | tee results/phase3/test-results.log
cp config/phase3.yaml results/phase3/frozen_design.yaml
sha256sum config/phase3.yaml > results/phase3/design.sha256
date -u +%FT%TZ > results/phase3/design_frozen_at.txt
sha=$(sha256sum config/phase3.yaml | cut -d ' ' -f1)
robot="$root/src/predictive_motion_kinematics/config/fr3.yaml"
scene="$root/.vendor/menagerie/franka_fr3/scene.xml"
install/predictive_motion_control/lib/predictive_motion_control/phase3_numerical "$robot" config/phase3.yaml results/phase3/numerical 2>&1 | tee results/phase3/numerical.log
install/predictive_motion_control/lib/predictive_motion_control/phase3_benchmark "$robot" "$scene" config/phase3.yaml results/phase3/development development results/phase3/selection.yaml "$sha" 2>&1 | tee results/phase3/development.log
sha256sum results/phase3/selection.yaml > results/phase3/selection.sha256
date -u +%FT%TZ > results/phase3/selection_frozen_at.txt
install/predictive_motion_control/lib/predictive_motion_control/phase3_benchmark "$robot" "$scene" config/phase3.yaml results/phase3/evaluation evaluation results/phase3/selection.yaml "$sha" 2>&1 | tee results/phase3/evaluation.log
cmake -S tests/integration/nullspace_consumer -B build/nullspace_consumer 2>&1 | tee results/phase3/consumer-build.log
cmake --build build/nullspace_consumer --parallel 2 2>&1 | tee -a results/phase3/consumer-build.log
(cd /tmp; "$root/build/nullspace_consumer/nullspace_consumer") | tee results/phase3/consumer.log
ldd build/nullspace_consumer/nullspace_consumer | tee results/phase3/consumer-runtime.log
install/predictive_motion_control/lib/predictive_motion_control/observation_contract "$robot" "$scene" results/phase3/observation_contract.csv | tee results/phase3/observation_contract.log
bash scripts/phase3/check_artifacts.sh

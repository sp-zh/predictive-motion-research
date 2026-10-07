#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
source /opt/ros/jazzy/setup.bash
source install/setup.bash
out=results/phase2-observation-sync
mkdir -p "$out"
sha256sum -c results/phase2/design.sha256
sha256sum -c results/phase2/selection.sha256
sha256sum -c results/phase2/weak-design.sha256
sha=$(sha256sum config/phase2.yaml | cut -d ' ' -f1)
robot=src/predictive_motion_kinematics/config/fr3.yaml
scene=.vendor/menagerie/franka_fr3/scene.xml
install/predictive_motion_control/lib/predictive_motion_control/observation_contract "$robot" "$scene" "$out/observation_contract.csv" | tee "$out/observation_contract.log"
runner=install/predictive_motion_control/lib/predictive_motion_control/phase2_benchmark
"$runner" "$robot" "$scene" config/phase2.yaml "$out/development" development "$out/corrected_development_ranking.yaml" "$sha" | tee "$out/development.log"
# This ranking is diagnostic only. Historical selection is always used for the following runs.
"$runner" "$robot" "$scene" config/phase2.yaml "$out/evaluation" evaluation results/phase2/selection.yaml "$sha" | tee "$out/evaluation.log"
"$runner" "$robot" "$scene" config/phase2_weak.yaml "$out/weak_direction" weak-direction results/phase2/selection.yaml "$sha" | tee "$out/weak-direction.log"
python3 scripts/phase3/audit_observation_sync.py | tee "$out/evidence-audit.log"

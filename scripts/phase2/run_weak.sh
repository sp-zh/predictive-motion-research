#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
source /opt/ros/jazzy/setup.bash
source install/setup.bash
mkdir -p results/phase2
# Supplementary post-evaluation diagnostic; never changes the original design or selection.
if [ ! -f config/phase2_weak.yaml ]; then
  cp config/phase2.yaml config/phase2_weak.yaml
  printf '\n# Supplementary dynamic weak-direction diagnostic, excluded from tuning/evaluation.\nweak_seeds: [3101, 3102]\nweak_reference_amplitude: 0.002\n' >> config/phase2_weak.yaml
fi
cp config/phase2_weak.yaml results/phase2/frozen_weak_design.yaml
sha256sum config/phase2_weak.yaml > results/phase2/weak-design.sha256
date -u +%FT%TZ > results/phase2/weak_design_frozen_at.txt
sha256sum -c results/phase2/design.sha256
sha256sum -c results/phase2/selection.sha256
design_hash=$(sha256sum config/phase2.yaml | cut -d ' ' -f1)
"$root/install/predictive_motion_control/lib/predictive_motion_control/phase2_benchmark" src/predictive_motion_kinematics/config/fr3.yaml .vendor/menagerie/franka_fr3/scene.xml config/phase2_weak.yaml results/phase2/weak_direction weak-direction results/phase2/selection.yaml "$design_hash" 2>&1 | tee results/phase2/weak-direction.log

#!/usr/bin/env bash
# Runs inside the candidate with a fresh checkout mounted at /work.
set -eo pipefail
kind=${1:?copy-base, build-ci or verify-public-ci}
[[ $kind == copy-base || $kind == build-ci || $kind == verify-public-ci ]] || exit 1
record_environment() {
  status=$?
  trap - EXIT
  set +e
  # Diagnostics cannot replace the original install/test failure exit status.
  if [[ -f /opt/ros/jazzy/setup.bash ]]; then
    # shellcheck disable=SC1091 # ROS is provided by the candidate image.
    source /opt/ros/jazzy/setup.bash
  fi
  python3 scripts/collect_environment.py --output results/phase0/environment.json
  diagnostic_status=$?
  if [[ $status == 0 ]]; then exit "$diagnostic_status"; fi
  exit "$status"
}
trap record_environment EXIT
if [[ $kind == copy-base ]]; then
  bash scripts/phase0/setup_linux.sh
else
  python3 scripts/check_ci_environment.py check
  mkdir -p results/ci-images
  cp /usr/local/share/predictive-motion-ci/{metadata.json,installed-packages.tsv} results/ci-images/
  for path in .git src build install log .vendor .cache; do
    test ! -e "/workspaces/predictive_motion/$path"
  done
fi
bash scripts/ci.sh

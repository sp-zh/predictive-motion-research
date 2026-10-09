#!/usr/bin/env bash
# Runs inside the freshly pulled candidate; no registry credentials enter it.
set -eo pipefail
record_environment() {
  rc=$?
  trap - EXIT
  if [[ -f /opt/ros/jazzy/setup.bash ]]; then
    # shellcheck disable=SC1091 # provided by the validated ROS image
    source /opt/ros/jazzy/setup.bash
    if ! python3 scripts/collect_environment.py --output results/phase0/environment.json; then
      echo 'Environment recording failed; retaining primary test exit code' >&2
      if [[ $rc == 0 ]]; then rc=1; fi
    fi
  fi
  exit "$rc"
}
trap record_environment EXIT
case "$CI_IMAGE_STAGE" in
  base)
    python3 scripts/ci/check_environment.py --base-only
    bash scripts/phase0/setup_linux.sh
    ;;
  ci) python3 scripts/ci/check_environment.py ;;
  *) echo 'Unknown image stage' >&2; exit 1 ;;
esac
# Each stage uses this exact entrypoint at the same checked-out source commit.
bash scripts/ci.sh

#!/usr/bin/env bash
# Called only by the trusted, default-branch dispatch publisher job.
set -euo pipefail
mode=${1:?copy-base or build-ci}
base=${2:-}
repo=sp-zh/predictive-motion-research
[[ ${GITHUB_REPOSITORY:-} == "$repo" && ${GITHUB_REF:-} == refs/heads/master && ${GITHUB_EVENT_NAME:-} == workflow_dispatch ]] || { echo 'Trusted default-branch dispatch required' >&2; exit 1; }
[[ $mode == copy-base || $mode == build-ci ]] || exit 1
[[ ${GITHUB_SHA:-} =~ ^[0-9a-f]{40}$ && ${GITHUB_RUN_ID:-} =~ ^[0-9]+$ && ${GITHUB_RUN_ATTEMPT:-} =~ ^[0-9]+$ ]] || exit 1
suffix=ros-base
[[ $mode == copy-base ]] || suffix=ci
package=predictive-motion-research-$suffix
image=ghcr.io/sp-zh/$package
tag=$GITHUB_SHA-$GITHUB_RUN_ID-$GITHUB_RUN_ATTEMPT
mkdir -p results/ci-images
# Fail on unavailable metadata or unlinked/foreign packages; never assume 403 means absent.
if gh api "users/sp-zh/packages/container/$package" > results/ci-images/package.json 2> results/ci-images/package-error.txt; then
  python3 - <<'PYCODE'
import json
from pathlib import Path
p=json.loads(Path('results/ci-images/package.json').read_text())
assert p.get('repository', {}).get('full_name') == 'sp-zh/predictive-motion-research', 'Package ownership/link is not confirmed'
PYCODE
  gh api --paginate "users/sp-zh/packages/container/$package/versions?per_page=100" --jq '.[].metadata.container.tags[]' > results/ci-images/existing-tags.txt
  if grep -Fxq "$tag" results/ci-images/existing-tags.txt; then echo 'Refusing to overwrite release tag' >&2; exit 1; fi
else
  grep -q 'HTTP 404' results/ci-images/package-error.txt || { cat results/ci-images/package-error.txt >&2; exit 1; }
fi
export DOCKER_CONFIG
DOCKER_CONFIG=$(mktemp -d)
build_context=
trap 'rm -rf "$DOCKER_CONFIG"; if [[ -n $build_context ]]; then rm -rf "$build_context"; fi' EXIT
printf '%s' "$GH_TOKEN" | docker login ghcr.io -u "$GITHUB_ACTOR" --password-stdin
if [[ $mode == copy-base ]]; then
  if [[ -n ${DOCKERHUB_USERNAME:-} || -n ${DOCKERHUB_TOKEN:-} ]]; then
    [[ -n ${DOCKERHUB_USERNAME:-} && -n ${DOCKERHUB_TOKEN:-} ]] || { echo 'Both Docker Hub secrets required' >&2; exit 1; }
    printf '%s' "$DOCKERHUB_TOKEN" | docker login docker.io -u "$DOCKERHUB_USERNAME" --password-stdin
  fi
  # Read the retained official source lock (also the current daily CI base).
  source_image=$(python3 - <<'PYCODE'
import re
from pathlib import Path
text=Path('docker/Dockerfile').read_text()
match=re.search(r'FROM (?:docker.io/library/)?(ros:jazzy-ros-base-noble@sha256:[0-9a-f]{64})', text)
assert match, 'Development Dockerfile no longer defines the expected locked ROS source; review before mirroring'
print('docker.io/library/' + match[1])
PYCODE
)
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends skopeo
  # skopeo reads only this job's isolated Docker auth file.
  skopeo inspect --authfile "$DOCKER_CONFIG/config.json" --raw "docker://$source_image" > results/ci-images/source-index.json
  source_platform=$(python3 - <<'PYCODE'
import json
from pathlib import Path
m=json.loads(Path('results/ci-images/source-index.json').read_text())
v=[x['digest'] for x in m['manifests'] if x.get('platform', {}).get('os') == 'linux' and x.get('platform', {}).get('architecture') == 'amd64']
assert len(v)==1, 'Exactly one linux/amd64 source manifest required'
print(v[0])
PYCODE
)
  source_platform_ref="${source_image%@*}@$source_platform"
  skopeo inspect --authfile "$DOCKER_CONFIG/config.json" --raw "docker://$source_platform_ref" > results/ci-images/source-manifest.json
  skopeo copy --authfile "$DOCKER_CONFIG/config.json" --override-os linux --override-arch amd64 "docker://$source_platform_ref" "docker://$image:$tag"
  skopeo inspect --authfile "$DOCKER_CONFIG/config.json" --raw "docker://$image:$tag" > results/ci-images/target-manifest.json
  digest=sha256:$(sha256sum results/ci-images/target-manifest.json | cut -d ' ' -f 1)
  python3 - "$source_image" "$source_platform_ref" "$image@$digest" <<'PYCODE'
import json, sys
from pathlib import Path
s=json.loads(Path('results/ci-images/source-manifest.json').read_text())
t=json.loads(Path('results/ci-images/target-manifest.json').read_text())
assert s['config']['digest']==t['config']['digest'] and s['layers']==t['layers'], 'Source/target content mismatch'
Path('results/ci-images/base-copy.json').write_text(json.dumps(dict(source_index=sys.argv[1], source_platform_manifest=sys.argv[2], target_manifest=sys.argv[3], platform='linux/amd64', config=s['config']['digest'], layers=[x['digest'] for x in s['layers']]), indent=2)+'\n')
PYCODE
else
  [[ $base =~ ^ghcr\.io/sp-zh/predictive-motion-research-ros-base@sha256:[0-9a-f]{64}$ ]] || { echo 'Reviewed project GHCR base digest required' >&2; exit 1; }
  # Caller must choose the base-copy digest whose full Stage A test run passed.
  gh api users/sp-zh/packages/container/predictive-motion-research-ros-base --jq '.repository.full_name' | grep -Fx "$repo"
  docker pull --platform linux/amd64 "$base"
  setup_hash=$(sha256sum scripts/phase0/setup_linux.sh | cut -d ' ' -f 1)
  env_hash=$(python3 scripts/check_ci_environment.py hash)
  # Stage an explicit four-file context; unrelated workspace data never reaches Docker.
  build_context=$(mktemp -d)
  mkdir -p "$build_context/scripts/phase0" "$build_context/docker"
  cp scripts/phase0/setup_linux.sh "$build_context/scripts/phase0/"
  cp scripts/check_ci_environment.py "$build_context/scripts/"
  cp docker/Dockerfile.ci docker/Dockerfile.ci.dockerignore "$build_context/docker/"
  # Docker's default driver uses the installed engine's BuildKit, no builder image.
  DOCKER_BUILDKIT=1 docker build --platform linux/amd64 -f "$build_context/docker/Dockerfile.ci" \
    --build-arg ROS_BASE_IMAGE="$base" --build-arg SOURCE_COMMIT="$GITHUB_SHA" \
    --build-arg SETUP_SHA256="$setup_hash" --build-arg ENVIRONMENT_SHA256="$env_hash" -t "$image:$tag" "$build_context"
  docker push "$image:$tag" | tee results/ci-images/push.log
  # Registry digest from remote manifest, never a local image/config ID.
  docker manifest inspect "$image:$tag" > results/ci-images/target-manifest.json
  digest=$(sed -nE 's/.*digest: (sha256:[0-9a-f]{64}).*/\1/p' results/ci-images/push.log | tail -1)
  [[ $digest =~ ^sha256:[0-9a-f]{64}$ ]] || exit 1
  docker manifest inspect "$image@$digest" > results/ci-images/digest-manifest.json
  cmp results/ci-images/target-manifest.json results/ci-images/digest-manifest.json
  docker image rm "$image:$tag"
fi
# Resolve and pull again from GHCR by the newly obtained registry digest.
docker pull --platform linux/amd64 "$image@$digest"
[[ $(docker image inspect "$image@$digest" --format '{{.Os}}/{{.Architecture}}') == linux/amd64 ]]
docker run --rm --entrypoint bash "$image@$digest" -ec 'source /etc/os-release; test "$ID" = ubuntu; test "$VERSION_ID" = 24.04; test -f /opt/ros/jazzy/setup.bash'
printf 'image=%s\nkind=%s\n' "$image@$digest" "$mode" >> "$GITHUB_OUTPUT"
# shellcheck disable=SC2016 # Markdown backticks are literal, not substitutions.
printf '## Candidate (%s)\n- Registry manifest: `%s@%s`\n- Platform: `linux/amd64` only\n- Source commit: `%s`\n- Tag: `%s`\n- Registry re-pull and OS/architecture checks passed. Full tests run in the separate read-only job.\n' "$mode" "$image" "$digest" "$GITHUB_SHA" "$tag" >> "$GITHUB_STEP_SUMMARY"

#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cache=${PM_CACHE:-$root/.cache}
mkdir -p "$cache"
archive=mujoco-3.3.7-linux-x86_64.tar.gz
digest=1895a2f71e86d9a6026703ebdc1fae32af07792805ac56f9a73abceca30dbe1c
commit=4d038b3feae26ec82b46a4d586379114012a8ac7
if [[ ! -f "$cache/$archive" ]]; then curl -fL --retry 2 --connect-timeout 20 --max-time 180 "https://github.com/google-deepmind/mujoco/releases/download/3.3.7/$archive" -o "$cache/$archive"; fi
echo "$digest  $cache/$archive" | sha256sum -c -
# Extract binaries to native Linux storage rather than a Windows drive.
if [[ ! -d "$root/.vendor/mujoco-3.3.7" ]]; then mkdir -p "$root/.vendor"; tar -xzf "$cache/$archive" -C "$root/.vendor"; fi
if [[ ! -d "$root/.vendor/menagerie/.git" ]]; then git clone --filter=blob:none --no-checkout https://github.com/google-deepmind/mujoco_menagerie.git "$root/.vendor/menagerie"; fi
git -C "$root/.vendor/menagerie" sparse-checkout init --cone
git -C "$root/.vendor/menagerie" sparse-checkout set franka_fr3
git -C "$root/.vendor/menagerie" fetch origin "$commit"
git -C "$root/.vendor/menagerie" checkout --detach "$commit"
mkdir -p "$cache/manifests"
(cd "$root/.vendor/menagerie"; find franka_fr3 -type f -print0 | sort -z | xargs -0 sha256sum) > "$cache/manifests/fr3.sha256"
if [[ -f "$root/src/predictive_motion_description/manifests/fr3.sha256" ]]; then
  (cd "$root/.vendor/menagerie"; sha256sum -c "$root/src/predictive_motion_description/manifests/fr3.sha256")
fi
cp "$root/.vendor/menagerie/franka_fr3/LICENSE" "$cache/manifests/FR3_LICENSE"
cp "$root/.vendor/mujoco-3.3.7/THIRD_PARTY_NOTICES" "$cache/manifests/MUJOCO_THIRD_PARTY_NOTICES" 2>/dev/null || true
echo "FR3_MODEL=$root/.vendor/menagerie/franka_fr3/scene.xml"

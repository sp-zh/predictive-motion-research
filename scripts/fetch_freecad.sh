#!/usr/bin/env bash
set -euo pipefail
[[ $(uname -s) == Linux && $(uname -m) == x86_64 ]] || { echo 'This locked FreeCAD runtime targets Linux x86_64'; exit 1; }
root=$(cd "$(dirname "$0")/.." && pwd)
cache=${PM_CACHE:-$root/.cache}
runtime="$root/.vendor/freecad-1.1.4"
archive="$cache/FreeCAD_1.1.4-Linux-x86_64-py311.AppImage"
digest=f6dc6ba676e5ac96a565ebc8d657232f94c6158e85b4352141bd1a46f6b43434
mkdir -p "$cache" "$root/.vendor"
if [[ ! -f "$archive" ]] || ! echo "$digest  $archive" | sha256sum -c --status; then
  curl -fL --retry 2 --connect-timeout 20 --max-time 600 --continue-at - \
    https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/FreeCAD_1.1.4-Linux-x86_64-py311.AppImage -o "$archive"
fi
echo "$digest  $archive" | sha256sum -c -
if [[ ! -f "$runtime/READY" ]]; then
  mkdir -p "$runtime"
  # NTFS cache mounts may reject chmod; execute a verified native-filesystem copy.
  cp "$archive" "$runtime/extractor.AppImage"
  chmod +x "$runtime/extractor.AppImage"
  (cd "$runtime"; ./extractor.AppImage --appimage-extract > extraction.log)
  rm "$runtime/extractor.AppImage"
  printf '%s\n' "$digest" > "$runtime/READY"
fi
echo "FreeCAD runtime: $runtime/squashfs-root"

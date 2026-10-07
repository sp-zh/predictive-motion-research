#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
runtime="$root/.vendor/freecad-1.1.4/squashfs-root"
[[ -x "$runtime/AppRun" ]] || { echo 'Run scripts/fetch_freecad.sh first'; exit 1; }
export PM_PROJECT_ROOT="$root"
export PYTHONPATH="$root/cad/scripts:$runtime/usr/lib${PYTHONPATH:+:$PYTHONPATH}"
# Import by module name so saved FeaturePython proxies survive a fresh process.
"$runtime/AppRun" python -c 'import os; from pathlib import Path; import generate_inspection as cad; root=Path(os.environ["PM_PROJECT_ROOT"]); cad.generate(Path(os.environ.get("PM_CAD_CONFIG",root/"cad/source/inspection.json")),Path(os.environ.get("PM_CAD_OUTPUT",root/"cad/generated")))'
"$runtime/AppRun" python "$root/cad/scripts/verify_saved_cad.py"

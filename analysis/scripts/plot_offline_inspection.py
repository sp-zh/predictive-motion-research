"""Plot recorded discrete IK screening; no executed-controller data are implied."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
with (args.input/'feasible_path.csv').open() as f:
    rows = list(csv.DictReader(f))
data = {key: np.asarray([float(row[key]) for row in rows]) for key in rows[0]}
summary = json.loads((args.input/'summary.json').read_text())
if summary['status'] != 'PASS' or summary['controller_trial'] or len(rows) != summary['samples']:
    raise ValueError('Expected passing offline screening evidence')
fig = plt.figure(figsize=(11, 8), layout='constrained')
ax = fig.add_subplot(221, projection='3d')
ax.plot(data['x'], data['y'], data['z'], '.-', ms=2)
ax.scatter(data['x'][[0,-1]], data['y'][[0,-1]], data['z'][[0,-1]], c=['green','red'])
ax.set(xlabel='World x (m)', ylabel='World y (m)', zlabel='World z (m)', title='Recorded discrete IK reference poses')
ax.set_box_aspect([3, 1, 1])
for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
    axis.set_major_locator(MaxNLocator(4))
ax.tick_params(labelsize=8, pad=1)
ax = fig.add_subplot(222)
for j in range(1,8):
    ax.plot(data['s'], data[f'q{j}'], label=f'q{j}')
ax.set(xlabel='Path progress s', ylabel='Joint position (rad)', title='Offline IK branch (no time law)')
ax.legend(ncol=4, fontsize=8)
ax.grid(alpha=.25)
ax = fig.add_subplot(223)
ax.plot(data['s'], 1000*data['tool_fixture_clearance_lower_bound_m'], label='Full tool, all fixture components')
ax.axhline(5, color='red', linestyle='--', label='Screening threshold')
ax.set(xlabel='Path progress s', ylabel='Clearance lower bound (mm)', title='Conservative world-AABB separation')
ax.legend(fontsize=8)
ax.grid(alpha=.25)
ax = fig.add_subplot(224)
ax.semilogy(data['s'], data['position_error_m'], label='Position (m)')
ax.semilogy(data['s'], data['rotation_error_rad'], label='Rotation (rad)')
ax.set(xlabel='Path progress s', ylabel='FK error', title='Physical TCP versus desired pose')
ax.legend(fontsize=8)
ax.grid(alpha=.25)
fig.suptitle(f'{len(rows)} offline poses — no executed controller or continuous collision guarantee')
args.output.mkdir(parents=True, exist_ok=True)
fig.savefig(args.output/'offline_inspection_screening.png', dpi=160)
manifest = {'scope': 'discrete offline IK screening', 'numpy': np.__version__, 'matplotlib': matplotlib.__version__, 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'figure_sha256': hashlib.sha256((args.output/'offline_inspection_screening.png').read_bytes()).hexdigest(), 'inputs': {name: hashlib.sha256((args.input/name).read_bytes()).hexdigest() for name in ['feasible_path.csv','summary.json','attempts.csv']}}
(args.output/'offline_inspection_figure_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')

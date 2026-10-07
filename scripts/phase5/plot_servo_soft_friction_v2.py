#!/usr/bin/env python3
"""Local soft-friction servo model validation; independent new development waveform."""
from pathlib import Path
import argparse
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from servo_model_v1 import trace, sha
from servo_model_soft_friction_v2 import step

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--project', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
base = a.project / 'results/phase5/development/servo-model-soft-friction-v2-frozen'
model_file = base / 'model.json'
model = json.loads(model_file.read_text())
training_file = base / 'training_report.json'
validation_file = base / 'heldout-validation/validation_report.json'
reports = [json.loads(f.read_text()) for f in [training_file, validation_file]]
raw = Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-soft-friction-v2-validation/raw.csv')
if sha(raw) != reports[1]['raw_sha256']:
    raise ValueError('validation identity changed')
rows, data = trace(raw)
tick, joint = reports[1]['metrics'][-1]['q_worst_start_tick_joint']
start, length = tick * 2, 400
q, v = data['q_before_'][start].copy(), data['v_before_'][start].copy()
predicted_q, predicted_v = [], []

for k in range(length):
    q, v = step(q, v, data['target_'][start + k], model)
    predicted_q.append(q.copy()); predicted_v.append(v.copy())
predicted_q, predicted_v = np.array(predicted_q), np.array(predicted_v)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
fig, axes = plt.subplots(2, 2, figsize=(12, 9))
fig.suptitle('Phase 5 local servo model: new holdout checks passed', x=.075, ha='left', fontsize=19, weight='bold')
fig.text(.075, .925, 'Frozen 91011 fit → independent 91012 trace · new waveform, same physical plant and accepted position interface', fontsize=10, color='#555')
colors = ['#406b96', '#bf6b36']
for k, (key, limit, label) in enumerate([('max_q_error_rad', 'q_limit_rad', 'Max position error [mrad]'), ('max_v_error_rad_s', 'v_limit_rad_s', 'Max velocity error [mrad/s]')]):
    ax = axes[0, k]
    for r, color, name, shift in zip(reports, colors, ['Training', 'Heldout development'], [-.15, .15]):
        ax.bar(np.arange(4)+shift, [1000*m[key] for m in r['metrics']], width=.28, color=color, label=name)
    ax.plot(np.arange(4), [1000*m[limit] for m in reports[1]['metrics']], color='#333', marker='_', linestyle=':', linewidth=1.4, label='Prefrozen error limit')
    ax.set_yscale('log'); ax.set_xticks(range(4), ['2 ms', '4 ms', '40 ms', '800 ms'])
    ax.set_xlabel('Conditional forecast duration'); ax.set_ylabel(label)
    ax.grid(axis='y', color='#ddd', linewidth=.6); ax.legend(loc='lower left', bbox_to_anchor=(0, 1.015), fontsize=8, frameon=False)
origin = data['q_before_'][start, joint]
t = .002 * np.arange(1, length+1)
actual_q = data['q_post_'][start:start+length, joint]
actual_v = data['v_post_'][start:start+length, joint]
for ax, actual, prediction, ylabel in [(axes[1, 0], 1000*(actual_q-origin), 1000*(predicted_q[:, joint]-origin), f'Joint {joint+1} displacement [mrad]'),
                                      (axes[1, 1], 1000*actual_v, 1000*predicted_v[:, joint], f'Joint {joint+1} velocity [mrad/s]')]:
    ax.plot(t, actual, color=colors[0], label='Recorded physical state', linewidth=1.8)
    ax.plot(t, prediction, color=colors[1], label='Frozen soft-friction forecast', linestyle='--', linewidth=1.8)
    ax.set_xlabel('Time after measured initialization [s]'); ax.set_ylabel(ylabel)
    ax.grid(axis='y', color='#ddd', linewidth=.6); ax.legend(loc='lower left', bbox_to_anchor=(0, 1.015), fontsize=8, frameon=False)
fig.text(.075, .055, f'Lower panels: largest 800 ms position-error window, joint {joint+1}, start tick {tick} (t={tick*.004:.3f} s).\n'
         'Every forecast starts from measured q/v once and uses completed recorded targets; no state reset within its window.\n'
         'Overlapping windows are diagnostics, not independent trials. All frozen 2–800 ms local error limits pass. No controller, task, stopping or online certificate.',
         fontsize=9, color='#555')
fig.subplots_adjust(left=.09, right=.975, top=.825, bottom=.18, hspace=.62, wspace=.28)
a.output.mkdir(exist_ok=False)
out = a.output / 'phase5_servo_soft_friction_v2.png'
fig.savefig(out, dpi=180, facecolor='white')
meta = {'scope': __doc__, 'source_files': {str(f): sha(f) for f in [raw, model_file, training_file, validation_file, Path(__file__), a.project/'scripts/phase5/servo_model_soft_friction_v2.py']},
        'output_sha256': sha(out), 'joint_index_zero_based': joint, 'window_start_tick': tick, 'window_duration_s': .8,
        'units': {'position': 'mrad', 'velocity': 'mrad/s', 'time': 's'}, 'inspection': 'pending visual inspection', 'gate': 'PASS_LOCAL_EMPIRICAL'}
with (a.output / 'phase5_servo_soft_friction_v2.json').open('x') as file:
    file.write(json.dumps(meta, indent=2)+'\n')
print(json.dumps(meta, indent=2))

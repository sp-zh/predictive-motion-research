"""Render retained file diagnostics; no model, solve, motion or acceptance."""
from pathlib import Path
import collections
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REVIEW = ROOT / 'reviews/evidence/phase5_task_start_a_v1_20261010/independent'
ready_bytes = (REVIEW / 'READY.json').read_bytes()
assert hashlib.sha256(ready_bytes).hexdigest() == 'a7cecbf2181485032cbf52af5090ce6be7321a7742d4219923a93add8068b099'
ready = json.loads(ready_bytes)
data_bytes = (REVIEW / 'results.json').read_bytes()
pin = ready['files']['results.json']
assert len(data_bytes) == pin['bytes'] and hashlib.sha256(data_bytes).hexdigest() == pin['sha256']
data = json.loads(data_bytes)
native = data['native_result']['forensic_diagnostics']
reference = data['external_reference']['diagnostics']
assert not data['external_reference']['literal_history_PASS']
assert data['native_result']['usable_count'] == 0

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), layout='constrained')
keys = ['F', 'H', 'g', 'lower', 'upper']
errors = [data['checks'][key] for key in keys]
axes[0].bar(keys, errors, color='#246a9b')
axes[0].set_yscale('log')
axes[0].set(title='Independent saved-QP regeneration', ylabel='Maximum absolute coefficient discrepancy\n(units vary by array)')
for i, value in enumerate(errors):
    axes[0].annotate(f'{value:.2g}', (i, value), xytext=(0, 5), textcoords='offset points', ha='center', fontsize=8)

values = [native['maximum_original_SI_violation'], reference['maximum_original_SI_violation']]
axes[1].bar(['Native unsolved\nforensic iterate', 'External SLSQP\nreference'], values, color=['#b04d42', '#92713e'])
axes[1].set_yscale('log')
axes[1].axhline(1e-7, color='#555555', ls='--', label='Original SI tolerance 1e-7')
axes[1].set(title='Full original row scan (diagnostic)', ylabel='Worst feedback-jerk violation (1/s³)')
axes[1].legend(fontsize=8)
for i, value in enumerate(values):
    axes[1].annotate(f'{value:.3g}', (i, value), xytext=(0, 5), textcoords='offset points', ha='center', fontsize=8)

counts = []
labels = []
colors = []
for name, result, color in [('Native forensic', native, '#b04d42'), ('SLSQP reference', reference, '#92713e')]:
    for kind, count in sorted(collections.Counter(row['kind'] for row in result['literal_history_failures']).items()):
        labels.append(name + '\n' + kind.replace('_', ' '))
        counts.append(count)
        colors.append(color)
axes[2].barh(labels, counts, color=colors)
axes[2].set(title='Literal strict-history failures', xlabel='Retained failing checks (not a method ranking)')
for i, count in enumerate(counts):
    axes[2].text(count + .5, i, str(count), va='center', fontsize=9)
axes[2].set_xlim(0, max(counts) * 1.15)
for axis in axes:
    axis.grid(axis='y', alpha=.18)
fig.suptitle('Same saved task-start development QP · exact input identity; no executable candidate', fontsize=15)
fig.supxlabel('Native MAX_ITERATIONS; reference fails strict progress history. Inline geometry absent; nonlinear B pending.\nZero task commits; no control replay or Phase 5 acceptance. No tolerance change, clamp or hidden state reset.', fontsize=10)
for suffix in ['png', 'svg']:
    fig.savefig(OUT / ('diagnostics.' + suffix), dpi=170, bbox_inches='tight')
provenance = {'schema': 'ROOT_TASK_START_A_DIAGNOSTIC_FIGURE_V1', 'review_ready_sha256': hashlib.sha256(ready_bytes).hexdigest(), 'review_results_sha256': hashlib.sha256(data_bytes).hexdigest(), 'renderer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'scope': 'Independent saved-file diagnostics only; same actual A2 matrices. No method ranking, executed controls or research acceptance.', 'data': {'regeneration_errors': dict(zip(keys, errors)), 'worst_original_jerk_violations': values, 'strict_counts': dict(zip(labels, counts))}, 'files': {p.name: {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUT.iterdir()) if p.suffix in ['.png', '.svg']}, 'phase5': 'NOT_ACCEPTED'}
(OUT / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')

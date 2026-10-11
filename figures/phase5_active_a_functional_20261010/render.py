"""Plot actual offline development solver timings, never physical motion."""
from pathlib import Path
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / 'reviews/evidence/phase5_active_a_functional_20261010/ACTUAL_SUMMARY.json'
data = json.loads(SOURCE.read_text())
EXTRA = HERE.parents[1] / 'reviews/evidence/phase5_active_a_numeric_repairs_20261010/ACTUAL_SUMMARY.json'
extra = json.loads(EXTRA.read_text())
rows = data['attempts'] + extra['attempts']
labels = ['Original coordinates', 'Jacobi + row scaling', 'Scaling + exact box screen',
          '20k iteration budget', 'Full SPD whitening', 'Terminal equality elimination',
          'Equality elimination + bounded row scale']
colors = ['#527b9d', '#4a928f', '#8974a5', '#927c63', '#b57672', '#65898e', '#648363']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.8), layout='constrained')
for ax, key, factor, title in zip(axes,
        ['setup_seconds', 'solve_seconds', 'iterations'], [1000, 1, 1],
        ['Native setup (ms)', 'Native solve (s)', 'Iterations completed']):
    values = [r[key] * factor for r in rows]
    bars = ax.bar(range(len(rows)), values, color=colors, width=.62)
    ax.set_title(title, loc='left', weight='bold')
    ax.set_xticks(range(len(rows)), [r['version'] for r in rows], rotation=45)
    ax.set_ylim(0, max(values) * 1.25)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', alpha=.18)
    ax.set_axisbelow(True)
    ax.bar_label(bars, labels=[f'{v:.2f}' if factor != 1 or key != 'iterations' else str(int(v)) for v in values], padding=4)
fig.suptitle('Actual active-session QP attempts — all rejected at original precision', x=.035, ha='left', weight='bold', fontsize=14)
fig.supxlabel('TIME_LIMIT: repair1, repair3, repair10   •   MAX_ITERATIONS: repair6, repair7, repair12, repair14\n'
              'Different declared budgets (5s/4k vs 20s/20k); development diagnostics, not a matched ranking.\n'
              'Usable candidates = 0, original SI candidate scans = 0, physical steps = 0, commits = 0', fontsize=10)
for extension in ['png', 'svg']:
    fig.savefig(HERE / f'qp_attempts.{extension}', dpi=180)
plt.close(fig)
provenance = {
    'schema': 'ACTUAL_ACTIVE_A_TIMING_FIGURE_V1',
    'sources': {str(p.relative_to(HERE.parents[1])): hashlib.sha256(p.read_bytes()).hexdigest() for p in [SOURCE, EXTRA]},
    'packet_ready_sha256': [data['ready_sha256'], extra['packet_ready_sha256']],
    'attempt_labels': dict(zip([r['version'] for r in rows], labels)),
    'render_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'matplotlib': matplotlib.__version__,
    'figures': {p.name: {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in HERE.glob('qp_attempts.*')},
    'scope': 'Recorded native setup/solve subsets and iterations, not full-cycle latency, physical performance, research ranking or Phase5 acceptance. No motion render or task video is claimed.',
    'phase5': 'NOT_ACCEPTED', 'phase6': 'NOT_STARTED'
}
(HERE / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')

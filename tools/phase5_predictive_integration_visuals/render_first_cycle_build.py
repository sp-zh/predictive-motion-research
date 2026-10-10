"""Plot one actual compile/link batch; never execute its produced program."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ['review', 'data', 'output-dir']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_text())
    data = json.loads(args.data.read_text())
    assert review['decision'] == 'PASS_ONE_FIRST_CYCLE_COMPILE_LINK_BATCH_ONLY_RUNTIME_CLOSED'
    assert review['public_build_data_sha256'] == sha(args.data)
    records = data['entries']
    assert [row['kind'] for row in records] == ['compile'] * 7 + ['link']
    assert all(row['exit'] == 0 for row in records)
    assert data['program_runtime'] == 0
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none',
                         'svg.hashsalt': 'first-cycle-actual-build-v1'})
    fig = plt.figure(figsize=(13, 7.5), dpi=180, facecolor='white')
    ink, blue, gray = '#172B46', '#2864B0', '#667180'
    fig.text(.06, .91, 'First-cycle program: actual build completed', fontsize=24,
             weight='bold', color=ink)
    fig.text(.06, .855, 'One configure · seven compiler entries · one link · program not run',
             fontsize=14, color=gray)
    ax = fig.add_axes([.25, .28, .65, .51])
    labels = [row['label'] for row in records]
    durations = [row['wall_seconds'] for row in records]
    ax.barh(range(8), durations, color=[blue] * 7 + ['#537D73'], height=.62)
    ax.set_yticks(range(8), labels, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlim(0, max(durations) * 1.25)
    for y, value in enumerate(durations):
        ax.text(value + max(durations) * .025, y, f'{value:.3f} s', va='center',
                fontsize=11, color=ink)
    ax.set_xlabel('Observed process wall time (seconds)', fontsize=11, color=gray)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', color='#E6EBEF', linewidth=.7)
    ax.set_axisbelow(True)
    fig.text(.06, .19, 'Exact staged source and input guards checked; compiler warnings retained.',
             fontsize=12, color=gray)
    fig.text(.06, .13, 'Build timings are not solver latency, robot tracking or an online 4 ms result.',
             fontsize=12, color=gray)
    fig.text(.06, .065, 'Phase 5 NOT_ACCEPTED · Phase 6 NOT_STARTED', fontsize=14,
             weight='bold', color=ink)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    names = ['first_cycle_actual_build.png', 'first_cycle_actual_build.svg']
    for name in names:
        fig.savefig(args.output_dir / name, dpi=180, facecolor='white',
                    metadata={'Date': None} if name.endswith('.svg') else None)
    plt.close(fig)
    provenance = {
        'scope': 'Actual ordinary compile/link process timings; no produced-program runtime',
        'review_sha256': sha(args.review), 'data_sha256': sha(args.data),
        'selection': 'All seven compiler entries and the sole link; no excluded attempts',
        'renderer': {'script': Path(__file__).name, 'sha256': sha(Path(__file__)),
                     'matplotlib': matplotlib.__version__, 'font': 'DejaVu Sans',
                     'dpi': 180, 'figure_inches': [13, 7.5]},
        'outputs': [{'file': name, 'bytes': (args.output_dir / name).stat().st_size,
                     'sha256': sha(args.output_dir / name)} for name in names],
        'phase5': 'NOT_ACCEPTED', 'phase6': 'NOT_STARTED'}
    (args.output_dir / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps(provenance['outputs']))


if __name__ == '__main__':
    main()

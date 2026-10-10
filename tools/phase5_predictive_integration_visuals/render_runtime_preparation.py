"""Show reviewed source and prospective runtime gates; no simulated motion."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--review', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args()
    review = json.loads(args.review.read_text())
    assert review['decision'] == 'PASS_RUNTIME_PREPARATION_V2_SOURCE_ONLY_PROFILE_STAGE_AND_EXECUTION_CLOSED'
    assert review['native_project_calls'] == 0
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none',
                         'svg.hashsalt': 'first-cycle-runtime-preparation-v2'})
    fig = plt.figure(figsize=(13, 7.5), dpi=180, facecolor='white')
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 13); ax.set_ylim(0, 7.5); ax.axis('off')
    ink, blue, gray = '#172B46', '#2864B0', '#667180'
    ax.text(.6, 6.85, 'One offline first cycle: reviewed preparation', fontsize=24,
            weight='bold', color=ink)
    ax.text(.6, 6.3, 'Program built · protocol source reviewed · profiles and execution remain closed',
            fontsize=13.5, color=gray)
    boxes = [
        (.6, 'Current checkpoint', 'Actual compiled program\nOriginal source / SDK bindings\nV2 pre-entry refusal checks', 'Build complete; preparation reviewed'),
        (4.7, 'Before execution', 'Install immutable profiles\nVerify actual files and rosters\nAuthor separate trusted reviews', 'Prospective; not yet released'),
        (8.8, 'Future diagnostic', 'Actual observation + forecast\nFull 0.8s horizon and one QP\nData-only first 4ms preview', 'No step, command commit or task run')]
    for x, title, text, status in boxes:
        ax.add_patch(FancyBboxPatch((x, 3.1), 3.5, 2.4, boxstyle='round,pad=0.025,rounding_size=.06',
                                    facecolor='white', edgecolor=blue, linewidth=1.5))
        ax.text(x+.18, 5.04, title, fontsize=16, weight='bold', color=blue)
        ax.text(x+.18, 4.5, text, fontsize=12.2, linespacing=1.8, va='top', color=ink)
        ax.text(x+.18, 3.34, status, fontsize=9.6, color=gray)
    for left, right in [(4.12, 4.66), (8.22, 8.76)]:
        ax.add_patch(FancyArrowPatch((left, 4.3), (right, 4.3), arrowstyle='-|>',
                                     mutation_scale=16, color=gray, linewidth=1.5))
    ax.text(.6, 2.4, 'V2 refuses before launch if the original total wall budget or output threshold is exhausted.',
            fontsize=12, color=ink)
    ax.text(.6, 1.91, 'The sealed V1 proposal and all preparation errors remain in the evidence archive.',
            fontsize=12, color=gray)
    ax.text(.6, 1.42, 'Future outputs require independent content review; process exit zero is not phase acceptance.',
            fontsize=12, color=gray)
    ax.text(.6, .84, 'Phase 5 NOT_ACCEPTED · Phase 6 NOT_STARTED', fontsize=14, weight='bold', color=ink)
    ax.text(.6, .42, 'Source / protocol diagram. No robot trajectory, tracking, safety or online 4ms result is shown.',
            fontsize=11, color=gray)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    names = ['first_cycle_runtime_preparation.png', 'first_cycle_runtime_preparation.svg']
    for name in names:
        fig.savefig(args.output_dir/name, dpi=180, facecolor='white',
                    metadata={'Date': None} if name.endswith('.svg') else None)
    plt.close(fig)
    provenance = {'scope': 'Reviewed source and prospective runtime gates; no target execution',
                  'review_sha256': sha(args.review),
                  'selection': 'Existing build checkpoint, remaining release prerequisites and single proposed diagnostic',
                  'renderer': {'script': Path(__file__).name, 'sha256': sha(Path(__file__)),
                               'matplotlib': matplotlib.__version__, 'font': 'DejaVu Sans',
                               'dpi': 180, 'figure_inches': [13, 7.5]},
                  'outputs': [{'file': name, 'bytes': (args.output_dir/name).stat().st_size,
                               'sha256': sha(args.output_dir/name)} for name in names],
                  'phase5': 'NOT_ACCEPTED', 'phase6': 'NOT_STARTED'}
    (args.output_dir/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    print(json.dumps(provenance['outputs']))


if __name__ == '__main__':
    main()

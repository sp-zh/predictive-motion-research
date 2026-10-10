"""Show actual file staging and remaining execution gates; no simulated motion."""
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
    assert review['decision'] == 'PASS_ONE_ACTUAL_PROFILE_STAGE_ONLY_RUNTIME_CLOSED'
    assert review['new_project_CPP_calls'] == 0
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none',
                         'svg.hashsalt': 'first-cycle-actual-profile-stage-v1'})
    fig = plt.figure(figsize=(13, 7.5), dpi=180, facecolor='white')
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 13); ax.set_ylim(0, 7.5); ax.axis('off')
    ink, blue, gray = '#172B46', '#2864B0', '#667180'
    ax.text(.6, 6.85, 'First-cycle profiles installed; execution pending', fontsize=24,
            weight='bold', color=ink)
    ax.text(.6, 6.3, '21 exact files installed once · readonly snapshot verified · program not run',
            fontsize=13.5, color=gray)
    boxes = [
        (.6, 'Exact installation', '21 sealed profile files\nThree source-contract copies\nOriginal profile values preserved', 'Fresh snapshot; no old files overwritten'),
        (4.7, 'Actual verification', 'Hashes and paths matched\nReadonly modes and rosters\nOriginal input identities unchanged', 'Root independently rechecked the files'),
        (8.8, 'Remaining release', 'Fresh trusted model review\nOuter review and exact plan\nSeparate first-cycle dispatch', 'Runtime proposals remain NOT_RELEASED')]
    for x, title, text, status in boxes:
        ax.add_patch(FancyBboxPatch((x, 3.1), 3.5, 2.4, boxstyle='round,pad=0.025,rounding_size=.06',
                                    facecolor='white', edgecolor=blue, linewidth=1.5))
        ax.text(x+.18, 5.04, title, fontsize=16, weight='bold', color=blue)
        ax.text(x+.18, 4.5, text, fontsize=12.2, linespacing=1.8, va='top', color=ink)
        ax.text(x+.18, 3.34, status, fontsize=9.6, color=gray)
    for left, right in [(4.12, 4.66), (8.22, 8.76)]:
        ax.add_patch(FancyArrowPatch((left, 4.3), (right, 4.3), arrowstyle='-|>',
                                     mutation_scale=16, color=gray, linewidth=1.5))
    ax.text(.6, 2.4, 'The original compiled program, model inputs, state and solver options remain unchanged.',
            fontsize=12, color=ink)
    ax.text(.6, 1.91, 'No constructor, metadata, forecast, algebra, solver, plant step or task run occurred.',
            fontsize=12, color=gray)
    ax.text(.6, 1.42, 'Actual native observations and outcomes require the separately reviewed runtime scope.',
            fontsize=12, color=gray)
    ax.text(.6, .84, 'Phase 5 NOT_ACCEPTED · Phase 6 NOT_STARTED', fontsize=14, weight='bold', color=ink)
    ax.text(.6, .42, 'Source / protocol diagram. No robot trajectory, tracking, safety or online 4ms result is shown.',
            fontsize=11, color=gray)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    names = ['first_cycle_actual_profile_stage.png', 'first_cycle_actual_profile_stage.svg']
    for name in names:
        fig.savefig(args.output_dir/name, dpi=180, facecolor='white',
                    metadata={'Date': None} if name.endswith('.svg') else None)
    plt.close(fig)
    provenance = {'scope': 'Actual file staging and remaining release prerequisites; no target execution',
                  'review_sha256': sha(args.review),
                  'selection': 'Exact installation, actual file verification and remaining execution gates',
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

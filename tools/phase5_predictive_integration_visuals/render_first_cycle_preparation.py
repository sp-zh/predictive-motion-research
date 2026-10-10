"""Source-backed first-cycle entry diagram; does not execute the controller."""
import argparse, hashlib, json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    for n in ['review', 'repo', 'output-dir']:
        ap.add_argument('--'+n, required=True, type=Path)
    a = ap.parse_args(); review = json.loads(a.review.read_text())
    assert review['decision'] == 'PASS_FIRST_CYCLE_SOURCE_AND_PREPARATION_ONLY_STAGING_BUILD_RUNTIME_CLOSED'
    for row in review['imported_source_identities']:
        p = a.repo/row['path']; assert p.stat().st_size == row['bytes'] and sha(p) == row['sha256']
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none', 'svg.hashsalt': 'first-cycle-source-preparation-v1'})
    fig = plt.figure(figsize=(13, 7.5), dpi=180, facecolor='white')
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 13); ax.set_ylim(0, 7.5); ax.axis('off')
    ink, blue, gray = '#172B46', '#2864B0', '#667180'
    ax.text(.6, 6.8, 'First-cycle entry and build preparation', fontsize=26, weight='bold', color=ink)
    ax.text(.6, 6.3, 'Source reviewed · new program has not been built or run', fontsize=15, color=gray)
    rows = [
        (.6, 'Actual source', 'New native home bootstrap\nRead q / v / actuator control\nInitialized history policy'),
        (4.7, 'Predictive chain', 'Full 0.8s nominal horizon\nSave original raw output\nInline QP + data-only preview'),
        (8.8, 'Boundary and evidence', 'After scratch observation\nBefore / after state comparison\nLossless outputs and failures')]
    for x, title, text in rows:
        ax.add_patch(FancyBboxPatch((x, 3.1), 3.5, 2.4, boxstyle='round,pad=0.025,rounding_size=.06', facecolor='white', edgecolor=blue, linewidth=1.5))
        ax.text(x+.2, 5.06, title, fontsize=16, weight='bold', color=blue)
        ax.text(x+.2, 4.5, text, fontsize=12.6, linespacing=1.8, va='top', color=ink)
        ax.text(x+.2, 3.35, 'Implemented source · runtime closed', fontsize=10.5, color=gray)
    for left, right in [(4.12, 4.66), (8.22, 8.76)]:
        ax.add_patch(FancyArrowPatch((left, 4.3), (right, 4.3), arrowstyle='-|>', mutation_scale=16, color=gray, linewidth=1.5))
    ax.text(.6, 2.45, 'Planned build: 7 compiler entries + 1 link · 10 existing static libraries reused', fontsize=14, color=ink)
    ax.text(.6, 1.99, '125 existing files checked; 15 source copies and their new tree remain prospective.', fontsize=12.5, color=gray)
    ax.text(.6, 1.52, 'First error stops the batch. Constructor, model, solver and motion permission remain separate.', fontsize=12, color=gray)
    ax.text(.6, .85, 'Phase 5 NOT_ACCEPTED · Phase 6 NOT_STARTED', fontsize=14, weight='bold', color=ink)
    ax.text(.6, .42, 'Architecture / preparation only. No trajectory, performance or safety result is shown.', fontsize=11, color=gray)
    a.output_dir.mkdir(parents=True, exist_ok=False)
    names = ['first_cycle_source_preparation.png', 'first_cycle_source_preparation.svg']
    for n in names:
        fig.savefig(a.output_dir/n, dpi=180, facecolor='white', metadata={'Date': None} if n.endswith('.svg') else None)
    plt.close(fig)
    prov = {'scope': 'Source/preparation diagram, no target runtime evidence', 'review_sha256': sha(a.review),
            'source_records': review['imported_source_identities'], 'selection': 'All three standalone pipeline blocks and exact declared build stages',
            'counts_scope': 'Build/source shapes and file identities, not executed compiler/Model calls',
            'renderer': {'script': Path(__file__).name, 'sha256': sha(Path(__file__)), 'matplotlib': matplotlib.__version__, 'font': 'DejaVu Sans', 'dpi': 180, 'figure_inches': [13, 7.5]},
            'outputs': [{'file': n, 'bytes': (a.output_dir/n).stat().st_size, 'sha256': sha(a.output_dir/n)} for n in names],
            'phase5': 'NOT_ACCEPTED', 'phase6': 'NOT_STARTED'}
    (a.output_dir/'provenance.json').write_text(json.dumps(prov, indent=2)+'\n'); print(json.dumps(prov['outputs']))

if __name__ == '__main__':
    main()

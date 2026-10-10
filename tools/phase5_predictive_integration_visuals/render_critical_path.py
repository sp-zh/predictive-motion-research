"""Render source-backed integration dependencies; this is not execution evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--findings', required=True, type=Path)
    ap.add_argument('--repo', required=True, type=Path)
    ap.add_argument('--integration-review', required=True, type=Path)
    ap.add_argument('--output-dir', required=True, type=Path)
    a = ap.parse_args()
    findings = json.loads(a.findings.read_text())
    reviewed = json.loads(a.integration_review.read_text())
    assert reviewed['decision'] == 'PASS_VERSIONED_INTEGRATION_SOURCE_ONLY_BUILD_AND_RUNTIME_CLOSED'
    for row in reviewed['imported_source_identities']:
        p = a.repo/row['path']
        assert p.stat().st_size == row['bytes'] and digest(p) == row['sha256']
    for x in findings['source_records']:
        p = a.repo/x['path']
        assert p.stat().st_size == x['bytes'] and digest(p) == x['sha256']
    assert [x['id'] for x in findings['findings']] == ['CP1', 'CP2', 'CP3', 'CP4', 'CP5']
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none', 'svg.hashsalt': 'coupled-integration-critical-path-v1'})
    fig = plt.figure(figsize=(14, 7.5), dpi=180, facecolor='white')
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 14); ax.set_ylim(0, 7.5); ax.axis('off')
    blue, ink, neutral = '#2864B0', '#172B46', '#667180'
    ax.text(.6, 6.72, 'Coupled predictive control: integration boundary', fontsize=25, weight='bold', color=ink)
    ax.text(.6, 6.2, 'Source dependency map · functional 3-second diagnostic has not run', fontsize=15, color=neutral)
    boxes = [
        ('Coupled model', '30-state q / v / C / w / s / r\n8-input alpha / b', 'Existing component evidence', blue),
        ('Affine maps', 'Typed live affine maps\nFrozen cost kept separately', 'Existing source and build', blue),
        ('QP connection', 'Inline task objective\nConstraint rows + SI gate', 'New source; build / run pending', ink),
        ('Candidate validation', 'Own nonlinear forecast\nFirst 4ms command check', 'Additional reviewed run scope', neutral),
        ('Plant + control loop', 'Fresh measured state\n750 commits at 4ms', 'Separate main / plant gate', neutral)]
    starts = [.6, 3.2, 5.8, 8.4, 11.0]
    for x, (title, body, status, edge) in zip(starts, boxes):
        ax.add_patch(FancyBboxPatch((x, 3.2), 2.35, 2.15, boxstyle='round,pad=0.03,rounding_size=0.06',
                                   facecolor='white', edgecolor=edge, linewidth=1.5))
        ax.text(x+.13, 4.95, title, fontsize=12.7, weight='bold', color=edge)
        ax.text(x+.13, 4.4, body, fontsize=10.8, linespacing=1.7, va='top', color=ink)
        ax.text(x+.13, 3.5, status, fontsize=9.0, color=edge)
    for left, right in zip(starts, starts[1:]):
        ax.add_patch(FancyArrowPatch((left+2.38, 4.2), (right-.05, 4.2), arrowstyle='-|>', mutation_scale=12,
                                    color=neutral, linewidth=1.2))
    ax.text(.6, 2.48, 'The 16-state legacy preview cannot supply the new command acceleration alpha.', fontsize=13.2, color=ink)
    ax.text(.6, 1.98, 'Accepted command: w_next = w + h alpha; C_next = C + h w_next. Physical q / v remain independent.', fontsize=12.2, color=neutral)
    ax.text(.6, 1.52, 'Existing Model release permits one forecast. Candidate checks and repeated sessions need explicit scope.', fontsize=12.2, color=neutral)
    ax.text(.6, .83, 'Phase 5 NOT_ACCEPTED · Phase 6 NOT_STARTED', fontsize=14, weight='bold', color=ink)
    ax.text(.6, .4, 'No forecast, solver, plant, trajectory, timing or safety result is implied by this map.', fontsize=11, color=neutral)
    a.output_dir.mkdir(parents=True, exist_ok=False)
    names = ['coupled_predictive_critical_path.png', 'coupled_predictive_critical_path.svg']
    for n in names:
        fig.savefig(a.output_dir/n, dpi=180, facecolor='white', metadata={'Date': None} if n.endswith('.svg') else None)
    plt.close(fig)
    p = {'scope': 'Source-backed dependency diagram, not numeric experiment or task acceptance',
         'baseline': findings['baseline'], 'source_findings_sha256': digest(a.findings), 'source_records': findings['source_records'],
         'integration_review_sha256': digest(a.integration_review),
         'new_integration_source_records': reviewed['imported_source_identities'],
         'selection': 'All five independent critical-path findings; phases remain unaccepted',
         'renderer': {'script': Path(__file__).name, 'sha256': digest(Path(__file__)), 'matplotlib': matplotlib.__version__,
                      'font': 'DejaVu Sans', 'dpi': 180, 'figure_inches': [14, 7.5]},
         'outputs': [{'file': n, 'bytes': (a.output_dir/n).stat().st_size, 'sha256': digest(a.output_dir/n)} for n in names],
         'phase5': 'NOT_ACCEPTED', 'phase6': 'NOT_STARTED'}
    (a.output_dir/'provenance.json').write_text(json.dumps(p, indent=2)+'\n')
    print(json.dumps(p['outputs']))

if __name__ == '__main__':
    main()

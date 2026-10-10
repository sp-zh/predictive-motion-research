"""Render reviewed file identity/static range contracts; never run project tests."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    for name in ['review', 'stdout', 'roster', 'results', 'output-dir']:
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_text())
    assert review['decision'] == 'PASS_FIXED24_IDENTITY_STATIC_RANGES_RUNTIME_ONLY_NOT_PHASE_ACCEPTANCE'
    roster = json.loads(args.roster.read_text())['groups']
    ids = [r['id'] for r in roster]
    expected = (''.join('PASS '+i+'\n' for i in ids)+
                'COMPLETE 24 identity/range groups; identity entries 14; range entries 15; total 29; no phase acceptance\n').encode()
    assert len(ids) == len(set(ids)) == 24 and args.stdout.read_bytes() == expected
    assert digest(args.stdout) == review['actual_stdout_sha256']
    groups = json.loads(args.results.read_text())['groups']
    assert [g['case_group_id'] for g in groups] == ids
    for g, r in zip(groups, roster):
        assert g['observed_status'] == 'PASS' and g['target_API'] == r['target_api']
        assert g['controlled_target_entries'] == r['target_entries'] and g['source_declared_expected'] == r['expected']
    rows = []
    for api, label in [('observePinnedFile', 'File identity'), ('loadPinnedStaticRanges', 'Static ranges')]:
        chosen = [r for r in roster if r['target_api'] == api]
        accepted = sum(r['target_entries'] for r in chosen if r['expected'].startswith('ACCEPT'))
        entries = sum(r['target_entries'] for r in chosen)
        rows.append({'area': label, 'API': api, 'case_group_ids': [r['id'] for r in chosen],
                     'passed_groups': len(chosen), 'planned_groups': len(chosen),
                     'controlled_entries': entries, 'accepted_entries': accepted,
                     'required_refusal_entries': entries-accepted})
    assert [r['passed_groups'] for r in rows] == [9, 15]
    assert [r['controlled_entries'] for r in rows] == [14, 15]
    assert sum(r['accepted_entries'] for r in rows) == 4
    assert sum(r['required_refusal_entries'] for r in rows) == 25
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 14,
                         'svg.fonttype': 'none', 'axes.unicode_minus': False,
                         'svg.hashsalt': 'phase5-identity-ranges-bounded24-v1'})
    fig = plt.figure(figsize=(13, 7), dpi=180, facecolor='white')
    axes = [fig.add_axes([.22, .37, .28, .29]), fig.add_axes([.64, .37, .30, .29])]
    blue, gray = '#2864B0', '#667180'
    for index, ax in enumerate(axes):
        if index == 0:
            ax.barh(range(2), [r['passed_groups'] for r in rows], height=.42, color=blue, zorder=3)
        else:
            accepted = [r['accepted_entries'] for r in rows]
            ax.barh(range(2), accepted, height=.42, color=blue, label='Accepted input', zorder=3)
            ax.barh(range(2), [r['required_refusal_entries'] for r in rows], left=accepted,
                    height=.42, color=gray, hatch='///', label='Required refusal', zorder=3)
            for i, r in enumerate(rows):
                ax.text(r['accepted_entries']/2, i, str(r['accepted_entries']), va='center', ha='center', color='white', fontweight='bold')
                ax.text(r['accepted_entries']+r['required_refusal_entries']/2, i,
                        str(r['required_refusal_entries']), va='center', ha='center', color='white', fontweight='bold')
        ax.set_yticks(range(2), [r['area'] for r in rows] if index == 0 else ['']*2)
        ax.invert_yaxis(); ax.set_ylim(1.65, -.65)
        ax.set_xlim(0, 18); ax.set_xticks([0, 3, 6, 9, 12, 15, 18]); ax.set_xlabel('Count', labelpad=10)
        ax.set_title('Groups passing checks' if index == 0 else 'Controlled API entries', fontweight='bold', pad=16)
        ax.grid(axis='x', color='#E3E7EC', linewidth=.8, zorder=0)
        ax.tick_params(axis='y', length=0, pad=12)
        for name in ['top', 'right']: ax.spines[name].set_visible(False)
        for name in ['left', 'bottom']: ax.spines[name].set_color('#68717E')
        for i, r in enumerate(rows):
            value = r['passed_groups'] if index == 0 else r['controlled_entries']
            label = f"{value} / {r['planned_groups']}" if index == 0 else str(value)
            ax.text(value+.4, i, label, va='center', fontweight='bold', color='#233247')
    axes[1].legend(loc='upper center', bbox_to_anchor=(.5, -.35), ncol=2, frameon=False, fontsize=11)
    fig.text(.06, .905, 'File identity and static range verification', fontsize=26, fontweight='bold', color='#172B46')
    fig.text(.06, .855, '24 groups passed · 29 controlled API entries · one invocation', fontsize=16, color='#4E5661')
    fig.text(.06, .795, '4 accepted inputs and 25 required refusals; exact pre-run stdout matched.', fontsize=13, color='#4E5661')
    fig.text(.06, .16, 'Development verification only · Phase 5 NOT_ACCEPTED', fontsize=14, fontweight='bold', color='#172B46')
    fig.text(.06, .115, 'All fixed groups included. Entries are not IO / getter / native calls or independent experiments.', fontsize=12, color='#4E5661')
    fig.text(.06, .078, 'Synthetic fixtures; no physical admission, robot motion, controller performance or RSS evidence.', fontsize=12, color='#4E5661')
    fig.text(.06, .036, f"Binary SHA-256: {review['binary_sha256'][:16]}…   Stdout SHA-256: {digest(args.stdout)[:16]}…", fontsize=10, color='#68717E')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    names = ['identity_static_ranges_bounded24_outcomes.png', 'identity_static_ranges_bounded24_outcomes.svg']
    for name in names:
        fig.savefig(args.output_dir/name, dpi=180, facecolor='white', metadata={'Date': None} if name.endswith('.svg') else None)
    plt.close(fig)
    prov = {'scope': 'Actual finite identity/static range interface checks; no phase acceptance',
            'grains': {'left': 'One fixed group', 'right': 'Entry at a compiled observe/load wrapper'},
            'selection': 'All24 original groups and29 entries; no curated subset', 'rows': rows,
            'source_reason_scope': 'Expected reasons checked by frozen source; exceptions not separately printed telemetry',
            'required_refusal_types': {'invalid_argument': 24, 'runtime_error_open_prefix': 1},
            'sources': {key: {'file': path.name, 'sha256': digest(path)} for key, path in
                        [('review', args.review), ('actual_stdout', args.stdout), ('original_roster', args.roster), ('group_results', args.results)]},
            'renderer': {'script': Path(__file__).name, 'sha256': digest(Path(__file__)), 'matplotlib': matplotlib.__version__,
                         'dpi': 180, 'figure_inches': [13, 7], 'font': 'DejaVu Sans', 'colors': [blue, gray], 'refusal_hatch': '///'},
            'outputs': [{'file': n, 'bytes': (args.output_dir/n).stat().st_size, 'sha256': digest(args.output_dir/n)} for n in names],
            'phase5': 'NOT_ACCEPTED', 'phase6': 'NOT_STARTED'}
    (args.output_dir/'provenance.json').write_text(json.dumps(prov, indent=2)+'\n')
    print(json.dumps({'rows': rows, 'outputs': prov['outputs']}))

if __name__ == '__main__':
    main()

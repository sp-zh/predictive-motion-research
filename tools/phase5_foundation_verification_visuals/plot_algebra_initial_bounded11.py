"""Render reviewed initial-state contract results without running project tests."""
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
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_text())
    if review['decision'] != 'PASS_FIXED11_SYNTHETIC_INITIAL_RUNTIME_ONLY_NOT_PHASE_ACCEPTANCE':
        raise ValueError('Requires independent review of the finite run')
    roster = json.loads(args.roster.read_text())
    ids = [row['id'] for row in roster['groups']]
    expected = (''.join(f'PASS {case}\n' for case in ids) +
                'COMPLETE 11 algebra initial groups; target entries 97; no phase acceptance\n').encode('ascii')
    if len(ids) != 11 or len(set(ids)) != 11 or args.stdout.read_bytes() != expected:
        raise ValueError('Actual output must match all original ordered groups')
    if digest(args.stdout) != review['actual_stdout_sha256']:
        raise ValueError('Actual output identity differs from independent review')
    results = json.loads(args.results.read_text())['groups']
    if [row['case_group_id'] for row in results] != ids or any(row['observed_status'] != 'PASS' for row in results):
        raise ValueError('Observed results must match all fixed groups')
    for actual, original in zip(results, roster['groups']):
        if (actual['source_declared_subcases'] != original['subcases'] or
                actual['controlled_target_entries'] != original['expected_target_entries']):
            raise ValueError('Controlled entries must match the pre-run source roster')
    definitions = [('Finite copy', ids[:5]), ('Joint NaN / Inf', ids[5:9]),
                   ('Progress NaN / Inf', ids[9:10]), ('Category priority', ids[10:])]
    rows = []
    for label, group_ids in definitions:
        rows.append({'area': label, 'case_group_ids': group_ids,
                     'passed_groups': len(group_ids), 'planned_groups': len(group_ids),
                     'controlled_validator_entries': sum(row['controlled_target_entries']
                                                        for row in results if row['case_group_id'] in group_ids)})
    if [row['passed_groups'] for row in rows] != [5, 4, 1, 1] or [row['controlled_validator_entries'] for row in rows] != [5, 84, 6, 2]:
        raise ValueError('The two counts must partition eleven groups and 97 entries')

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 14,
                         'svg.fonttype': 'none', 'axes.unicode_minus': False,
                         'svg.hashsalt': 'phase5-initial-bounded11-v1'})
    fig = plt.figure(figsize=(13, 7), dpi=180, facecolor='white')
    axes = [fig.add_axes([.26, .32, .28, .37]), fig.add_axes([.66, .32, .28, .37])]
    color = '#2864B0'
    for index, (ax, key, limit, ticks, title) in enumerate([
        (axes[0], 'passed_groups', 6, range(7), 'Groups passing checks'),
        (axes[1], 'controlled_validator_entries', 100, range(0, 101, 20), 'Controlled validator entries')
    ]):
        values = [row[key] for row in rows]
        ax.barh(range(4), values, height=.54, color=color, zorder=3)
        ax.set_yticks(range(4), [row['area'] for row in rows] if index == 0 else [''] * 4)
        ax.invert_yaxis()
        ax.set_xlim(0, limit)
        ax.set_xticks(list(ticks))
        ax.set_xlabel('Count', labelpad=10)
        ax.set_title(title, fontsize=14, pad=16, fontweight='bold')
        ax.grid(axis='x', color='#E3E7EC', linewidth=.8, zorder=0)
        ax.tick_params(axis='y', length=0, pad=12)
        ax.tick_params(axis='x', colors='#4E5661', length=4)
        for name in ['top', 'right']:
            ax.spines[name].set_visible(False)
        for name in ['left', 'bottom']:
            ax.spines[name].set_color('#68717E')
            ax.spines[name].set_linewidth(.8)
        for i, value in enumerate(values):
            label = f"{value} / {rows[i]['planned_groups']}" if index == 0 else str(value)
            ax.text(value + limit * .022, i, label, va='center', ha='left',
                    fontsize=14, color='#233247', fontweight='bold')
    fig.text(.06, .905, 'Initial-state contract verification', fontsize=27,
             fontweight='bold', color='#172B46')
    fig.text(.06, .855, '11 groups passed · 97 controlled validator entries · one invocation',
             fontsize=16, color='#4E5661')
    fig.text(.06, .795, 'Exact pre-run stdout matched; required nonfinite refusals matched their category messages.',
             fontsize=13, color='#4E5661')
    fig.text(.06, .16, 'Development verification only · Phase 5 NOT_ACCEPTED', fontsize=14,
             fontweight='bold', color='#172B46')
    fig.text(.06, .115, 'Synthetic coordinates. Entry counts are not independent experiments or all C++ / native calls.',
             fontsize=12, color='#4E5661')
    fig.text(.06, .078, 'Physical admission, live context, robot motion, controller performance and RSS remain outside scope.',
             fontsize=12, color='#4E5661')
    fig.text(.06, .036, f"Binary SHA-256: {review['binary_sha256'][:16]}…   Stdout SHA-256: {digest(args.stdout)[:16]}…",
             fontsize=10, color='#68717E')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    names = ['algebra_initial_bounded11_outcomes.png', 'algebra_initial_bounded11_outcomes.svg']
    for name in names:
        fig.savefig(args.output_dir/name, dpi=180, facecolor='white',
                    metadata={'Date': None} if name.endswith('.svg') else None)
    plt.close(fig)
    provenance = {
        'scope': 'Finite synthetic initial-state verification; no phase acceptance',
        'grains': {'left': 'One fixed case group', 'right': 'One entry at the compiled validator callsite'},
        'selection': 'All eleven original groups and 97 declared entries; no curated subset',
        'counter_scope': 'Five accepted entries and 92 required invalid_argument entries; not all C++/native/getter counts or independent experiments',
        'rows': rows,
        'sources': {key: {'file': path.name, 'sha256': digest(path)} for key, path in
                    [('review', args.review), ('actual_stdout', args.stdout),
                     ('original_roster', args.roster), ('group_results', args.results)]},
        'renderer': {'script': Path(__file__).name, 'sha256': digest(Path(__file__)),
                     'matplotlib': matplotlib.__version__, 'dpi': 180, 'figure_inches': [13, 7],
                     'font': 'DejaVu Sans', 'bar_color': color},
        'outputs': [{'file': name, 'bytes': (args.output_dir/name).stat().st_size,
                     'sha256': digest(args.output_dir/name)} for name in names],
        'phase5': 'NOT_ACCEPTED', 'phase6': 'NOT_STARTED'
    }
    (args.output_dir/'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps({'rows': rows, 'outputs': provenance['outputs']}))


if __name__ == '__main__':
    main()

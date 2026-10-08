#!/usr/bin/env python3
"""Render already validated affine algebra data; no kernel/model/plant calls."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    ready = json.loads((args.results/'READY.json').read_text())
    for name, entry in ready['files'].items():
        f = args.results/name
        assert sha(f) == entry['sha256'] and f.stat().st_size == entry['bytes']
    report = json.loads((args.results/'audit.json').read_text())
    assert report['decision'] == 'PASS_PREDECLARED_AFFINE_KERNEL_CLI_ALGEBRA'
    assert report['kernel_calls'] == 1 and report['original_model_calls'] == 0
    packet = json.loads((args.results/'kernel_once.json').read_text())
    cases = packet['cases']; positive = [c for c in cases if c['success']]
    controls = report['mutation_controls']
    assert len(positive) == 4 and len(cases) == 12
    assert len(controls) == 23 and all(c['rejected'] for c in controls)
    args.output.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11,
                         'axes.spines.top':False, 'axes.spines.right':False,
                         'figure.facecolor':'#f8fafc', 'axes.facecolor':'#f8fafc',
                         'savefig.facecolor':'#f8fafc'})
    footer = ('Cached affine-coefficient algebra only. No executed motion, accuracy, '
              'safety or Phase 5 acceptance.')
    assets = []

    def save(fig, stem, caption):
        fig.text(.06, .035, footer, fontsize=9, color='#475569')
        for suffix in ('png','svg'):
            path = args.output/(stem+'.'+suffix)
            fig.savefig(path, dpi=180, bbox_inches='tight')
            assets.append(dict(file=path.name, sha256=sha(path),
                               bytes=path.stat().st_size, caption=caption))
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10,4.5))
    counts = [4,8,23]
    labels = ['Algebra positive cases\nvalidated', 'Expected source/shape\nrefusals preserved',
              'Altered output packets\nrejected']
    bars = ax.barh(labels[::-1], counts[::-1], color=['#8057b2','#c0832f','#187f82'])
    for bar, count in zip(bars, counts[::-1]):
        ax.text(count+.35, bar.get_y()+bar.get_height()/2, str(count), va='center', weight='bold')
    ax.set_xlim(0,26); ax.set_xlabel('Count (different check categories; not a method ranking)')
    ax.set_title('Independent first-attempt affine verification', loc='left', weight='bold', pad=15)
    ax.grid(axis='x', alpha=.18); ax.set_axisbelow(True)
    fig.tight_layout(rect=(.02,.10,.98,.97))
    save(fig, 'public_affine_horizon_root_outcomes', 'Root12-case first attempt and23 output-mutation controls.')

    n4 = next(c for c in positive if c['name']=='root_affine_public_nonuniform_shifted')
    a = n4['assembly']; assert a['cycles'] == [1,3,2,4]
    assert len(a['samples']) == 20
    # r is progress speed; b is progress acceleration, so dr/db has units s.
    sensitivity = np.array([a['recursive_states'][0]['control'][29]] +
                           [s['recursive']['control'][29] for s in a['samples']])
    bcols = sensitivity[:, [7,15,23,31]]
    time_ms = np.arange(21)*2.
    boundary_ms = np.r_[0, np.cumsum(a['cycles'])*4.]
    fig, ax = plt.subplots(figsize=(10,4.8))
    colors = ['#187f82','#8057b2','#c0832f','#b64f65']
    for c in range(4):
        ax.plot(time_ms,bcols[:,c],marker='o',markersize=3,color=colors[c],
                label=f'Cell {c}: {a["cycles"][c]*4} ms')
        ax.axvspan(boundary_ms[c],boundary_ms[c+1],alpha=.045,color=colors[c])
    ax.set_xlabel('Elapsed affine mesh (ms)'); ax.set_ylabel('Progress-speed sensitivity dr/db (s)')
    ax.set_title('Distinct inputs over the nonuniform N=4 mesh', loc='left', weight='bold', pad=15)
    ax.legend(frameon=False, ncol=2); ax.grid(alpha=.18)
    fig.tight_layout(rect=(.02,.10,.98,.97))
    save(fig, 'public_affine_horizon_distinct_progress_inputs',
         'Serialized cumulative sample sensitivities; final own-cell b columns .004/.012/.008/.016s.')

    metrics = []
    for case in positive:
        e = case['evaluation']; pairs = e['terms']+[e['sum']]
        row = []
        for left,right in [('lifted_value','condensed_value'),
                           ('lifted_chain_gradient','condensed_gradient'),
                           ('lifted_chain_hessian','condensed_hessian')]:
            row.append(max(float(np.max(np.abs(np.asarray(v[left])-np.asarray(v[right])) /
                       (report['output_abs']+report['output_rel']*np.abs(np.asarray(v[left])))))
                       for v in pairs))
        metrics.append(row)
    metrics = np.array(metrics)
    fig, axes = plt.subplots(1,3,figsize=(12,4.6),sharey=True)
    labels = ['Startup N=1','Shifted N=4','Generic N=3','Zero terms']
    for j, ax in enumerate(axes):
        ax.barh(labels[::-1],metrics[::-1,j],color=colors[j])
        ax.set_title(['Value','Gradient','Hessian'][j],weight='bold')
        ax.set_xscale('symlog',linthresh=1e-8); ax.set_xlim(0,1.)
        ax.set_xticks([0.,1e-8,1e-5,1e-2,1.])
        ax.set_xticklabels(['0',r'$10^{-8}$',r'$10^{-5}$',r'$10^{-2}$','1'])
        ax.axvline(1.,color='#64748b',ls='--',lw=1)
        for i,value in enumerate(metrics[::-1,j]):
            ax.annotate('0' if value == 0 else f'{value:.1e}',(value,i),xytext=(4,0),
                        textcoords='offset points',va='center',fontsize=9)
        ax.grid(axis='x',alpha=.18); ax.set_axisbelow(True)
        ax.set_xlabel('Max normalized difference')
    fig.suptitle('Full versus condensed objective evaluations',x=.065,ha='left',weight='bold')
    fig.text(.065,.09,'Ratio = |full - condensed| / (1e-11 + 1e-10 |full|); declared algebra units.',fontsize=9)
    fig.tight_layout(rect=(.02,.15,.98,.93))
    save(fig, 'public_affine_horizon_objective_agreement',
         'Differences between serialized full and condensed evaluations, independently audited against the root reference.')
    provenance = dict(scope=__doc__,kernel_output_sha256=sha(args.results/'kernel_once.json'),
                      audit_report_sha256=sha(args.results/'audit.json'),
                      renderer_sha256=sha(Path(__file__)),assets=assets,
                      own_cell_b_sensitivity_s=bcols[-1].tolist(),
                      normalized_objective_difference=metrics.tolist(),
                      kernel_calls_in_rendering=0,original_model_calls=0,phase5='NOT_ACCEPTED')
    (args.output/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')


if __name__ == '__main__':
    main()

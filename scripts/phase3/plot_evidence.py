import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import yaml
root=Path(__file__).resolve().parents[2];folder=root/'results/phase3/evaluation';selection=yaml.safe_load((root/'results/phase3/selection.yaml').read_text())
for kind,seed in [('joint_limit',51012),('singularity',51011)]:
    fig,axes=plt.subplots(2,3,figsize=(13,8),sharex=True,constrained_layout=True)
    for method,color in [('none','#555555'),('joint','#246aa5'),('sigma_min','#e18a24'),('log_volume','#23845b'),('combined','#c33932')]:
        gain=0 if method=='none' else selection[method]
        rows=list(csv.DictReader((folder/f'{kind}_hold_{seed}_{method}_{gain:.6f}.csv').open()))
        def field(key):return np.array([float(row[key]) for row in rows])
        time=field('time_before');label=method.replace('_',' ')
        axes[0,0].plot(time,field('H_joint'),color=color,label=label)
        axes[0,1].plot(time,field('min_normalized_margin'),color=color,label=label)
        axes[0,2].semilogy(time,np.maximum(field('scaled_sigma_min'),1e-14),color=color,label=label)
        axes[1,0].plot(field('time_after'),field('position_error')*1000,color=color,label=label)
        axes[1,1].semilogy(time,np.maximum(field('raw_unscaled_JPz_leakage'),1e-18),color=color,label=label)
        axes[1,2].semilogy(time,np.maximum(field('guard_unscaled_task_distortion'),1e-18),color=color,label=label)
    labels=['H_joint','Minimum normalized joint margin','Scaled raw-J sigma_min (m/rad)','Post-step TCP position error (mm)','Raw ||J P z|| (mixed units)','Guard ||J(accepted-requested)|| (mixed units)']
    for ax,label in zip(axes.flat,labels):ax.set_ylabel(label);ax.grid(alpha=.2);ax.legend(fontsize=8)
    for ax in axes[1,:]:ax.set_xlabel('Control time after warmup (s)')
    fig.suptitle(f'Phase 3 held-pose component example: {kind}, seed {seed}\nFrozen gains; exact projector; includes unfavorable outcomes; no collision/CAD/research superiority claim')
    fig.savefig(root/f'results/phase3/{kind}-hold-{seed}.png',dpi=150);fig.savefig(root/f'results/phase3/{kind}-hold-{seed}.pdf')
print('PHASE3_RAW_FIGURES_WRITTEN')

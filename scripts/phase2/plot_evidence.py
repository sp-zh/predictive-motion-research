"""Offline scientific figure from actual raw CSV, with no controller execution."""
import csv
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--input',type=Path,default=root/'results/phase2/weak_direction')
parser.add_argument('--output',type=Path,default=root/'results/phase2')
args=parser.parse_args()
folder=args.input
args.output.mkdir(parents=True,exist_ok=True)
vmax=np.array([float(row['velocity']) for row in csv.DictReader((folder/'bounds.csv').open())])
fig,axes=plt.subplots(3,2,figsize=(12,10),sharex=True,constrained_layout=True)
colors={'mp':'#c33932','fixed':'#246aa5','adaptive':'#23845b'}
for method,damping,label in [('mp',0,'MP'),('fixed',.003,'DLS λ=0.003'),('adaptive',.01,'Adaptive DLS λmax=0.01')]:
    rows=list(csv.DictReader((folder/f'weak_direction_3102_{method}_{damping:.6f}.csv').open()))
    time=np.array([float(row['time_after']) for row in rows])
    def field(key):return np.array([float(row[key]) for row in rows])
    def motion(name):return np.array([[float(row[f'{name}_{i}']) for i in range(7)] for row in rows])
    color=colors[method]
    axes[0,0].semilogy(time,field('sigma_min'),color=color,label=label)
    axes[0,1].semilogy(time,np.maximum(np.max(np.abs(motion('requested_dq'))/vmax,axis=1),1e-8),color=color,label=label)
    axes[1,0].plot(time,np.max(np.abs(motion('accepted_dq'))/vmax,axis=1),color=color,label=label)
    axes[1,1].plot(time,np.max(np.abs(motion('executed_dq'))/vmax,axis=1),color=color,label=label)
    axes[2,0].plot(time,field('position_error')*1000,color=color,label=label)
    axes[2,1].plot(time,field('rotation_error'),color=color,label=label)
axes[0,0].set_ylabel('σmin of weighted -de/dq (m/rad)')
axes[0,1].set_ylabel('Raw requested |dq| / joint limit (max)')
axes[1,0].set_ylabel('Accepted |dq| / joint limit (max)')
axes[1,1].set_ylabel('Executed |dq| / joint limit (max)')
axes[2,0].set_ylabel('TCP position error (mm)')
axes[2,1].set_ylabel('TCP geodesic rotation error (rad)')
for ax in [axes[0,1],axes[1,0],axes[1,1]]:ax.axhline(1,color='black',linestyle='--',linewidth=.8)
for ax in axes.flat:ax.grid(alpha=.2);ax.legend(fontsize=8)
for ax in axes[2,:]:ax.set_xlabel('Time after warmup (s)')
fig.suptitle('Supplementary weak-direction diagnostic, seed 3102\nShared 250 Hz plant/guard; frozen damping; not certified feasible or included in held-out aggregates')
fig.savefig(args.output/'weak-direction-3102.png',dpi=160)
fig.savefig(args.output/'weak-direction-3102.pdf')
inputs=['bounds.csv']+[f'weak_direction_3102_{method}_{damping:.6f}.csv' for method,damping in [('mp',0),('fixed',.003),('adaptive',.01)]]
manifest={'scope':'supplementary component diagnostic; corrected post-step observations','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'inputs':{name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in inputs},'matplotlib':matplotlib.__version__,'numpy':np.__version__}
(args.output/'figure_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('RAW_CSV_FIGURES_WRITTEN')

"""Reproduce validation figures from recorded C++ finite-difference samples."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

parser=argparse.ArgumentParser()
parser.add_argument('--input',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
args.output.mkdir(parents=True,exist_ok=True)
def columns(path):
    with path.open() as f:
        rows=list(csv.DictReader(f))
    return {key:np.array([float(row[key]) for row in rows]) for key in rows[0]}

d=columns(args.input/'samples.csv')
if len(d['sample'])<2000:
    raise ValueError('Expected at least 2000 actual samples')
eps=columns(args.input/'epsilon_scan.csv')
fig,(left,right)=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for key,label in [('local_full_abs','TCP LOCAL Jacobian'),('lwa_full_abs','TCP LWA Jacobian'),('residual_abs','SE(3) q derivative'),('desired_body_abs','Desired body derivative'),('rotated_local_abs','Rotated base / tool')]:
    x=np.sort(d[key])
    left.semilogx(np.maximum(x,1e-18),np.arange(1,len(x)+1)/len(x),label=label)
left.set(xlabel='Absolute Frobenius error (mixed SI units)',ylabel='Empirical cumulative fraction',title=f'{len(d["sample"])} configurations, seed 42, h = 1e-6 rad')
left.legend(fontsize=8)
for key,label in [('local_abs','LOCAL Jacobian'),('residual_abs','SE(3) q derivative'),('desired_body_abs','Desired body derivative')]:
    hs=sorted(set(eps['h']))
    right.loglog(hs,[np.max(eps[key][eps['h']==h]) for h in hs],marker='o',label=label)
right.set(xlabel='Central finite-difference h (rad / twist units)',ylabel='Worst absolute Frobenius error',title='Step-size sensitivity, first 50 configurations')
right.legend(fontsize=8)
for ax in [left,right]:ax.grid(alpha=0.25)
fig.savefig(args.output/'kinematics_validation.png',dpi=160)
manifest={'matplotlib':matplotlib.__version__,'numpy':np.__version__,'inputs':{name:hashlib.sha256((args.input/name).read_bytes()).hexdigest() for name in ['samples.csv','epsilon_scan.csv','summary.json']}}
(args.output/'kinematics_figure_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

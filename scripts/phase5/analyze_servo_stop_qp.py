#!/usr/bin/env python3
"""Original-SI interval/geometry checks on actual shared stop QP captured after matched replay."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import yaml
from scipy.optimize import linprog
from servo_model_v1 import sha,write_new
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
d=a.case/'replay-stop';meta=yaml.safe_load((d/'summary.yaml').read_text())
A=np.loadtxt(d/'stop_A.csv',delimiter=',',ndmin=2);lower=np.loadtxt(d/'stop_lower.csv',delimiter=',').reshape(-1);upper=np.loadtxt(d/'stop_upper.csv',delimiter=',').reshape(-1)
names=[r['label'] for r in csv.DictReader((d/'stop_rows.csv').open())]
n=A.shape[1];meta['box_rows']=3*n;lo=np.full(n,-np.inf);hi=np.full(n,np.inf)
for i in range(meta['box_rows']):
    nz=np.flatnonzero(A[i]!=0)
    if len(nz)!=1:raise ValueError('box row not one coordinate')
    j=nz[0];factor=A[i,j];l,u=lower[i]/factor,upper[i]/factor
    lo[j]=max(lo[j],min(l,u));hi[j]=min(hi[j],max(l,u))
geometry=[]
for i in range(meta['box_rows'],len(A)):
    maximum=float(A[i]@np.where(A[i]>=0,hi,lo));minimum=float(A[i]@np.where(A[i]>=0,lo,hi))
    geometry.append({'row':i,'label':names[i],'lower':float(lower[i]),'upper':None if not np.isfinite(upper[i]) else float(upper[i]),
                     'min_over_command_box':minimum,'max_over_command_box':maximum,'lower_deficit':float(lower[i]-maximum),
                     'individually_inconsistent_with_command_box':bool(lower[i]>maximum+1e-12 or minimum>upper[i]+1e-12)})
norms=np.linalg.norm(A,axis=1)
if np.any(norms==0):raise ValueError('zero row requires separate constant check')
scaled=A/norms[:,None];sl=lower/norms;su=upper/norms
finite_upper=np.isfinite(su);finite_lower=np.isfinite(sl)
matrix=np.vstack([np.column_stack([scaled[finite_upper],np.ones(sum(finite_upper))]),np.column_stack([-scaled[finite_lower],np.ones(sum(finite_lower))])])
rhs=np.r_[su[finite_upper],-sl[finite_lower]];objective=np.r_[np.zeros(n),-1.]
lp=linprog(objective,A_ub=matrix,b_ub=rhs,bounds=[(None,None)]*(n+1),method='highs')
lp_report={'success':bool(lp.success),'status':int(lp.status),'message':lp.message}
if lp.success:
    candidate=lp.x[:n];values=A@candidate;violation=np.maximum.reduce([np.zeros(len(A)),lower-values,values-upper])
    lp_report.update({'max_normalized_row_common_margin_rad_s':float(lp.x[-1]),'original_SI_max_violation':float(max(violation)),
                      'candidate_velocity':candidate.tolist(),'worst_original_row':int(np.argmax(violation)),
                      'worst_original_label':names[int(np.argmax(violation))]})
plain=linprog(np.zeros(n),A_ub=np.vstack([A[np.isfinite(upper)],-A[np.isfinite(lower)]]),b_ub=np.r_[upper[np.isfinite(upper)],-lower[np.isfinite(lower)]],bounds=[(None,None)]*n,method='highs')
report={'scope':'Actual guarded stop QP captured in full matched-prefix replay; not original failed trial command matrix; no stop command accepted',
         'case':str(a.case),'source_sha256':sha(__file__),'files':{x.name:sha(x) for x in d.iterdir() if x.is_file()},
         'box_intervals':{'lower':lo.tolist(),'upper':hi.tolist(),'nonempty':bool(np.all(lo<=hi))},'geometry_rows':geometry,
         'plain_feasibility_LP':{'success':bool(plain.success),'status':int(plain.status),'message':plain.message},'normalized_margin_LP':lp_report,
         'infeasible_geometry_box_witness':any(r['individually_inconsistent_with_command_box'] for r in geometry)}
write_new(a.output,report);print(json.dumps(report,indent=2))

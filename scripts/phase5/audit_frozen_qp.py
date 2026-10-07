#!/usr/bin/env python3
"""Read-only independent feasibility/scale audit of a frozen QP.

Uses SciPy HiGHS for feasibility, not production OSQP or controller code.
This is an offline numerical diagnostic; no controls are issued and no robot
performance/safety or QP objective optimality is inferred from a feasible LP.
Input directory: H.csv,A.csv,g.csv,l.csv,u.csv (no headers), optional seed.csv,
F.csv, row_labels.txt and metadata.json. All effective inputs are hashed.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import linprog
from scipy.sparse import csr_matrix,vstack

def load(d):
    out={}
    for key in ('H','A','g','l','u'):
        out[key]=np.loadtxt(d/(key+'.csv'),delimiter=',',ndmin=2 if key in ('H','A') else 1)
    n=out['g'].size;m=out['l'].size
    if out['H'].shape!=(n,n) or out['A'].shape!=(m,n) or out['u'].shape!=(m,):raise ValueError('Dimension mismatch')
    if not all(np.isfinite(out[k]).all() for k in ('H','A','g')):raise ValueError('Nonfinite matrix/objective')
    if np.isnan(out['l']).any() or np.isnan(out['u']).any():raise ValueError('NaN bounds')
    if np.isposinf(out['l']).any() or np.isneginf(out['u']).any():raise ValueError('Wrong infinite bound direction')
    if (d/'row_labels.txt').exists():out['labels']=(d/'row_labels.txt').read_text().splitlines()
    else:out['labels']=[str(i) for i in range(m)]
    if len(out['labels'])!=m:raise ValueError('Label count mismatch')
    if (d/'seed.csv').exists():
        out['seed']=np.loadtxt(d/'seed.csv',delimiter=',',ndmin=1)
        if out['seed'].shape!=(n,) or not np.isfinite(out['seed']).all():raise ValueError('Bad seed')
    return out

def violation(p,x):
    ax=p['A']@x
    residual=np.maximum(np.maximum(p['l']-ax,ax-p['u']),0)
    worst=np.argsort(residual)[-10:][::-1]
    return {'max_original_row_violation':float(np.max(residual,initial=0)),
      'worst_rows':[{'row':int(i),'label':p['labels'][i],'violation':float(residual[i])} for i in worst]}

def audit(p):
    H,A,g,lo,hi=[p[k] for k in ('H','A','g','l','u')];n=len(g);m=len(lo)
    rownorm=np.max(np.abs(A),axis=1,initial=0);colnorm=np.max(np.abs(A),axis=0,initial=0)
    eq=np.isfinite(lo)&np.isfinite(hi)&(lo==hi)
    # Normalize only the independent LP rows for numerical conditioning. Verify
    # its returned point on the original SI constraints, without a scaled tolerance.
    scales=np.ones(m);nz=rownorm>0;scales[nz]=1/rownorm[nz]
    if not np.isfinite(scales).all():raise ValueError('Nonfinite normalization')
    As=csr_matrix(A*scales[:,None]);ls=lo*scales;us=hi*scales
    upper=(~eq)&np.isfinite(hi);lower=(~eq)&np.isfinite(lo)
    aub=vstack([As[upper],-As[lower]],format='csr');bub=np.r_[us[upper],-ls[lower]]
    begin=time.perf_counter()
    lp=linprog(np.zeros(n),A_ub=aub if aub.shape[0] else None,b_ub=bub if len(bub) else None,
      A_eq=As[eq] if np.any(eq) else None,b_eq=ls[eq] if np.any(eq) else None,
      bounds=[(None,None)]*n,method='highs',
      options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9,'time_limit':30})
    elapsed=time.perf_counter()-begin
    scale=max(1.,float(np.max(np.abs(H),initial=0)))
    eig=np.linalg.eigvalsh((H+H.T)/(2*scale))
    d={'scope':'offline independent linear feasibility and matrix-scale diagnostic; no objective optimum/robot acceptance',
      'numpy_version':np.__version__,'scipy_version':scipy.__version__,'variables':n,'rows':m,
      'equality_rows':int(eq.sum()),'inconsistent_bound_rows':int((lo>hi).sum()),
      'zero_coefficient_rows':int((rownorm==0).sum()),'zero_coefficient_columns':int((colnorm==0).sum()),
      'row_coefficient_max_min_nonzero':float(np.min(rownorm[nz])) if nz.any() else None,
      'row_coefficient_max_max':float(np.max(rownorm,initial=0)),
      'hessian_scale':scale,'normalized_symmetry_frobenius':float(np.linalg.norm((H-H.T)/scale)),
      'normalized_min_eigenvalue':float(np.min(eig)),'normalized_max_eigenvalue':float(np.max(eig)),
      'lp_status':int(lp.status),'lp_message':str(lp.message),'lp_iterations':int(lp.nit),'lp_elapsed_s':elapsed,
      'status':'UNRESOLVED'}
    if 'seed' in p:d['nominal']=violation(p,p['seed'])
    if lp.success and lp.x is not None and np.isfinite(lp.x).all():
        d['feasible_point']=violation(p,lp.x)
        d['status']='FEASIBLE_POINT_VERIFIED' if d['feasible_point']['max_original_row_violation']<=1e-7 else 'LP_POINT_FAILS_ORIGINAL_ROWS'
    elif lp.status==2:d['status']='HIGHS_REPORTS_INFEASIBLE_NOT_FORMAL_PROOF'
    return d,lp.x if lp.success else None

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    if a.output.exists():ap.error('Refuse output overwrite')
    p=load(a.input);d,x=audit(p)
    # Hash every file in this frozen directory including producer metadata.
    d['inputs_sha256']={str(f.relative_to(a.input)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(a.input.rglob('*')) if f.is_file()}
    d['auditor_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if (a.input/'F.csv').exists():
        F=np.loadtxt(a.input/'F.csv',delimiter=',',ndmin=2)
        if F.shape[1]!=len(p['g']) or not np.isfinite(F).all():raise ValueError('Invalid factor')
        d['normalized_gram_error_frobenius']=float(np.linalg.norm((F.T@F-p['H'])/d['hessian_scale']))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    if x is not None:
        point=a.output.with_name(a.output.stem+'-feasible-point.csv')
        if point.exists():raise ValueError('Refuse point overwrite')
        np.savetxt(point,x,delimiter=',',fmt='%.17g');d['feasible_point_sha256']=hashlib.sha256(point.read_bytes()).hexdigest()
    a.output.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');print(json.dumps(d,indent=2,allow_nan=False))

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Independent frozen tracking-weight assembly sweep audit (not robot trials)."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);a=p.parse_args()
if a.output.exists():p.error('Refuse overwrite')
manifest_bytes=a.manifest.read_bytes();manifest=json.loads(manifest_bytes);assert len(manifest)==12
by_path={r['snapshot']:r for r in manifest};assert len(by_path)==12
rows=[];ident={};unchanged=['A.csv','l.csv','u.csv','seed.csv','initial_q.csv','initial_v.csv','accepted_q.csv','accepted_v.csv','previous_command_acc.csv','previous_model_acc.csv']
for tick in [499,500]:
 for form in ['condensed','lifted']:
  paths=[a.base/f'tracking-numerics-v1-tracking-{w}-{form}-tick{tick}' for w in [100,1000,10000]]
  H=[];g=[];metas=[]
  for d in paths:
   m=by_path[str(d)];metas.append(m)
   for name,sha in m['snapshot_files'].items():assert hashlib.sha256((d/name).read_bytes()).hexdigest()==sha
   ident[str(d)]=m['snapshot_files'];H.append(np.loadtxt(d/'H.csv',delimiter=','));g.append(np.loadtxt(d/'g.csv',delimiter=','))
  assert all(len({m['snapshot_files'][name] for m in metas})==1 for name in unchanged)
  dH=(H[1]-H[0])/900;dg=(g[1]-g[0])/900;dH2=(H[2]-H[0])/9900;dg2=(g[2]-g[0])/9900
  he=float(np.max(np.abs(dH-dH2)));ge=float(np.max(np.abs(dg-dg2)));scale=max(1.,float(np.max(np.abs(dH))))
  mineig=float(np.linalg.eigvalsh((dH+dH.T)/(2*scale)).min());assert he<1e-12 and ge<1e-12 and mineig>=-1e-12
  rows.append({'tick':tick,'form':form,'variables':len(g[0]),'constraints_histories_initial_state_unchanged':True,'tracking_weight_linear_hessian_error':he,'tracking_weight_linear_gradient_error':ge,'normalized_min_eigenvalue_of_added_tracking_cost':mineig})
assert a.manifest.read_bytes()==manifest_bytes
for name,m in by_path.items():
 for file,sha in m['snapshot_files'].items():assert hashlib.sha256((Path(name)/file).read_bytes()).hexdigest()==sha
d={'scope':__doc__.strip(),'status':'PASS','comparisons':rows,'snapshot_files_sha256':ident,'completed_manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),'numpy':np.__version__,'auditor_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({k:v for k,v in d.items() if k!='snapshot_files_sha256'},indent=2))

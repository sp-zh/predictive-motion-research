from pathlib import Path
import json,subprocess,shlex,hashlib
D=Path('/private/tmp/phase5_nonzero_progress_active_v1_20261011');remote=json.loads((D/'REMOTE.json').read_text())['remote']
old=Path('/private/tmp/root_independent_dynamic_actual_review_20261011/SOURCE_SNAPSHOT.py').read_text();readers=old[old.index('class R:'):old.index('def state(')]+old[old.index('def reduction('):old.index('def readmap(')]+old[old.index('def inline_full('):old.index('def candidate_value(')]
s='''from pathlib import Path
import resource,signal,os,struct,json,hashlib
resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));signal.alarm(40);os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import numpy as np
'''+readers+'''
p=Path(%r);out=p/'pure144-fixture-v1';out.mkdir(exist_ok=False)
base=Path('/home/codextransfer/predictive_motion/results/phase5/session-geometry-qp-three-cycle-v4-20261011-attempt30/run-attempt1/artifacts/cycle-0');names=['inline_qp.bin','qp_equality_reduction.bin'];before={n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names};q=inline_full((base/names[0]).read_bytes());d=reduction((base/names[1]).read_bytes());assert q['H'].shape==(160,160) and q['A'].shape==(14756,160) and d['E'].shape==(16,160) and len(d['eq'])==16
Z=np.zeros((160,144));Z[:144]=np.eye(144);offset=np.zeros(160)
for j in range(8):
 row=d['E'][8+j];pivot=144+j;offset[pivot]=d['rhs'][8+j]/row[pivot];Z[pivot]=-row[:144]/row[pivot]
assert np.max(np.abs(d['E']@Z))<1e-12 and np.max(np.abs(d['E']@offset-d['rhs']))<1e-12
rows=[r for r in d['rows'] if r>=0];H=Z.T@q['H']@Z;g=Z.T@(q['g']+q['H']@offset);Dscale=1/np.sqrt(np.diag(H));A=q['A'][rows]@Z;l=q['l'][rows]-q['A'][rows]@offset;u=q['u'][rows]-q['A'][rows]@offset;extraA=[];extral=[];extrau=[]
for k in range(20):
 for j in range(7):
  c=8*k+j;extraA.append(Z[c]);extral.append(-.000999-offset[c]);extrau.append(.000999-offset[c])
# Source30 initial current has s=r=previousb=0, as bound by original progress
# first-jerk original row and rhs. This archived fixture is not a new forecast.
index={name:i for i,(name,units) in enumerate(q['labels'])};first=index['input/jerk/cell/0/7'];assert q['l'][first]==-5 and q['u'][first]==5;previousb=0.
for k in range(20):
 c=8*k+7;v=Z[c]/.004;shift=offset[c]/.004
 if k:v=v-Z[c-8]/.004;shift-=offset[c-8]/.004
 else:shift-=previousb/.004
 extraA.append(v);extral.append(-4.999-shift);extrau.append(4.999-shift)
A=np.vstack([A,np.asarray(extraA)]);l=np.r_[l,extral];u=np.r_[u,extrau];As=A*Dscale;Rscale=1/np.maximum(1,np.max(np.abs(As),axis=1));As*=Rscale[:,None];ls=l*Rscale;us=u*Rscale;Hs=Dscale[:,None]*H*Dscale[None,:];gs=Dscale*g
assert np.count_nonzero(q['seed'][:144])==0 and min(ls)>=-1e300 and max(us)<=1e300 and np.max(ls)<=1e-12 and np.min(us)>=-1e-12
with (out/'input.bin').open('xb') as f:
 for a in [Hs,gs,As,ls,us]:
  assert np.isfinite(a).all()
  for dim in a.shape:f.write(struct.pack('<Q',dim))
  f.write(np.asarray(a,dtype='<f8').tobytes(order='C'))
np.savez(out/'INPUTS.npz',H=Hs,g=gs,A=As,l=ls,u=us,Z=Z,p=offset,D=Dscale,originalH=q['H'],originalg=q['g'],originalA=q['A'],originall=q['l'],originalu=q['u'],originalF=q['F'],originalf=q['f'],current_nominal_seed=q['seed'],base_original_rows=rows)
assert before=={n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names}
result={'fixture_path':str(out/'input.bin'),'fixture_sha256':hashlib.sha256((out/'input.bin').read_bytes()).hexdigest(),'fixture_bytes':(out/'input.bin').stat().st_size,'archived_source_hashes':before,'reduced_dim':144,'rows':len(ls),'original_rows':14756,'extra_alpha_rows':140,'extra_progress_jerk_rows':20,'previousb':previousb,'scope':'numpy mathematics fixture of saved30 initial QP; no new forecast/native OSQP/physics/current33exactIEEE claim','Model':0,'Scene':0,'MuJoCo':0};(out/'READY.json').write_text(json.dumps(result,indent=2)+'\\n');print(json.dumps(result))
'''%remote
(D/'pure_fixture33.py').write_text(s)
files={'pure_fixture33.py':s};code='''from pathlib import Path
import sys,json
p=Path(%r)
for n,b in json.load(sys.stdin).items():
 with (p/n).open('x') as f:f.write(b)
'''%remote
x=subprocess.run(['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(code)],input=json.dumps(files).encode(),capture_output=True,timeout=25);assert x.returncode==0,x.stderr;print('pure144 fixture source staged only; no evaluation yet')

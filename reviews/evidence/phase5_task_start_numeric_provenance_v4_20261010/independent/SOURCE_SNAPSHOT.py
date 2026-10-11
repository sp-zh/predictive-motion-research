"""Bounded saved-array/guess provenance arithmetic; never solve or call Model.
Uses NumPy products only, no scipy, optimization, project imports or native calls.
"""
import hashlib,json,struct,tarfile
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent
PACK=Path('/private/tmp/phase5_task_start_numeric_repairs_checkpoint_v4_20261010')
ORACLE=Path('/private/tmp/phase5_task_start_oracle_checkpoint_v2_20261010/actual-dell/task-start-linear-oracle-v2-20261010-attempt1/oracle-artifacts-attempt1')
PINS={}
SS=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p,expected=None):
 b=p.read_bytes();h=sha(b)
 if expected:assert h==expected,(str(p),h,expected)
 PINS[str(p)]={'bytes':len(b),'sha256':h};return b
def npz(p):
 pin(p);a=np.load(p,allow_pickle=False);result={k:a[k] for k in a.files}
 assert all(x.dtype.kind in 'fi' and np.isfinite(x).all() for x in result.values())
 return result
def digest(arrays,c=None):
 h=hashlib.sha256()
 for v in arrays:
  for n in v.shape:h.update(struct.pack('<Q',n))
  h.update(np.asarray(v,dtype='<f8').tobytes(order='C'))
 if c is not None:h.update(struct.pack('<d',c))
 return h.hexdigest()
class Reader:
 def __init__(self,b,role):self.b=b;self.i=0;assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1' and self.text()==role
 def u(self):assert self.i+8<=len(self.b);v=struct.unpack_from('<Q',self.b,self.i)[0];self.i+=8;return v
 def d(self):assert self.i+8<=len(self.b);v=struct.unpack_from('<d',self.b,self.i)[0];self.i+=8;return v
 def text(self):n=self.u();assert n<=len(self.b)-self.i;v=self.b[self.i:self.i+n].decode();self.i+=n;return v
 def nums(self,n):assert n<=10_000_000 and self.i+8*n<=len(self.b);v=np.frombuffer(self.b,dtype='<f8',count=n,offset=self.i).copy();self.i+=8*n;return v
 def vec(self):return self.nums(self.u())
 def mat(self):r,c=self.u(),self.u();return self.nums(r*c).reshape(r,c)
 def end(self):assert self.i==len(self.b)
def packet_artifact(p,readysha,name):
 m=json.loads(pin(p/'READY.json',readysha))['files'];matches=[k for k in m if k.endswith('/'+name) and '/run-attempt1/artifacts/' in k];assert len(matches)==1
 q=p/matches[0];return pin(q,m[matches[0]]['sha256'])
def external_guess(b,role,subset=False):
 r=Reader(b,role);path,h,original,scaled=[r.text() for _ in range(4)]
 if subset:r.text()
 x,y,state,alpha,bprev=r.vec(),r.vec(),r.nums(30),r.nums(7),r.d();r.end()
 return dict(path=path,sha=h,original=original,scaled=scaled,x=x,y=y,state=state,alpha=alpha,bprev=bprev)
def inline_original(b):
 r=Reader(b,'INLINE_QP_COMPLETE_OR_RETAINED_PREFIX');r.text();r.text()
 for _ in range(7):r.u()
 r.text();r.u()
 for _ in range(3):r.d()
 r.u();H,g,A,l,u=r.mat(),r.vec(),r.mat(),r.vec(),r.vec();r.d();F,f=r.mat(),r.vec();r.vec();c=r.d()
 labels=[(r.text(),r.text()) for _ in range(r.u())]
 assert H.shape==(160,160) and A.shape==(13156,160) and F.shape==(741,160)
 return dict(H=H,g=g,A=A,l=l,u=u,F=F,f=f,c=c,labels=labels)
def maximum(x):return float(np.max(np.abs(x))) if np.size(x) else 0.
def kkt(H,g,A,l,u,x,y):
 ax=A@x;vio=np.maximum(np.maximum(l-ax,ax-u),0)
 cp=np.maximum(y,0)*(u-ax)+np.maximum(-y,0)*(ax-l)
 return {'scaled_box_violation':float(vio.max()),'stationarity_inf':maximum(H@x+g+A.T@y),'signed_complementarity_maxabs':maximum(cp),'worst_scaled_row':int(vio.argmax()),'dual_nonzero':int(np.count_nonzero(y))}
def history(U,guess):
 w=np.array(guess['w']);C=np.array(guess['C']);a=np.array(guess['previous_alpha']);s=guess['s'];r=guess['r'];bprev=guess['previous_b'];fails=[];tick=0;maxj=0.
 for k,n in enumerate([1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40]):
  s0,r0=s,r;alpha=U[8*k:8*k+7];b=U[8*k+7]
  for t in range(n):
   tick+=1;nw=w+.004*alpha;nC=C+.004*nw;ia=(nw-w)/.004;j=(ia-a)/.004;bj=(b-bprev)/.004;maxj=max(maxj,abs(float(bj)))
   if np.any(np.abs(alpha)>1) or np.any(np.abs(ia)>1) or np.any(np.abs(j)>20) or np.any(np.abs(nw)>.0625):fails.append({'kind':'command','tick':tick})
   for j in range(7):
    row=original['labels'].index((f'command/C/tick/{tick}/{j}','rad'));offset=guess['C'][j]+tick*.004*guess['w'][j]
    if nC[j]<original['l'][row]+offset or nC[j]>original['u'][row]+offset:fails.append({'kind':'command_C_position','tick':tick,'joint':j})
   if abs(b)>.5 or abs(bj)>5:fails.append({'kind':'progress_jerk','tick':tick,'b':float(b),'jerk':float(bj)})
   for half in (1,2):
    dt=.004*t+.002*half;ss=s0+dt*r0+.5*dt*dt*b;rr=r0+dt*b
    if not(0<=ss<=1 and 0<=rr<=.2):fails.append({'kind':'half_progress','tick':tick,'half':half,'s':float(ss),'r':float(rr)})
   ns=s+.004*r+.5*.004*.004*b;nr=r+.004*b
   if not(0<=ns<=1 and 0<=nr<=.2):fails.append({'kind':'recursive_progress','tick':tick,'s':float(ns),'r':float(nr)})
   C,w,s,r,a,bprev=nC,nw,ns,nr,ia,b
 return {'cycles':tick,'failures':len(fails),'first_failure':fails[0] if fails else None,'final_r':float(r),'final_w_maxabs':maximum(w),'max_literal_progress_jerk':maxj}

ready=pin(PACK/'READY.json','673350a4f4a9bf6ab32356eff904c346b7a7fcbf432328f99f8dd4a94959075f');manifest=json.loads(ready)['files'];assert len(manifest)==60
for name,v in manifest.items():assert len(pin(PACK/name,v['sha256']))==v['bytes']
archive=PACK/'actual_collection.tar.gz';tar_names=[]
with tarfile.open(archive,'r:gz') as tf:
 for m in tf.getmembers():
  assert m.isfile() or m.isdir()
  if not m.isfile():continue
  rel=Path(m.name);assert not rel.is_absolute() and '..' not in rel.parts
  name='actual-dell/'+m.name;assert name in manifest
  data=tf.extractfile(m).read();assert len(data)==manifest[name]['bytes'] and sha(data)==manifest[name]['sha256'];tar_names.append(name)
assert len(tar_names)==53 and len(set(tar_names))==53
(OUT/'PACKET_READY_READ.json').write_bytes(ready)
for name in ['derive_stabilization_numeric_guess.py','derive_stabilization_numeric_guess2.py','refine_stabilization_active_set.py','collect_task_start_numeric_repairs4.py']:(OUT/name).write_bytes((PACK/name).read_bytes())
basepath=ORACLE/'ACTUAL_ORACLE_INPUTS.npz';pin(basepath,'3fa8228457f27b66208a1b3b02547b0727a65946a99bc9e2651c8f98d1decdc0');a=npz(basepath)
ref=npz(ORACLE/'FOR_NUMERICAL_REFERENCE_ONLY.npz')['solver_x']
H,g,A,l,u=[a[k] for k in ['H','g','A','l','u']];assert H.shape==(144,144) and A.shape==(6211,144)
A2=Path('/private/tmp/phase5_task_start_a_checkpoint_v1_20261010')
original=inline_original(packet_artifact(A2,'17d59d457b1ba039141883a211e5259717a012f6dd8a48c5b81f892e5dbef3b6','inline_qp.bin'))
original_digest=digest([original[k] for k in ['H','g','A','l','u','F','f']],original['c'])
A5=Path('/private/tmp/phase5_task_start_a_primaldual_checkpoint_v2_20261010')
A7=Path('/private/tmp/phase5_task_start_stabilization_checkpoint_v2_20261010')
used5=external_guess(packet_artifact(A5,'2da3d50c450279d672b602316256412c89406dc1d7814b4e503c3dc5968dbf14','external_numeric_guess.bin'),'EXTERNAL_ALGEBRA_PRIMAL_DUAL_OPTIMIZER_GUESS_V2_NOT_CANDIDATE')
used7=external_guess(packet_artifact(A7,'5146ccede2eef1edeac17d1b7c3674675a2c3065633cafa0ca349497b7667294','external_numeric_guess.bin'),'STABILIZATION_B_ZERO_PRIMAL_DUAL_GUESS_V1_NOT_CANDIDATE',True)
results=[]
for attempt in [2,3,4]:
 path=PACK/f'actual-dell/task-start-dual-guess-v1-20261010-attempt{attempt}'
 assert pin(path/'BEFORE_INPUTS.json')==pin(path/'AFTER_INPUTS.json')
 assert pin(path/'SDK_BEFORE.json')==pin(path/'SDK_AFTER.json')
 nn=npz(path/'ACTUAL_NNLS_INPUTS.npz');n=npz(path/'NUMERICAL_GUESS_ONLY.npz');guess=json.loads(pin(path/'guess.json'))
 faces=nn['side_rows'];assert faces.shape==(23,2) and set(faces[:,1])<=set([-1,1])
 M=np.stack([sign*A[k] for k,sign in faces],axis=1)
 assert np.array_equal(nn['M'],M)
 target_error=maximum(nn['target']+(H@ref+g));assert target_error<=2e-16
 x=n['primal_x'];y=n['dual_y'];weights=n['weights'];assert np.min(weights)>=0
 expected_y=np.zeros(6211)
 for (k,sign),weight in zip(faces,weights):expected_y[k]+=sign*weight
 if attempt==2:assert np.array_equal(expected_y,y)
 if attempt in [3,4]:
  v=npz(path/'ACTUAL_KKT_REFINEMENT.npz');active=v['active_faces'];B=M[:,active].T
  K=np.block([[H,B.T],[B,np.zeros((len(active),len(active)))]])
  rhs=np.concatenate([-g,np.array([sign*(u[k] if sign==1 else l[k]) for k,sign in faces[active]])])
  assert np.array_equal(v['K'],K) and np.array_equal(v['rhs'],rhs) and np.array_equal(v['solution'][:144],x)
  expected_y[:]=0
  for (k,sign),weight in zip(faces[active],v['solution'][144:]):expected_y[k]+=sign*weight
  assert np.array_equal(expected_y,y) and np.min(v['solution'][144:])>=0
  kres=maximum(K@v['solution']-rhs)
 else:kres=None
 gx=np.array(guess['solver_coordinates']);gy=np.array(guess['dual_coordinates'])
 assert guess['original_problem_sha256']==original_digest and guess['transformed_problem_sha256']==digest([H,g,A,l,u])
 fields=np.concatenate([guess[k] for k in ['q','v','C','w']]+[[guess['s'],guess['r']]])
 assert fields.tobytes()==used5['state'].tobytes() and np.array(guess['previous_alpha']).tobytes()==used5['alpha'].tobytes() and struct.pack('<d',guess['previous_b'])==struct.pack('<d',used5['bprev'])
 actual_used=sha((path/'guess.json').read_bytes())==used5['sha']
 if actual_used:assert gx.tobytes()==used5['x'].tobytes() and gy.tobytes()==used5['y'].tobytes()
 U=a['p']+a['Z']@(a['D']*gx)
 fullax=original['A']@U;fullvio=np.maximum(np.maximum(original['l']-fullax,fullax-original['u']),0)
 results.append({'attempt':attempt,'full_original_SI_max':float(fullvio.max()),'guess_sha256':sha((path/'guess.json').read_bytes()),'actual_A5_used':actual_used,'guess_primal_matches_saved_NPZ':np.array_equal(gx,x),'guess_dual_matches_saved_NPZ':np.array_equal(gy,y),'NNLS_target_product_roundoff':target_error,'saved_KKT_system_residual':kres,'saved_primal_dual':kkt(H,g,A,l,u,x,y),'JSON_hint_pair':kkt(H,g,A,l,u,gx,gy),'literal_history':history(U,guess)})

cols=np.array([k*8+j for k in range(18) for j in range(7)]);Hs=H[np.ix_(cols,cols)];gs=g[cols];As=A[:,cols]
stab=PACK/'actual-dell/task-start-stabilization-numeric-guess-v1-20261010-repair2';st=npz(stab/'ACTUAL_STABILIZATION_INPUTS.npz')
for k,v in {'H':Hs,'g':gs,'A':As,'l':l,'u':u,'columns':cols}.items():assert np.array_equal(st[k],v)
post=npz(stab/'POST_KKT_DIAGNOSTIC.npz');sx=npz(stab/'SLSQP_REFERENCE_ONLY.npz')['x'];assert np.array_equal(sx,post['reference_x'])
postmetrics=kkt(Hs,gs,As,l,u,post['x'],post['y'])
asp=PACK/'actual-dell/task-start-stabilization-active-set-v1-20261010';last=npz(asp/'LATEST_DIAGNOSTIC.npz');sn=npz(asp/'NUMERICAL_GUESS_ONLY.npz');sg=json.loads(pin(asp/'guess.json'));faces=last['faces'];B=np.stack([sign*As[k] for k,sign in faces]);K=np.block([[Hs,B.T],[B,np.zeros((len(faces),len(faces)))]])
rhs=np.concatenate([-gs,np.array([sign*(u[k] if sign==1 else l[k]) for k,sign in faces])]);sol=np.concatenate([last['x'],last['lambda_faces']]);assert np.array_equal(last['K'],K) and np.array_equal(last['rhs'],rhs) and np.array_equal(last['x'],sn['primal_x'])
expected_y=np.zeros(6211)
for (k,sign),weight in zip(faces,last['lambda_faces']):expected_y[k]+=sign*weight
assert np.array_equal(expected_y,sn['dual_y']) and np.min(last['lambda_faces'])>=0
assert sha((asp/'guess.json').read_bytes())==used7['sha'] and np.array(sg['solver_coordinates']).tobytes()==used7['x'].tobytes() and np.array(sg['dual_coordinates']).tobytes()==used7['y'].tobytes()
assert sg['original_problem_sha256']==original_digest and sg['transformed_problem_sha256']==digest([Hs,gs,As,l,u])
assert np.array(sg['solver_coordinates']).tobytes()==sn['primal_x'].tobytes() and np.array(sg['dual_coordinates']).tobytes()==sn['dual_y'].tobytes()
sgfields=np.concatenate([sg[k] for k in ['q','v','C','w']]+[[sg['s'],sg['r']]])
assert sgfields.tobytes()==used7['state'].tobytes() and np.array(sg['previous_alpha']).tobytes()==used7['alpha'].tobytes() and struct.pack('<d',sg['previous_b'])==struct.pack('<d',used7['bprev'])
U=a['p']+a['Z'][:,cols]@(a['D'][cols]*sn['primal_x']);assert np.all(U[7::8]==0)
fullax=original['A']@U;fullvio=np.maximum(np.maximum(original['l']-fullax,fullax-original['u']),0)
stabmetrics=kkt(Hs,gs,As,l,u,sn['primal_x'],sn['dual_y']);stabmetrics.update(full_original_SI_max=float(fullvio.max()),saved_KKT_system_residual=maximum(K@sol-rhs),literal_history=history(U,sg),actual_A7_used=True,guess_sha256=used7['sha'])
probes=[]
for eta in ['1e-08','1e-07','1e-06']:
 path=PACK/'actual-dell/task-start-inner-jerk-probe-v1-20261010';v=npz(path/f'probe-{eta}.npz');U2=a['p']+a['Z']@(a['D']*v['solver_x']);assert maximum(U2-v['originalU'])<1e-14
 actual=original['A']@v['originalU'];vio=np.maximum(np.maximum(original['l']-actual,actual-original['u']),0)
 probes.append({'eta':eta,'stronger_problem':kkt(H,g,A,v['strong_lower'],v['strong_upper'],v['solver_x'],v['solver_y']),'full_original_SI_max':float(vio.max()),'literal_history':history(v['originalU'],sg),'actual_A5_or_A7_used':False})
summary={'schema':'ROOT_NUMERIC_HINT_PROVENANCE_FILE_REVIEW_V1','source_sha256':SS,'verified_packet_files':60,'verified_packet_bytes':sum(v['bytes'] for v in manifest.values()),'archive_verified_regular_payloads':53,'input_pins':PINS,'original_problem_sha256':original_digest,'dual_guess_attempts':results,'stabilization_rejected_initial_KKT':postmetrics,'stabilization_final_hint':stabmetrics,'inner_progress_guard_explorations':probes,'new_optimizer_Model_native_calls':0,'complete_dual_derivation_source_present':False,'scope':'numerical hint provenance supplement; no independent optimizer/oracle optimum/native candidate claim','phase5':'NOT_ACCEPTED'}
for name,v in manifest.items():assert len(pin(PACK/name,v['sha256']))==v['bytes']
for name,identity in list(PINS.items()):
 data=Path(name).read_bytes();assert len(data)==identity['bytes'] and sha(data)==identity['sha256']
assert sha(Path(__file__).read_bytes())==SS
(OUT/'SOURCE_SNAPSHOT.py').write_bytes(Path(__file__).read_bytes());(OUT/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='input_pins'},indent=2))

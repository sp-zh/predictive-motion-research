"""Independent saved-array arithmetic only: no optimizer/Model/native invocation."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
OUT=Path(__file__).resolve().parent
PACK=Path('/private/tmp/phase5_pilot_inputtrust_pure_checkpoint_v2_20261011')
NUM=PACK/'actual-dell/pilot-inputtrust-numeric-guess-v2-20261010'
DRIVER=PACK/'actual-dell/pilot-inputtrust-numeric-driver-v2-20261010'
ORACLE=Path('/private/tmp/phase5_task_start_oracle_checkpoint_v2_20261010')
OBASE=ORACLE/'actual-dell/task-start-linear-oracle-v2-20261010-attempt1/oracle-artifacts-attempt1'
PINS={};SS=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p,h=None):
 b=p.read_bytes();actual=sha(b)
 if h:assert actual==h,(str(p),actual,h)
 PINS[str(p)]={'bytes':len(b),'sha256':actual};return b
def npz(p):
 pin(p);z=np.load(p,allow_pickle=False);d={k:z[k] for k in z.files};assert all(x.dtype.kind in 'fi' and np.isfinite(x).all() for x in d.values());return d
def digest(arrays,c=None):
 h=hashlib.sha256()
 for x in arrays:
  for n in x.shape:h.update(struct.pack('<Q',n))
  h.update(np.asarray(x,dtype='<f8').tobytes(order='C'))
 if c is not None:h.update(struct.pack('<d',c))
 return h.hexdigest()
class Reader:
 def __init__(self,b,role):self.b=b;self.i=0;assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1' and self.text()==role
 def u(self):assert self.i+8<=len(self.b);n=struct.unpack_from('<Q',self.b,self.i)[0];self.i+=8;return n
 def d(self):assert self.i+8<=len(self.b);n=struct.unpack_from('<d',self.b,self.i)[0];self.i+=8;return n
 def text(self):n=self.u();assert n<=len(self.b)-self.i;s=self.b[self.i:self.i+n].decode();self.i+=n;return s
 def nums(self,n):assert n<=10_000_000 and self.i+n*8<=len(self.b);x=np.frombuffer(self.b,dtype='<f8',count=n,offset=self.i).copy();self.i+=n*8;return x
 def vec(self):return self.nums(self.u())
 def mat(self):n,m=self.u(),self.u();return self.nums(n*m).reshape(n,m)
def maxabs(x):return float(np.max(np.abs(x)))
ready=pin(PACK/'READY.json','7454dce3190d5761a4f24a1587e2889856806e076288171b68f616ab3a52440f');manifest=json.loads(ready)['files'];assert len(manifest)==65
for name,identity in manifest.items():assert len(pin(PACK/name,identity['sha256']))==identity['bytes']
(OUT/'INPUT_READY_READ.json').write_bytes(ready)
plan=json.loads(pin(DRIVER/'pure_plan.json','2c01609b28f8a54dd9b4bdb5230059d43f1cd1da01b8b0a77814a241e92d0472'));rows=plan['input_files'];assert len(rows)==1350
control=DRIVER/'control-attempt1';before=pin(control/'BEFORE_INPUT_IDENTITIES.json');after=pin(control/'AFTER_INPUT_IDENTITIES.json');assert before==after
recorded=json.loads(before);assert len(recorded)==1350
for declared,actual in zip(rows,recorded):
 for k in ['requested_path','resolved_path','bytes','sha256']:assert actual[k]==declared[k]
assert pin(NUM/'BEFORE_INPUTS.json')==pin(NUM/'AFTER_INPUTS.json') and pin(NUM/'SDK_BEFORE.json')==pin(NUM/'SDK_AFTER.json')
inputsha=json.loads((NUM/'BEFORE_INPUTS.json').read_text());sdk=dict(json.loads((NUM/'SDK_BEFORE.json').read_text()));assert len(inputsha)==3 and len(sdk)==1345
for k,expected in [('INPUTS',inputsha),('SDK',sdk)]:
 result=json.loads(pin(NUM/f'FINAL_{k}_CHECK.json'));assert result['passed'] is True and result['observed']==expected
batch=json.loads(pin(control/'BUILD_RESULT.json'));assert batch['complete'] is True and len(batch['records'])==1 and batch['records'][0]['exit']==0 and batch['records'][0]['argv']==plan['compile_argv'][0]
sr=json.loads(pin(PACK/'phase5_pilot_inputtrust_ahead_review_v3_20261010/READY.json','374c592d7a1481c9860953612f4623ee054e1a6683f5a7d3ee46d7e9caa1da51'))
for name,v in sr['files'].items():assert pin(PACK/'phase5_pilot_inputtrust_ahead_review_v3_20261010'/name,v['sha256'])==pin(Path('/private/tmp/phase5_pilot_inputtrust_ahead_review_v3_20261010')/name,v['sha256'])
assert pin(DRIVER/'derive_numeric_guess.py','85049a4fd1a8eafdf8ce4e9fc81a8c0218427a365d26c71eb43a108dddcc8a12')==pin(PACK/'phase5_pilot_inputtrust_ahead_review_v3_20261010/derive_numeric_guess.py')
pin(OBASE/'ACTUAL_ORACLE_INPUTS.npz','3fa8228457f27b66208a1b3b02547b0727a65946a99bc9e2651c8f98d1decdc0');a=npz(OBASE/'ACTUAL_ORACLE_INPUTS.npz')
oldguesspath=ORACLE/'actual-dell/task-start-numeric-guess-v1-20261010/guess.json';oldguess=json.loads(pin(oldguesspath,'b9563e031892611491bfab40d7126e5de3858f25dc2adb85bc132fd6904fce01'))
cols=np.array([8*k+j for k in range(18) for j in range(7)]);alpha=np.array([8*k+j for k in range(20) for j in range(7)])
H=a['H'][np.ix_(cols,cols)];g=a['g'][cols];baseA=a['A'][:,cols];Z=a['Z'][:,cols];D=a['D'][cols];p=a['p'];guard=Z[alpha]*D[None,:];R=1/np.maximum(1,np.max(abs(guard),axis=1));A=np.vstack([baseA,R[:,None]*guard]);l=np.r_[a['l'],R*(-.000999-p[alpha])];u=np.r_[a['u'],R*(.000999-p[alpha])]
actual=npz(NUM/'ACTUAL_INPUTTRUST_INPUTS.npz');expected=dict(H=H,g=g,A=A,l=l,u=u,Z=Z,D=D,p=p,guard_original_columns=alpha,guard_multiplier=R)
for k,v in expected.items():assert actual[k].shape==v.shape and actual[k].dtype==v.dtype and actual[k].tobytes()==v.tobytes(),k
assert A.shape==(6351,126) and np.all((R>0)&(R<=1)) and np.all(guard[-7:]==0)
guess=json.loads(pin(NUM/'guess.json','433cf19bd6a50bccd14b738384560d0fee078be4aa04395c2dfbf39c63f46c41'));hint=npz(NUM/'NUMERICAL_GUESS_ONLY.npz');x=hint['primal_x'];y=hint['dual_y'];U=hint['originalU']
assert x.shape==(126,) and y.shape==(6351,) and U.shape==(160,) and np.array(guess['solver_coordinates']).tobytes()==x.tobytes() and np.array(guess['dual_coordinates']).tobytes()==y.tobytes()
for k in ['q','v','C','w','previous_alpha']:assert np.array(guess[k],dtype='<f8').tobytes()==np.array(oldguess[k],dtype='<f8').tobytes()
for k in ['s','r','previous_b']:assert struct.pack('<d',guess[k])==struct.pack('<d',oldguess[k])
scaledhash=digest([H,g,A,l,u]);assert scaledhash==guess['transformed_problem_sha256']=='a9f3cdb85c7757a9ee6dd85beaf6a69ce79dde961eee4353c9a1685aed184ba8'
assert guess['solver_alpha_guard']==.000999 and guess['strict_alpha_guard']==.001 and np.all(abs(U[alpha])<=.001) and np.all(U[7::8]==0)
reconstruction=maxabs(U-(p+Z@(D*x)));assert reconstruction<1e-14
k=npz(NUM/'LATEST_KKT_DIAGNOSTIC.npz');faces=k['faces'];assert faces.shape==(126,2) and set(faces[:,1])<=set([-1,1]) and np.all((faces[:,0]>=0)&(faces[:,0]<6351))
B=np.array([sign*A[row] for row,sign in faces]);K=np.block([[H,B.T],[B,np.zeros((126,126))]]);rhs=np.r_[-g,[sign*(u[row] if sign==1 else l[row]) for row,sign in faces]]
assert np.array_equal(k['K'],K) and np.array_equal(k['rhs'],rhs) and k['solution'][:126].tobytes()==x.tobytes()
lam=k['solution'][126:];assert np.min(lam)>=0;ey=np.zeros(6351)
for (row,sign),weight in zip(faces,lam):ey[row]+=sign*weight
assert ey.tobytes()==y.tobytes()
ax=A@x;vio=np.maximum(np.maximum(l-ax,ax-u),0);station=H@x+g+A.T@y;cp=np.maximum(y,0)*(u-ax)+np.maximum(-y,0)*(ax-l)
A2=Path('/private/tmp/phase5_task_start_a_checkpoint_v1_20261010');am=json.loads(pin(A2/'READY.json','17d59d457b1ba039141883a211e5259717a012f6dd8a48c5b81f892e5dbef3b6'))['files'];name=next(n for n in am if n.endswith('/artifacts/inline_qp.bin'))
r=Reader(pin(A2/name,am[name]['sha256']),'INLINE_QP_COMPLETE_OR_RETAINED_PREFIX');r.text();r.text();[r.u() for _ in range(7)];r.text();r.u();[r.d() for _ in range(3)];r.u();OH,Og,OA,Ol,Ou=r.mat(),r.vec(),r.mat(),r.vec(),r.vec();r.d();OF,Of=r.mat(),r.vec();r.vec();Oc=r.d();labels=[(r.text(),r.text()) for _ in range(r.u())]
assert OA.shape==(13156,160) and OF.shape==(741,160);originalhash=digest([OH,Og,OA,Ol,Ou,OF,Of],Oc);assert originalhash==guess['original_problem_sha256']==oldguess['original_problem_sha256']
originalvio=np.maximum(np.maximum(Ol-OA@U,OA@U-Ou),0);terminal=[i for i,(label,units) in enumerate(labels) if label.startswith('terminal/')];assert len(terminal)==16
cost_original=.5*U@OH@U+Og@U+Oc;cost_scaled=.5*x@H@x+g@x+float(a['constant']);T=Z*D[None,:];graderror=maxabs(T.T@(OH@U+Og)-(H@x+g))
assert abs(cost_original-cost_scaled)<1e-11 and graderror<1e-11
labelindex={label:i for i,(label,units) in enumerate(labels)};C=np.array(guess['C']);w=np.array(guess['w']);previous=np.array(guess['previous_alpha']);s=guess['s'];pr=guess['r'];pb=guess['previous_b'];tick=0;fails=[];maxcmdj=0.
for cell,n in enumerate([1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40]):
 s0,r0=s,pr;cmd=U[cell*8:cell*8+7];b=U[cell*8+7]
 for i in range(n):
  tick+=1;nw=w+.004*cmd;nc=C+.004*nw;implied=(nw-w)/.004;jerk=(implied-previous)/.004;maxcmdj=max(maxcmdj,maxabs(jerk))
  if np.any(abs(cmd)>1) or np.any(abs(implied)>1) or np.any(abs(jerk)>20) or np.any(abs(nw)>.0625):fails.append(('command',tick))
  for j in range(7):
   row=labelindex[f'command/C/tick/{tick}/{j}'];offset=guess['C'][j]+tick*.004*guess['w'][j]
   if nc[j]<Ol[row]+offset or nc[j]>Ou[row]+offset:fails.append(('C',tick,j))
  if abs(b)>.5 or abs((b-pb)/.004)>5:fails.append(('b',tick))
  for half in [1,2]:
   dt=.004*i+.002*half;sr=s0+dt*r0+.5*dt*dt*b;rr=r0+dt*b
   if not(0<=sr<=1 and 0<=rr<=.2):fails.append(('half_progress',tick,half))
  ns=s+.004*pr+.5*.004*.004*b;nr=pr+.004*b
  if not(0<=ns<=1 and 0<=nr<=.2):fails.append(('recursive_progress',tick))
  C,w,s,pr,previous,pb=nc,nw,ns,nr,implied,b
assert tick==200 and not fails and s==pr==pb==0
record=json.loads(pin(NUM/'RESULT.json'));assert record['bindings_valid'] is True and record['Model']==record['physical_steps']==record['commits']==0 and record['slsqp_success'] is True
sx=npz(NUM/'SLSQP_REFERENCE_ONLY.npz')['x'];sv=np.maximum(np.maximum(l-A@sx,A@sx-u),0)
summary={'schema':'ROOT_ACTUAL_PURE_INPUTTRUST_FILE_ARITHMETIC_V1','source_sha256':SS,'packet_files':65,'packet_bytes':sum(v['bytes'] for v in manifest.values()),'input_pins':PINS,'outer1350_before_after_metadata_match_frozen_plan':True,'inner_three_input_and1345SDK_final_guards_pass':True,'frozen_source_Ahead3_verified':True,'augmented_arrays_all_byte_exact_independent_generation':True,'original_problem_digest':originalhash,'scaled_problem_digest':scaledhash,'all140_guard_coordinates_verified':alpha.tolist(),'guard_rows_include_dependent18_and_zero19':True,'guard_R_minmax':[float(R.min()),float(R.max())],'guess_JSON_primal_dual_and_actual_history_byte_bound':True,'guess_sha256':'433cf19bd6a50bccd14b738384560d0fee078be4aa04395c2dfbf39c63f46c41','alpha_original_max':maxabs(U[alpha]),'reconstruction_error':reconstruction,'KKT':{'faces':126,'system_residual':maxabs(K@k['solution']-rhs),'stationarity':maxabs(station),'scaled_box_violation':float(vio.max()),'complementarity':maxabs(cp),'minimum_face_multiplier':float(lam.min())},'full_original_SI':{'rows':13156,'max_violation':float(originalvio.max()),'terminal16_max_residual':maxabs(OA[terminal]@U-Ol[terminal])},'objective_and_gradient':{'original_value':float(cost_original),'reduced_scaled_value':float(cost_scaled),'value_difference':abs(float(cost_original-cost_scaled)),'gradient_difference':graderror},'strict_literal_history':{'cycles':200,'failures':0,'max_command_jerk':maxcmdj,'final_w_max':maxabs(w),'exact_beta_s_r_b_zero':True},'SLSQP_recorded':{'iterations':record['slsqp_iterations'],'elapsed':record['slsqp_elapsed_seconds'],'saved_reference_box_violation':float(sv.max()),'KKT_refine_events':len(record['events'])},'new_optimizer_Model_native_calls':0,'no_accepted_native_candidate':True,'scope':'additional optimizer-subdomain numeric hint only; no unrestricted optimum/B/C/plant/phase acceptance','phase5':'NOT_ACCEPTED'}
for path,v in list(PINS.items()):data=Path(path).read_bytes();assert len(data)==v['bytes'] and sha(data)==v['sha256']
assert sha(Path(__file__).read_bytes())==SS
(OUT/'SOURCE_SNAPSHOT.py').write_bytes(Path(__file__).read_bytes());(OUT/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ['input_pins','all140_guard_coordinates_verified']},indent=2))

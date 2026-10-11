"""Actual attempt12 B refusal: file parsing and independent saved-array arithmetic.
No Model/native/compiler/solver/SSH calls. Future raw values are predictions only.
"""
from pathlib import Path
import hashlib,json,struct,csv
import numpy as np
OUT=Path(__file__).resolve().parent
PACK=Path('/private/tmp/phase5_pilot_bc_checkpoint_v5_20261010')
UNIT=PACK/'actual-dell/session-task-start-pilot-bc-v5-20261010-attempt12'
BASE=UNIT/'run-attempt1/artifacts'
PINS={};SS=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def pin(p,h=None):
 b=p.read_bytes();actual=hashlib.sha256(b).hexdigest()
 if h:assert actual==h,(str(p),actual,h)
 PINS[str(p)]={'bytes':len(b),'sha256':actual};return b
class R:
 def __init__(self,b,role):self.b=b;self.i=0;assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1' and self.text()==role
 def u(self):assert self.i+8<=len(self.b);x=struct.unpack_from('<Q',self.b,self.i)[0];self.i+=8;return x
 def signed(self):x=self.u();return x-(1<<64) if x>=(1<<63) else x
 def d(self):assert self.i+8<=len(self.b);x=struct.unpack_from('<d',self.b,self.i)[0];self.i+=8;return x
 def text(self):n=self.u();assert n<=len(self.b)-self.i;s=self.b[self.i:self.i+n].decode();self.i+=n;return s
 def nums(self,n):assert n<=10_000_000 and self.i+n*8<=len(self.b);x=np.frombuffer(self.b,dtype='<f8',count=n,offset=self.i).copy();self.i+=n*8;return x
 def vec(self):return self.nums(self.u())
 def mat(self):n,m=self.u(),self.u();return self.nums(n*m).reshape(n,m)
 def end(self):assert self.i==len(self.b),(self.i,len(self.b))
def state(r):
 vs=[r.vec() for _ in range(4)];assert all(x.shape==(7,) for x in vs);return np.concatenate(vs+[[r.d(),r.d()]])
def identity(r):return dict(path=r.text(),sha256=r.text(),bytes=r.u())
def metadata(r):
 m=dict(pinocchio_version=r.text(),nq=r.u(),nv=r.u())
 for k in ['joint_names','frame_names']:m[k]=[r.text() for _ in range(r.u())]
 for k in ['idx_q','idx_v','joint_nq','joint_nv']:m[k]=[r.signed() for _ in range(r.u())]
 for k in ['masses','armature','gravity','R','B','damping']:m[k]=r.vec().tolist()
 return m
def values(r):
 points=[]
 for _ in range(r.u()):
  p=dict(cell=r.u(),cycle=r.u(),half=r.u(),time=r.d(),s=r.d(),r=r.d())
  for k in ['q','v','C','w','force']:p[k]=r.vec();assert p[k].shape==(7,) and np.isfinite(p[k]).all()
  p['branches']=[r.signed() for _ in range(r.u())];p.update(iterations=r.u(),kkt=r.d(),control_clips=r.u(),force_clips=r.u())
  assert len(p['branches'])==7 and np.isfinite(p['kkt']) and p['kkt']<=1e-10
  points.append(p)
 cycles=[state(r) for _ in range(r.u())];cells=[state(r) for _ in range(r.u())]
 return points,cycles,cells
def inline(b):
 r=R(b,'INLINE_QP_COMPLETE_OR_RETAINED_PREFIX');r.text();error=r.text();info=[r.u() for _ in range(7)];r.text();r.u();[r.d() for _ in range(3)];geo=r.u()
 H,g,A,l,u=r.mat(),r.vec(),r.mat(),r.vec(),r.vec();r.d();F,f,seed=r.mat(),r.vec(),r.vec();constant=r.d();labels=[(r.text(),r.text()) for _ in range(r.u())]
 return H,g,A,l,u,F,f,seed,constant,labels,info,geo,error
def snapshot(b):
 r=R(b,'ACTUAL_NATIVE_SESSION_SNAPSHOT');ids=[r.text(),r.text()];boundary=[r.u(),r.u()];complete=r.u();stage,error=r.text(),r.text();[r.u() for _ in range(3)];time,age=r.d(),r.d();contact=r.u();x=r.nums(30);alpha=r.nums(7);b=r.d();available=r.u();v,a=r.nums(7),r.nums(7);steps=r.u();source=r.text();ib,ia=r.vec(),r.vec();r.end()
 assert complete==available==contact==1 and not error and np.array_equal(ib,ia)
 return dict(ids=ids,boundary=boundary,time=time,age=age,x=x,alpha=alpha,b=b,v=v,a=a,steps=steps,source=source,ib=ib,ia=ia)
def maxabs(x):return float(np.max(np.abs(x)))
ready=pin(PACK/'READY.json','5320992b8ec6334d07bc37a58b5750053090f62d960c3c757b78beb3b391bdd9');manifest=json.loads(ready)['files'];assert len(manifest)==558
for name,x in manifest.items():assert len(pin(PACK/name,x['sha256']))==x['bytes']
(OUT/'PACKET_READY_READ.json').write_bytes(ready)
receipts={};receipt_fields={};current=None
def scalar(v):
 if v in ('true','false'):return v=='true'
 if v.isdecimal():return int(v)
 if v.startswith(chr(34)):return json.loads(v)
 return v
for line in pin(BASE/'MANIFEST.yaml').decode().splitlines():
 if line=='files:':continue
 if line.startswith('  - file: '):
  name=scalar(line[len('  - file: '):]);assert name not in receipts;current={};receipts[name]=current
 elif line.startswith('    '):key,v=line[4:].split(': ',1);assert key not in current;current[key]=scalar(v)
 else:key,v=line.split(': ',1);assert key not in receipt_fields;receipt_fields[key]=scalar(v)
for name,v in receipts.items():
 data=pin(BASE/name,v['sha256']);assert len(data)==v['bytes'] and v['created'] and v['hash_valid'] and v['complete'] and not v['error'];R(data,v['role'])
assert sum(v['bytes'] for v in receipts.values())==receipt_fields['output_bytes'] and receipt_fields['execution_permission'] is False
oldsource=Path('/private/tmp/phase5_pilot_bc_ahead_review_v5_20261010');oldready=json.loads(pin(oldsource/'READY.json','7495e8ecd0bf8c169eda2eb3bd18471e0bc48c556390bd6ae5eac54a86b9dc97'))
for name,v in oldready['files'].items():assert pin(PACK/'ahead-source-profile-v5'/name,v['sha256'])==pin(oldsource/name,v['sha256'])
profile=json.loads(pin(UNIT/'profile-version1/active_input.json','0ae467e18237636f9af77a0c893ccaaacecc7f8d6d0bde17ea09b597e8250a10'))
profile['producer']=json.loads(pin(UNIT/'profile-version1/PRODUCER.json'))
for name in ['candidate_validation.cpp','runtime_observer.cpp','model_boundary.cpp','active_first_cycle.cpp','lossless_evidence.cpp']:(OUT/name).write_bytes((PACK/'ahead-source-profile-v5/src'/name).read_bytes())
before,after=[snapshot(pin(BASE/name)) for name in ['observation_before.bin','observation_after.bin']]
assert before['steps']==after['steps']==1000 and before['boundary']==after['boundary']==[0,0]
assert before['x'].tobytes()==after['x'].tobytes() and before['ib'].tobytes()==after['ib'].tobytes() and before['alpha'].tobytes()==after['alpha'].tobytes() and before['b']==after['b']==0
r=R(pin(BASE/'actual_warmup.bin','ddfe59b603e0caa2ef85b0bb3e3e14a75e4f57a639cc22f8bad2fda249802901'),'ACTUAL_TASK_INITIALIZATION_AND_PHYSICAL_WARMUP_V2');warmflags=[r.u() for _ in range(4)];r.text();assert not r.text();r.nums(7);r.d();r.d();r.text();wn=r.u();assert wn==1000
for i in range(wn):
 step=r.u();wt=r.d();native,readn,reads=r.u(),r.u(),r.u();wq,wv,wC,wa,wj=[r.nums(7) for _ in range(5)];[r.u() for _ in range(4)];[r.u() for _ in range(8)];r.d();r.d();r.u();r.d();r.d();r.text();assert not r.text()
r.end();assert step==1000
assert wq.tobytes()==before['x'][:7].tobytes() and wv.tobytes()==before['x'][7:14].tobytes()==before['v'].tobytes() and wa.tobytes()==before['a'].tobytes() and wt==before['time']
r=R(pin(BASE/'model_open.bin'),'SESSION_STARTUP_VERIFIED_METADATA');meta=metadata(r);r.end()
r=R(pin(BASE/'original_nominal.bin'),'ORIGINAL_GENUINE_NOMINAL_BEFORE_ADAPTER');tags=[r.text() for _ in range(5)];ids=[identity(r) for _ in range(4)];sid=r.text();deps=[identity(r) for _ in range(r.u())];libs=[identity(r) for _ in range(r.u())];assert metadata(r)==meta
x0=r.nums(30);a0=r.nums(7);b0=r.d();bound=r.u();mesh=[r.u() for _ in range(r.u())];nomcontrols=[]
for _ in range(r.u()):nomcontrols.append((r.u(),r.vec(),r.d()))
assert r.u()==1;nomflags=[r.u(),r.u()];nomerror=r.text();nomfinal=state(r);ext=r.u();uncert=r.signed();exterr=r.text();nom,ncycles,ncells=values(r)
def readmap():
 m=dict(cell=r.u(),cycle=r.u(),half=r.u())
 for k in ['origin','state','cell_origin']:m[k]=state(r)
 m['u']=r.vec()
 for k in ['A','B','cell_A','cell_B']:m[k]=r.mat()
 m['d'],m['cell_d']=r.vec(),r.vec();return m
maps={k:[readmap() for _ in range(r.u())] for k in ['half','cycle','cell']};r.end()
assert not tags[0] and not tags[1] and bound==ext==1 and uncert==-1 and nomflags==[1,1] and not nomerror and not exterr
assert x0.tobytes()==before['x'].tobytes() and a0.tobytes()==before['alpha'].tobytes() and b0==before['b'] and mesh==[1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40]
assert [len(nom),len(ncycles),len(ncells),len(maps['half']),len(maps['cycle']),len(maps['cell'])]==[400,200,20,400,200,20]
assert all(n==mesh[k] and np.all(a==0) and b==0 for k,(n,a,b) in enumerate(nomcontrols))
assert ids[0]==profile['producer'] and ids[1:]==[profile[k] for k in ['xml','constants','expected_metadata']] and libs==profile['loaded_libraries'] and deps==profile['dependencies']
r=R(pin(BASE/'candidate_value.bin'),'ORIGINAL_GENUINE_CANDIDATE_VALUE_NO_EXECUTION');facts=[r.u() for _ in range(3)];metapresent=r.u();assert metapresent==1 and metadata(r)==meta
transport,nomdigest,vdigest=r.text(),r.text(),r.text();vx=r.nums(30);controls=[]
for _ in range(r.u()):controls.append((r.u(),r.vec(),r.d()))
assert r.u()==1;vflags=[r.u(),r.u()];verror=r.text();vfinal=state(r);value,vcycles,vcells=values(r);r.end()
assert facts==[1,1,1] and vflags==[1,1] and not transport and not verror and nomdigest==tags[2] and vx.tobytes()==x0.tobytes()
assert [len(value),len(vcycles),len(vcells)]==[400,200,20] and len(controls)==20 and all(n==mesh[k] and b==0 for k,(n,a,b) in enumerate(controls))
for k,p in enumerate(value):
 z=np.r_[p['q'],p['v'],p['C'],p['w'],p['s'],p['r']]
 if k%2==1:assert z.tobytes()==vcycles[k//2].tobytes()
endindex=0
for k,n in enumerate(mesh):
 endindex+=2*n;p=value[endindex-1];z=np.r_[p['q'],p['v'],p['C'],p['w'],p['s'],p['r']];assert z.tobytes()==vcells[k].tobytes()
assert vfinal.tobytes()==vcells[-1].tobytes()
r=R(pin(BASE/'candidate_validation.bin'),'FULL_PREDICTED_VALUE_DOMAINS_AND_DISCRETE_INTERPOLATION_V1');assessed,passed=r.u(),r.u();astage,aerror=r.text(),r.text();reach,radius,sigmaL=r.d(),r.d(),r.d();iscope=r.text();checks=[]
for _ in range(r.u()):
 p=dict(sample=r.u(),cell=r.u(),cycle=r.u(),half=r.u(),elapsed=r.d(),a=r.nums(7),j=r.nums(7))
 for k in ['true','cover','sigma','geometry_lower','sigma_lower','affine_error','trust']:p[k]=r.d()
 p.update(queries=r.u(),complete=r.u(),stage=r.text(),error=r.text());checks.append(p)
r.end();assert assessed==1 and passed==0 and len(checks)==53 and sum(p['complete'] for p in checks)==52
qp=inline(pin(BASE/'inline_qp.bin'));H,g,A,l,u,F,f,seed,c,labels,info,geo,qp_error=qp;assert not qp_error and A.shape==(13156,160) and F.shape==(741,160) and geo==0
A7=Path('/private/tmp/phase5_task_start_stabilization_checkpoint_v2_20261010');am=json.loads(pin(A7/'READY.json','5146ccede2eef1edeac17d1b7c3674675a2c3065633cafa0ca349497b7667294'))['files'];an=[n for n in am if n.endswith('/artifacts/inline_qp.bin')];assert len(an)==1
oldqp=inline(pin(A7/an[0],am[an[0]]['sha256']))
for i in range(9):assert np.array_equal(qp[i],oldqp[i])
assert labels==oldqp[9]
r=R(pin(BASE/'candidate.bin'),'SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');stop=r.text();cf=[r.u() for _ in range(7)];r.signed();U=r.vec();metric=[r.d() for _ in range(14)];[r.u() for _ in range(4)];r.text();counts=[r.u() for _ in range(4)];rowv=r.vec();r.u();[r.d() for _ in range(4)];[r.u() for _ in range(2)];preview=r.u()
assert preview==1
previewjoint=[r.nums(7) for _ in range(5)];previewprogress=[r.d() for _ in range(4)];r.nums(2);r.nums(2);[r.u() for _ in range(2)];tail=r.u();assert tail==1;r.nums(7);r.nums(7);r.d();r.d();exacttail=r.u();request=r.u();assert request==1
requestx=r.nums(30);requestboundary=[r.u(),r.u()];requestids=[r.text() for _ in range(3)];requestmesh=[r.u() for _ in range(20)];requestcontrols=[r.nums(8) for _ in range(r.u())];r.end()
assert cf[:3]==[0,1,1] and cf[3:]==[0,1,0,1] and U.shape==(160,) and len(rowv)==13156 and np.all(U[7::8]==0)
assert requestx.tobytes()==x0.tobytes() and requestboundary==[0,0] and requestids[:2]==before['ids'] and requestids[2]==nomdigest and requestmesh==mesh
for k,(n,a,b) in enumerate(controls):assert np.r_[a,b].tobytes()==requestcontrols[k].tobytes()==U[k*8:k*8+8].tobytes()
originalax=A@U;vios=np.maximum(np.maximum(l-originalax,originalax-u),0);assert vios.max()<=1e-7 and maxabs(vios-rowv)<1e-11
strict_tick=0;strict_fail=[];sc=x0[14:21].copy();sw=x0[21:28].copy();sa=a0.copy();ss=x0[28];sr=x0[29];sb=b0;labelindex={label:i for i,(label,unit) in enumerate(labels)}
for k,n in enumerate(mesh):
 origin_s,origin_r=ss,sr;alpha=U[k*8:k*8+7];b=U[k*8+7]
 for tick in range(n):
  strict_tick+=1;nw=sw+.004*alpha;nc=sc+.004*nw;implied=(nw-sw)/.004;jerk=(implied-sa)/.004
  if np.any(abs(alpha)>1) or np.any(abs(implied)>1) or np.any(abs(jerk)>20) or np.any(abs(nw)>.0625):strict_fail.append(('command',strict_tick))
  for j in range(7):
   row=labelindex[f'command/C/tick/{strict_tick}/{j}'];offset=x0[14+j]+strict_tick*.004*x0[21+j]
   if nc[j]<l[row]+offset or nc[j]>u[row]+offset:strict_fail.append(('C',strict_tick,j))
  if abs(b)>.5 or abs((b-sb)/.004)>5:strict_fail.append(('progress_derivative',strict_tick))
  for half in [1,2]:
   dt=.004*tick+.002*half;sref=origin_s+dt*origin_r+.5*dt*dt*b;rref=origin_r+dt*b
   if not (0<=sref<=1 and 0<=rref<=.2):strict_fail.append(('half_progress',strict_tick,half))
  ns=ss+.004*sr+.5*.004*.004*b;nr=sr+.004*b
  if not(0<=ns<=1 and 0<=nr<=.2):strict_fail.append(('recursive_progress',strict_tick))
  sc,sw,ss,sr,sa,sb=nc,nw,ns,nr,implied,b
assert strict_tick==200 and not strict_fail and ss==sr==sb==0
delta=np.zeros(30);C=x0[14:21].copy();w=x0[21:28].copy();previous_v=x0[7:14].copy();previous_a=before['a'].copy();previous_q=x0[:7].copy();index=0;diffs=[];derivatives=[];first=None;prefix_aerr=prefix_jerr=0.;neighbor=[];rowout=[];geointervalerr=0.
for k,n in enumerate(mesh):
 du=np.r_[controls[k][1],controls[k][2]]
 for cycle in range(1,n+1):
  w=w+.004*du[:7];C=C+.004*w
  for half in [1,2]:
   v=value[index];m=maps['half'][index];nompoint=nom[index];assert (v['cell'],v['cycle'],v['half'])==(k,cycle,half)==(m['cell'],m['cycle'],m['half'])
   assert abs(v['time']-.002*(index+1))<1e-10 and v['s']==v['r']==0 and v['control_clips']==v['force_clips']==0 and v['C'].tobytes()==C.tobytes() and v['w'].tobytes()==w.tobytes()
   z=np.r_[v['q'],v['v'],v['C'],v['w'],v['s'],v['r']];nz=np.r_[nompoint['q'],nompoint['v'],nompoint['C'],nompoint['w'],nompoint['s'],nompoint['r']];assert m['state'].tobytes()==nz.tobytes()
   predicted=nz+m['cell_A']@delta+m['cell_B']@du;difference=z-predicted;err=maxabs(difference);trust=maxabs(v['q']-nompoint['q']);ia=(v['v']-previous_v)/.002;ij=(ia-previous_a)/.002
   assert maxabs(v['q']-(previous_q+.002*v['v']))<=1e-12
   diffs.append(difference);derivatives.append((ia,ij))
   if first is None and (err>1e-6 or trust>.002):first=dict(sample=index,cell=k,cycle=cycle,half=half,time=v['time'],affine_error=err,trust=trust,component=int(np.argmax(abs(difference))))
   if index<len(checks):
    check=checks[index];assert (check['sample'],check['cell'],check['cycle'],check['half'])==(index,k,cycle,half)
    assert abs(check['affine_error']-err)<=2e-13 and abs(check['trust']-trust)<=2e-13
    prefix_aerr=max(prefix_aerr,maxabs(check['a']-ia));prefix_jerr=max(prefix_jerr,maxabs(check['j']-ij));assert maxabs(ia)<=5 and maxabs(ij)<=500 and np.all(abs(v['v'])<=np.array(profile['physical_speed']))
    if check['complete']:
     assert check['queries']>0 and min(check['true'],check['cover'])>=.005 and check['geometry_lower']>=.005 and check['sigma_lower']>=1e-6 and not check['error']
     if index>0:
      prev=checks[index-1];travel=float(np.abs(v['q']-previous_q).sum());geointervalerr=max(geointervalerr,abs(check['geometry_lower']-(min(prev['true'],prev['cover'],check['true'],check['cover'])-4*travel-1e-6)),abs(check['sigma_lower']-(min(prev['sigma'],check['sigma'])-32*travel)))
   if 49<=index<=54:neighbor.append(dict(sample=index,time=v['time'],nominal_branches=nompoint['branches'],candidate_branches=v['branches'],q_residual=difference[:7].tolist(),v_residual=difference[7:14].tolist(),nominal_force=nompoint['force'].tolist(),candidate_force=v['force'].tolist()))
   rowout.append([index,k,cycle,half,v['time']]+z.tolist()+predicted.tolist()+difference.tolist()+ia.tolist()+ij.tolist()+[err,trust,index<53,index<52])
   previous_q=v['q'];previous_v=v['v'];previous_a=ia;index+=1
 delta=maps['cell'][k]['cell_A']@delta+maps['cell'][k]['cell_B']@du
assert index==400 and first['sample']==52 and prefix_aerr==prefix_jerr==0
assert checks[-1]['complete']==0 and checks[-1]['queries']==0 and all(checks[-1][k]==0 for k in ['true','cover','sigma','geometry_lower','sigma_lower'])
assert checks[-1]['stage']=='ORIGINAL_AFFINE_AND_TRUST_MODEL_CHECK' and aerror=='original value-affine1e-6/jointtrust.002'
r=R(pin(BASE/'entry_completion.bin'),'ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING');stage,error=r.text(),r.text();same,sessionpass=r.u(),r.u();sf=r.text();simpass=r.u();simf=r.text();wall=r.d();steps,commits=r.u(),r.u();r.end();assert same==sessionpass==simpass==1 and not sf and not simf and steps==1000 and commits==0 and error==aerror
r=R(pin(BASE/'bootstrap.bin'),'ACTUAL_DIRECT_SESSION_API_ENTRIES');bootstrap=[r.u() for _ in range(9)];r.end();assert bootstrap==[1,2,1,1004,1002,2004,2,1000,0]
assert not (BASE/'actual_commit.bin').exists() and not (BASE/'actual_commit_journal.csv').exists()
run=UNIT/'run-attempt1';dispatch=json.loads(pin(run/'BATCH_PREFIX.json'));assert dispatch['native_project_entry_dispatches']==1 and len(dispatch['records'])==1 and dispatch['records'][0]['exit']==1
release=json.loads(pin(PACK/'ROOT_ONE_COMPONENT_RELEASE.json'));assert dispatch['records'][0]['argv']==release['sole_child_argv'] and release['ELF_sha256']==ids[0]['sha256'] and release['runtime_input_sha256']=='0ae467e18237636f9af77a0c893ccaaacecc7f8d6d0bde17ea09b597e8250a10'
beforepins=pin(run/'BEFORE_INPUT_IDENTITIES.json');afterpins=pin(run/'AFTER_INPUT_IDENTITIES.json');assert beforepins==afterpins;inputcount=len(json.loads(beforepins))
with (OUT/'independent_all400_value_affine_components.csv').open('w',newline='') as fd:
 names=['q'+str(j) for j in range(7)]+['v'+str(j) for j in range(7)]+['C'+str(j) for j in range(7)]+['w'+str(j) for j in range(7)]+['s','r']
 writer=csv.writer(fd);writer.writerow(['sample','cell','cycle','half','elapsed']+['predicted_value_'+x for x in names]+['global_affine_'+x for x in names]+['residual_'+x for x in names]+['predicted_a'+str(j) for j in range(7)]+['predicted_jerk'+str(j) for j in range(7)]+['max30','joint_trust','assessment_reached','geometry_assessment_completed']);writer.writerows(rowout)
summary={'schema':'ROOT_ACTUAL_B_REFUSAL_FILE_ARITHMETIC_V1','source_sha256':SS,'packet_payloads':558,'packet_bytes':sum(x['bytes'] for x in manifest.values()),'input_pins':PINS,'source_Ahead5_exact':True,'profile_ELF_declared':profile['producer'],'local_ELF_bytes_present_verified':False,'recorded_startup_termination_pin_count':inputcount,'recorded_pin_lists_before_after_exact':True,'artifact_receipts_verified':len(receipts),'artifact_receipt_bytes':receipt_fields['output_bytes'],'actual_dispatch_count':1,'raw_facts':facts,'raw_shapes':[400,200,20],'own_full400_recomputation':True,'first_failure':first,'failed_point_residual30':diffs[52].tolist(),'max30_all400':float(np.max(np.abs(diffs))),'max30_by_component':np.max(np.abs(diffs),axis=0).tolist(),'initial_physical_history_exact_actual_warmup_last_point':True,'first53_physical_a_jerk_record_difference':[prefix_aerr,prefix_jerr],'complete_geometry_points':52,'failed_point_geometry':'NOT_EVALUATED: zero aggregate defaults are not PASS','stored_geometry_sigma_interval_recompute_error_points1to51':geointervalerr,'first_geometry_initial_sigma_not_saved_not_independently_recomputed':True,'full_original_QP_arrays_exact_previousA7':True,'full_original_SI':{'rows':13156,'max_independent':float(vios.max()),'max_recorded':float(rowv.max()),'row_error':maxabs(vios-rowv)},'native_SOLVED':{'status':cf[3],'raw_status':cf[4],'api_error':cf[5],'iterations':cf[6],'setup':metric[3],'solve':metric[4]},'strict_actual_input_history':{'cycles':strict_tick,'failures':len(strict_fail),'exact_beta_s_r_b_zero':True,'final_w_maxabs':maxabs(sw)},'exact_tail':exacttail,'coincident_branch_neighborhood':neighbor,'branch_causality_claim':False,'completion':{'stage':stage,'error':error,'wall':wall,'boundary_unchanged':same,'termination_session':sessionpass,'termination_sim':simpass,'physical_steps':steps,'C_commits':commits},'no_new_Model_native_solver_calls':True,'phase5':'NOT_ACCEPTED'}
for path,v in list(PINS.items()):b=Path(path).read_bytes();assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==SS
(OUT/'SOURCE_SNAPSHOT.py').write_bytes(Path(__file__).read_bytes());(OUT/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ['input_pins','coincident_branch_neighborhood']},indent=2))

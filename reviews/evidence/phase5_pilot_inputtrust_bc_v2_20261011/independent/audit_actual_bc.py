"""Actual native14 restricted B400/C2: file parsing and independent saved-array arithmetic.
No Model/native/compiler/solver/SSH calls. Future raw values are predictions only.
"""
from pathlib import Path
import hashlib,json,struct,csv,argparse
import numpy as np
OUT=Path(__file__).resolve().parent
PACK=Path('/private/tmp/phase5_pilot_inputtrust_checkpoint_v2_20261011')
UNIT=PACK/'actual-dell/session-task-start-inputtrust-bc-v2-20261010-attempt14'
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
args=argparse.ArgumentParser();args.add_argument('--ready-sha',required=True);args=args.parse_args()
ready=pin(PACK/'READY.json',args.ready_sha);manifest=json.loads(ready)['files'];assert len(manifest)==429
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
oldsource=Path('/private/tmp/phase5_pilot_inputtrust_ahead_review_v3_20261010');oldready=json.loads(pin(oldsource/'READY.json','374c592d7a1481c9860953612f4623ee054e1a6683f5a7d3ee46d7e9caa1da51'))
for name,v in oldready['files'].items():
 if name.startswith('src/'):assert pin(UNIT/name,v['sha256'])==pin(oldsource/name,v['sha256'])
profile=json.loads(pin(UNIT/'profile-version1/active_input.json','3b442197a19376f69799aa0a9acb96a3d3334b42071cfb5c7cb36a448330189d'))
profile['producer']=json.loads(pin(UNIT/'profile-version1/PRODUCER.json'))
for name in ['candidate_validation.cpp','runtime_observer.cpp','model_boundary.cpp','active_first_cycle.cpp','lossless_evidence.cpp']:(OUT/name).write_bytes((UNIT/'src'/name).read_bytes())
before,after=[snapshot(pin(BASE/name)) for name in ['observation_before.bin','observation_after.bin']]
assert before['steps']==1000 and after['steps']==1002 and before['boundary']==[0,0] and after['boundary']==[1,1]
assert before['x'].tobytes()!=after['x'].tobytes() and before['ib'].tobytes()!=after['ib'].tobytes() and before['b']==after['b']==0
r=R(pin(BASE/'actual_warmup.bin','ddfe59b603e0caa2ef85b0bb3e3e14a75e4f57a639cc22f8bad2fda249802901'),'ACTUAL_TASK_INITIALIZATION_AND_PHYSICAL_WARMUP_V2');warmflags=[r.u() for _ in range(4)];r.text();assert not r.text();r.nums(7);r.d();r.d();r.text();wn=r.u();assert wn==1000
for i in range(wn):
 step=r.u();wt=r.d();native,readn,reads=r.u(),r.u(),r.u();wq,wv,wC,wa,wj=[r.nums(7) for _ in range(5)];[r.u() for _ in range(4)];[r.u() for _ in range(8)];warm_true=r.d();warm_cover=r.d();r.u();r.d();r.d();r.text();assert not r.text()
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
r.end();assert assessed==passed==1 and len(checks)==400 and sum(p['complete'] for p in checks)==400 and not aerror
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
   rowout.append([index,k,cycle,half,v['time']]+z.tolist()+predicted.tolist()+difference.tolist()+ia.tolist()+ij.tolist()+[err,trust,True,True])
   previous_q=v['q'];previous_v=v['v'];previous_a=ia;index+=1
 delta=maps['cell'][k]['cell_A']@delta+maps['cell'][k]['cell_B']@du
assert index==400 and first is None and prefix_aerr==prefix_jerr==0
assert all(p['complete']==1 and p['queries']==9035 for p in checks)
r=R(pin(BASE/'entry_completion.bin'),'ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING');stage,error=r.text(),r.text();same,sessionpass=r.u(),r.u();sf=r.text();simpass=r.u();simf=r.text();wall=r.d();steps,commits=r.u(),r.u();r.end();assert same==0 and sessionpass==simpass==1 and not sf and not simf and steps==1002 and commits==1 and error==aerror==''
r=R(pin(BASE/'bootstrap.bin'),'ACTUAL_DIRECT_SESSION_API_ENTRIES');bootstrap=[r.u() for _ in range(9)];r.end();assert bootstrap==[1,2,1,1006,1004,2010,2,1002,1]
# Actual commit parser/checks added below; these files are required.
assert (BASE/'actual_commit.bin').exists() and (BASE/'actual_commit_journal.csv').exists()
# All recorded reduced arrays and140 guards: compare independent prior pure inputs.
def reduction(data):
 rr=R(data,'STRUCTURED_ORIGINAL_TERMINAL_EQUALITY_REDUCTION');d={'policy':rr.text(),'stage':rr.text(),'valid':rr.u()}
 def ids():return [rr.signed() for _ in range(rr.u())]
 for name,fn in [('Z',rr.mat),('p',rr.vec),('E',rr.mat),('rhs',rr.vec),('eq',ids),('rows',ids),('Hr',rr.mat),('gr',rr.vec),('Ar',rr.mat),('lr',rr.vec),('ur',rr.vec),('D',rr.vec),('Fr',rr.mat),('seed',rr.vec),('x',rr.vec),('Y',rr.vec),('R',rr.vec),('Hs',rr.mat),('gs',rr.vec),('As',rr.mat),('ls',rr.vec),('us',rr.vec),('Fs',rr.mat),('solver_seed',rr.vec)]:d[name]=fn()
 d['tag']=rr.text();d['flags']=[rr.u() for _ in range(5)];d['rawx'],d['rawy']=rr.vec(),rr.vec();d['slots']=rr.u();d['errors']=[rr.d() for _ in range(5)];rr.end();return d
red=reduction(pin(BASE/'qp_equality_reduction.bin'));assert red['valid']==1 and red['Z'].shape==(160,126) and red['As'].shape==(6351,126) and len(red['rows'])==6351 and red['rows'][-140:]==[-1]*140
pure=Path('/private/tmp/phase5_pilot_inputtrust_pure_checkpoint_v2_20261011/actual-dell/pilot-inputtrust-numeric-guess-v2-20261010')
purepkg=Path('/private/tmp/phase5_pilot_inputtrust_pure_checkpoint_v2_20261011');pm=json.loads(pin(purepkg/'READY.json','7454dce3190d5761a4f24a1587e2889856806e076288171b68f616ab3a52440f'))['files']
pp=pure/'ACTUAL_INPUTTRUST_INPUTS.npz';pin(pp,pm[str(pp.relative_to(purepkg))]['sha256']);pa=np.load(pp,allow_pickle=False)
for akey,rkey in [('H','Hs'),('g','gs'),('A','As'),('l','ls'),('u','us'),('Z','Z'),('D','D'),('p','p')]:assert pa[akey].tobytes()==red[rkey].tobytes()
assert maxabs(U-(red['p']+red['Z']@(red['D']*red['x'])))<1e-14 and np.all(abs(U.reshape(20,8)[:,:7])<=.001)
rr=R(pin(BASE/'planning_guard.bin'),'EXPLICIT_OPTIMIZER_ORIGINAL_ALPHA_SUBSET_GUARD_V1');caps=[rr.d(),rr.d()];basecount=rr.u();guardcols=[rr.u() for _ in range(rr.u())];guardR=rr.vec();guardlabel=rr.text();guardscope=rr.text();rr.end()
assert caps==[.000999,.001] and basecount==6211 and guardcols==[8*k+j for k in range(20) for j in range(7)] and np.array_equal(guardR,pa['guard_multiplier']) and np.array_equal(red['R'][-140:],guardR)
assert np.array_equal(red['Ar'][-140:],red['Z'][guardcols]) and np.array_equal(red['lr'][-140:],-.000999-red['p'][guardcols]) and np.array_equal(red['ur'][-140:],.000999-red['p'][guardcols])
rr=R(pin(BASE/'solver_row_screen.bin'),'ORIGINAL_SI_INPUT_BOX_IMPLICATION_SCREEN');rr.text();kept=[rr.u() for _ in range(rr.u())];omitted=[rr.u() for _ in range(rr.u())];proofs=[rr.text() for _ in range(rr.u())];[rr.u() for _ in range(3)];rr.text();mappedrow=rr.signed();rr.text();scanned=rr.u();fullworst=rr.signed();fullmax=rr.d();rr.end();assert scanned==13156 and mappedrow==-1 and guardlabel=='internal_alpha_guard/cell/18/joint/1' and kept==red['rows'][:6211] and len(kept)==6211 and len(omitted)==6929
rr=R(pin(BASE/'external_numeric_guess.bin'),'STABILIZATION_B_ZERO_INPUT_TRUST_GUESS_V1_NOT_CANDIDATE');gpath,gsha,goriginal,gscaled=[rr.text() for _ in range(4)];rr.text();gx,gy=rr.vec(),rr.vec();gstate,ga,gb=rr.nums(30),rr.nums(7),rr.d();rr.end();gp=pure/'guess.json';pin(gp,'433cf19bd6a50bccd14b738384560d0fee078be4aa04395c2dfbf39c63f46c41');gj=json.loads(gp.read_bytes());assert gsha==profile['numeric_guess']['sha256']=='433cf19bd6a50bccd14b738384560d0fee078be4aa04395c2dfbf39c63f46c41' and gpath==profile['numeric_guess']['path']
assert gx.tobytes()==np.array(gj['solver_coordinates']).tobytes()==red['solver_seed'].tobytes() and gy.tobytes()==np.array(gj['dual_coordinates']).tobytes() and gstate.tobytes()==x0.tobytes() and ga.tobytes()==a0.tobytes() and gb==b0 and goriginal==gj['original_problem_sha256'] and gscaled==gj['transformed_problem_sha256']
# Actual two real substeps, separately measured and published only afterboth.
rr=R(pin(BASE/'actual_commit.bin'),'TWO_REAL_2MS_HELD_TARGET_COMMIT_OR_RETAINED_PARTIAL_V1');commitflags=[rr.u() for _ in range(4)];commitstage,commiterror=rr.text(),rr.text();cbefore=[rr.u(),rr.u()];cafter=[rr.u(),rr.u()];held=rr.nums(7);ctime0,ctime1=rr.d(),rr.d();commitpoints=[]
for _ in range(rr.u()):
 cp=dict(step=rr.u(),time=rr.d(),returned=rr.u(),native_read=rr.u(),scratch_read=rr.u())
 for name in ['q','v','C','a','j']:cp[name]=rr.nums(7)
 for name in ['jerk_available','geometry_complete','integration_guard','contacts']:cp[name]=rr.u()
 cp['warnings']=[rr.u() for _ in range(8)]
 for name in ['true','cover','tcp_error','arm_error','sigma','geometry_lower','sigma_lower']:cp[name]=rr.d()
 cp.update(queries=rr.u(),passed=rr.u(),stage=rr.text(),error=rr.text());commitpoints.append(cp)
rr.end();assert commitflags==[1,1,2,2] and cbefore==[0,0] and cafter==[1,1] and not commiterror and len(commitpoints)==2 and held.tobytes()==previewjoint[0].tobytes() and ctime0==before['time'] and ctime1==after['time']
prevq=x0[:7];prevv=x0[7:14];preva=before['a'];prevclear=min(warm_true,warm_cover);prevsigma=None;cmderr=0.;actualmodelerror=0.;actualintervalerror=0.
for i,cp in enumerate(commitpoints):
 assert cp['step']==i+1 and abs(cp['time']-ctime0-.002*(i+1))<=1e-10 and cp['returned']==cp['passed']==cp['jerk_available']==cp['geometry_complete']==cp['integration_guard']==1 and cp['native_read']==cp['scratch_read']==7 and cp['contacts']==0 and cp['warnings']==[0]*8 and cp['queries']==9035 and not cp['error']
 assert cp['C'].tobytes()==held.tobytes()==value[i]['C'].tobytes();aa=(cp['v']-prevv)/.002;jj=(aa-preva)/.002;assert aa.tobytes()==cp['a'].tobytes() and jj.tobytes()==cp['j'].tobytes() and maxabs(aa)<=5 and maxabs(jj)<=500 and np.all(abs(cp['v'])<=profile['physical_speed'])
 assert cp['tcp_error']<=1e-8 and cp['arm_error']<=1e-8 and cp['geometry_lower']>=.005 and cp['sigma_lower']>=1e-6
 travel=float(abs(cp['q']-prevq).sum());actualintervalerror=max(actualintervalerror,abs(cp['geometry_lower']-(min(prevclear,cp['true'],cp['cover'])-4*travel-1e-6)))
 if prevsigma is not None:actualintervalerror=max(actualintervalerror,abs(cp['sigma_lower']-(min(prevsigma,cp['sigma'])-32*travel)))
 actualmodelerror=max(actualmodelerror,maxabs(cp['q']-value[i]['q']),maxabs(cp['v']-value[i]['v']))
 prevq,prevv,preva,prevclear,prevsigma=cp['q'],cp['v'],aa,min(cp['true'],cp['cover']),cp['sigma']
assert after['x'][:7].tobytes()==prevq.tobytes() and after['x'][7:14].tobytes()==prevv.tobytes() and after['a'].tobytes()==preva.tobytes() and after['v'].tobytes()==prevv.tobytes()
assert after['x'][14:21].tobytes()==held.tobytes() and after['x'][21:28].tobytes()==previewjoint[1].tobytes() and after['alpha'].tobytes()==previewjoint[3].tobytes() and np.all(after['x'][28:]==0)
# Durable target-write +nativeattempt/return/checked phases and exact receipt.
journal=pin(BASE/'actual_commit_journal.csv');jrows=list(csv.reader(journal.decode().splitlines()));assert len(jrows)==8 and all(len(x)==58 for x in jrows)
expected=['BEFORE_VALIDATED_HELD_TARGET_WRITE','VALIDATED_HELD_TARGET_WRITTEN_NO_STEP_YET']+['BEFORE_NATIVE_COMMIT_STEP_ATTEMPT','NATIVE_COMMIT_STEP_RETURNED_BEFORE_SCRATCH','COMPLETE_ACTUAL_COMMIT_OBSERVATION_AND_GEOMETRY']*2
assert [x[0] for x in jrows]==expected
for i,row in enumerate(jrows):
 nums=np.array([float(v) for v in row[1:]]);assert nums[28:35].tobytes()==held.tobytes()
 if i>=2:
  cp=commitpoints[(i-2)//3];assert nums[0]==cp['step']
  phase=(i-2)%3
  if phase==0:assert np.array_equal(nums[2:5],[0,0,0])
  elif phase==1:assert np.array_equal(nums[2:5],[1,7,0]) and nums[14:21].tobytes()==cp['q'].tobytes() and nums[21:28].tobytes()==cp['v'].tobytes()
  else:
   assert np.array_equal(nums[2:5],[1,7,7]);assert nums[14:21].tobytes()==cp['q'].tobytes() and nums[21:28].tobytes()==cp['v'].tobytes() and nums[35:42].tobytes()==cp['a'].tobytes() and nums[42:49].tobytes()==cp['j'].tobytes()
rr=R(pin(BASE/'commit_journal_receipt.bin'),'ACTUAL_DURABLE_NATIVE_STEP_JOURNAL_PREFIX_V3');jpath,jsha=rr.text(),rr.text();jcounts=[rr.u() for _ in range(5)];jnote=rr.text();rr.end();assert jsha==hashlib.sha256(journal).hexdigest() and jcounts==[len(journal),len(journal),8,8,0]
run=UNIT/'run-attempt1';dispatch=json.loads(pin(run/'BATCH_PREFIX.json'));assert dispatch['native_project_entry_dispatches']==1 and len(dispatch['records'])==1 and dispatch['records'][0]['exit']==0
release=json.loads(pin(PACK/'ROOT_ONE_COMPONENT_RELEASE.json'));assert dispatch['records'][0]['argv']==release['sole_child_argv'] and release['ELF_sha256']==ids[0]['sha256'] and release['runtime_input_sha256']=='3b442197a19376f69799aa0a9acb96a3d3334b42071cfb5c7cb36a448330189d'
beforepins=pin(run/'BEFORE_INPUT_IDENTITIES.json');afterpins=pin(run/'AFTER_INPUT_IDENTITIES.json');assert beforepins==afterpins;inputcount=len(json.loads(beforepins))
with (OUT/'independent_all400_value_affine_components.csv').open('w',newline='') as fd:
 names=['q'+str(j) for j in range(7)]+['v'+str(j) for j in range(7)]+['C'+str(j) for j in range(7)]+['w'+str(j) for j in range(7)]+['s','r']
 writer=csv.writer(fd);writer.writerow(['sample','cell','cycle','half','elapsed']+['predicted_value_'+x for x in names]+['global_affine_'+x for x in names]+['residual_'+x for x in names]+['predicted_a'+str(j) for j in range(7)]+['predicted_jerk'+str(j) for j in range(7)]+['max30','joint_trust','assessment_reached','geometry_assessment_completed']);writer.writerows(rowout)
summary={'schema':'ROOT_ACTUAL_INPUTTRUST_BC_COMPONENT_FILE_ARITHMETIC_V1','source_sha256':SS,'packet_payloads':429,'packet_bytes':sum(x['bytes'] for x in manifest.values()),'input_pins':PINS,'source_Ahead3_exact':True,'profile_ELF_declared':profile['producer'],'local_ELF_bytes_present_verified':False,'recorded_startup_termination_pin_count':inputcount,'recorded_pin_lists_before_after_exact':True,'artifact_receipts_verified':len(receipts),'artifact_receipt_bytes':receipt_fields['output_bytes'],'manifest_execution_permission_false_is_not_no_commit_evidence':True,'actual_dispatch_count':1,'raw_facts':facts,'raw_shapes':[400,200,20],'own_full400_recomputation':True,'first_failure':first,'max30_all400':float(np.max(np.abs(diffs))),'max30_by_component':np.max(np.abs(diffs),axis=0).tolist(),'initial_physical_history_exact_actual_warmup_last_point':True,'all400_physical_a_jerk_record_difference':[prefix_aerr,prefix_jerr],'complete_geometry_points':400,'stored_geometry_sigma_interval_recompute_error_points1to399':geointervalerr,'first_geometry_initial_sigma_not_saved_not_independently_recomputed':True,'full_original_QP_arrays_exact_previousA7':True,'full_original_SI':{'rows':13156,'max_independent':float(vios.max()),'max_recorded':float(rowv.max()),'row_error':maxabs(vios-rowv)},'native_SOLVED':{'status':cf[3],'raw_status':cf[4],'api_error':cf[5],'iterations':cf[6],'setup':metric[3],'solve':metric[4]},'new_guard':{'rows':140,'all6351_scaled_arrays_exact_pure_hint_inputs':True,'solver_caps':caps,'alpha_max':maxabs(U.reshape(20,8)[:,:7]),'internal_label':guardlabel,'backend_mapped_original_row':mappedrow,'actual_guess_and_seed_byte_matches_closed_pure_result':True},'actual_C':{'attempts':2,'returns':2,'history_before':cbefore,'history_after':cafter,'held_C':held.tolist(),'times':[cp['time'] for cp in commitpoints],'actual_derivatives_exact':True,'value_actual_qv_maxdiff':actualmodelerror,'interval_arithmetic_error':actualintervalerror,'journal_events':8,'last_physical_history_matches_after_snapshot':True},'strict_actual_input_history':{'cycles':strict_tick,'failures':len(strict_fail),'exact_beta_s_r_b_zero':True,'final_w_maxabs':maxabs(sw)},'exact_tail':exacttail,'coincident_branch_neighborhood':neighbor,'branch_causality_claim':False,'completion':{'stage':stage,'error':error,'wall':wall,'boundary_unchanged':same,'termination_session':sessionpass,'termination_sim':simpass,'physical_steps':steps,'C_commits':commits},'no_new_Model_native_solver_calls':True,'accepted_tick_count':1,'actual_task_substeps':2,'phase5':'NOT_ACCEPTED'}
for path,v in list(PINS.items()):b=Path(path).read_bytes();assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==SS
(OUT/'SOURCE_SNAPSHOT.py').write_bytes(Path(__file__).read_bytes());(OUT/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ['input_pins','coincident_branch_neighborhood']},indent=2))

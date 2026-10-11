"""Independent task-start saved-file algebra; no native/model/SciPy solve."""
import hashlib,json,struct,csv,math,time
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent;PACK=Path('/private/tmp/phase5_task_start_a_checkpoint_v1_20261010');ORACLE=Path('/private/tmp/phase5_task_start_oracle_checkpoint_v2_20261010')
SS=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();pins={};start=time.monotonic()
def pin(path,expected=None):
 b=path.read_bytes();h=hashlib.sha256(b).hexdigest()
 if expected:assert h==expected,(str(path),h,expected)
 pins[str(path)]={'bytes':len(b),'sha256':h};return b
rb=pin(PACK/'READY.json','17d59d457b1ba039141883a211e5259717a012f6dd8a48c5b81f892e5dbef3b6');manifest=json.loads(rb)['files'];assert len(manifest)==223 and sum(x['bytes'] for x in manifest.values())==77710253
for name,v in manifest.items():b=pin(PACK/name,v['sha256']);assert len(b)==v['bytes']
ob=pin(ORACLE/'READY.json','337fb7eb6d282b9e6a4c33b4bbed9be8ee1b259de18e19ddd333abe39dc60fc7');om=json.loads(ob)['files'];assert len(om)==26
for name,v in om.items():b=pin(ORACLE/name,v['sha256']);assert len(b)==v['bytes']
sm=json.loads(pin(OUT/'SOURCE_READ_MANIFEST.json'))
for name,v in sm.items():pin(OUT/'source-read-snapshot'/name,v['sha256'])
BASE=PACK/'actual-dell/repair2/run-attempt1/artifacts'
profile=json.loads((PACK/'actual-dell/repair2/profile-version1/active_input.json').read_text())
class Reader:
 def __init__(self,b,role):
  self.b=b;self.i=0;assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1';assert self.text()==role
 def u(self):
  assert self.i+8<=len(self.b);v=struct.unpack_from('<Q',self.b,self.i)[0];self.i+=8;return v
 def signed(self):
  v=self.u();return v-(1<<64) if v>=(1<<63) else v
 def d(self):
  assert self.i+8<=len(self.b);v=struct.unpack_from('<d',self.b,self.i)[0];self.i+=8;return v
 def text(self):
  n=self.u();assert n<=len(self.b)-self.i;v=self.b[self.i:self.i+n].decode();self.i+=n;return v
 def nums(self,n):
  assert n<=10_000_000 and self.i+8*n<=len(self.b)
  v=np.frombuffer(self.b,dtype='<f8',count=n,offset=self.i).copy();self.i+=8*n;return v
 def vec(self):return self.nums(self.u())
 def mat(self):r,c=self.u(),self.u();return self.nums(r*c).reshape(r,c)
 def ids(self):return [self.u() for _ in range(self.u())]
 def end(self):assert self.i==len(self.b),(self.i,len(self.b))
def inline(b):
 r=Reader(b,'INLINE_QP_COMPLETE_OR_RETAINED_PREFIX');stage,error=r.text(),r.text();info=[r.u() for _ in range(7)];r.text();r.u()
 for _ in range(3):r.d()
 r.u();H,g,A,l,u=r.mat(),r.vec(),r.mat(),r.vec(),r.vec();r.d();F,f,seed=r.mat(),r.vec(),r.vec();k=r.d();labels=[(r.text(),r.text()) for _ in range(r.u())]
 assert H.shape==(160,160) and A.shape==(13156,160) and F.shape==(741,160) and len(labels)==13156
 assert all(np.isfinite(x).all() for x in [H,g,A,l,u,F,f,seed]) and np.isfinite(k)
 return H,g,A,l,u,F,f,seed,k,labels,info
H,g,A,lower,upper,F,f,seed,constant,labels,info=inline(pin(BASE/'inline_qp.bin'))
r=Reader(pin(BASE/'qp_equality_reduction.bin'),'STRUCTURED_ORIGINAL_TERMINAL_EQUALITY_REDUCTION')
policy,stage=r.text(),r.text();valid=r.u();Z,p,E,rhs=r.mat(),r.vec(),r.mat(),r.vec();eq,rows=r.ids(),r.ids()
Hr,gr,Ar,lr,ur,D,Fr,seedr,usablex,usabley,R,Hs,gs,As,ls,us,Fs,seeds=(r.mat(),r.vec(),r.mat(),r.vec(),r.vec(),r.vec(),r.mat(),r.vec(),r.vec(),r.vec(),r.vec(),r.mat(),r.vec(),r.mat(),r.vec(),r.vec(),r.mat(),r.vec())
tag=r.text();wrapper,native,rawstatus,presentx,presenty=[r.u() for _ in range(5)];rawx,rawy=r.vec(),r.vec();slots=r.u();kr,eorigin,emap,efactor,esfactor=[r.d() for _ in range(5)];r.end()
assert valid==wrapper==native==presentx==presenty==1 and rawstatus==7 and rawx.shape==(144,) and rawy.shape==(len(rows),) and usablex.size==usabley.size==0
checks={}
def check(name,a,b,abs_gate=1e-11,rel_gate=1e-10):
 a,b=np.asarray(a),np.asarray(b);assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all(),name
 e=np.abs(a-b);assert np.all(e<=abs_gate+rel_gate*np.maximum(np.abs(a),np.abs(b))),(name,float(e.max()));checks[name]=float(e.max()) if e.size else 0.
check('Hr',Hr,Z.T@H@Z);check('gr',gr,Z.T@(g+H@p));check('Ar',Ar,A[rows]@Z);check('lr',lr,lower[rows]-A[rows]@p);check('ur',ur,upper[rows]-A[rows]@p);check('Fr',Fr,F@Z);check('D',D,1/np.sqrt(np.diag(Hr)));check('R',R,1/np.maximum(1,np.max(np.abs(Ar*D),axis=1)));check('Hs',Hs,D[:,None]*Hr*D);check('gs',gs,D*gr);check('As',As,R[:,None]*Ar*D);check('ls',ls,R*lr);check('us',us,R*ur);check('Fs',Fs,Fr*D);check('seeds',seeds,seedr/D);check('kr',kr,constant+g@p+.5*p@H@p)
def snapshot(name):
 r=Reader(pin(BASE/name),'ACTUAL_NATIVE_SESSION_SNAPSHOT');identities=[r.text(),r.text()];boundary=[r.u(),r.u()];complete=r.u();stage,error=r.text(),r.text();counts=[r.u() for _ in range(3)];t,age=r.d(),r.d();contact=r.u();state=r.nums(30);alpha=r.nums(7);b=r.d();available=r.u();v,a=r.nums(7),r.nums(7);physicalsteps=r.u();source=r.text();before,after=r.vec(),r.vec();r.end()
 assert complete==contact==available==1 and not error and boundary==[0,0] and physicalsteps==1000 and abs(t-2)<1e-10 and np.array_equal(before,after)
 return {'state':state,'alpha':alpha,'b':b,'physicalsteps':physicalsteps,'t':t,'age':age,'v':v,'a':a,'source':source,'integration':before}
obs=snapshot('observation_before.bin');obsafter=snapshot('observation_after.bin');assert np.array_equal(obs['state'],obsafter['state']) and np.array_equal(obs['integration'],obsafter['integration'])
x0=obs['state'];previous_alpha=obs['alpha'];previous_b=obs['b'];mesh=[1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40]
odp=ORACLE/'actual-dell/task-start-linear-oracle-v2-20261010-attempt1/oracle-artifacts-attempt1'
inp=np.load(odp/'ACTUAL_ORACLE_INPUTS.npz',allow_pickle=False);ref=np.load(odp/'FOR_NUMERICAL_REFERENCE_ONLY.npz',allow_pickle=False)
for key,array in {'H':Hs,'g':gs,'A':As,'l':ls,'u':us,'recorded_seed':seeds,'zero_seed':np.zeros(144),'Z':Z,'p':p,'D':D,'R':R,'constant':kr}.items():assert np.array_equal(inp[key],array),(key,'NPZ not exact actual binary value')
xref=ref['solver_x'];Uref=p+Z@(D*xref);assert np.array_equal(ref['reduced_z'],D*xref) and np.array_equal(ref['reconstructed_original_U'],Uref)
guess=json.loads((ORACLE/'actual-dell/task-start-numeric-guess-v1-20261010/guess.json').read_text());assert np.array_equal(np.asarray(guess['solver_coordinates']),xref)
for key,start,end in [('q',0,7),('v',7,14),('C',14,21),('w',21,28)]:assert struct.pack('<7d',*guess[key])==x0[start:end].astype('<f8').tobytes()
assert guess['s']==x0[28] and guess['r']==x0[29] and struct.pack('<7d',*guess['previous_alpha'])==previous_alpha.astype('<f8').tobytes() and guess['previous_b']==previous_b
def diagnostics(U):
 ax=A@U;v=np.maximum(np.maximum(lower-ax,ax-upper),0);worst=int(v.argmax());C=x0[14:21].copy();w=x0[21:28].copy();s,pr=x0[28:];previous=previous_alpha.copy();pb=previous_b;h=.004;events=[];maxjerk=0.;clock=0
 for cell,m in enumerate(mesh):
  os,orr=s,pr;a=U[cell*8:cell*8+7];b=U[cell*8+7]
  for t in range(m):
   clock+=1;nw=w+h*a;nC=C+h*nw;implied=(nw-w)/h;jerk=(implied-previous)/h;maxjerk=max(maxjerk,float(np.max(np.abs(jerk))))
   for j in range(7):
    for label,value,cap in [('alpha',abs(a[j]),1),('implied_alpha',abs(implied[j]),1),('command_jerk',abs(jerk[j]),20),('command_speed',abs(nw[j]),.0625)]:
     if value>cap:events.append({'kind':label,'cell':cell,'tick':clock,'joint':j,'excess':float(value-cap)})
   if abs(b)>.5 or abs((b-pb)/h)>5:events.append({'kind':'b_or_progress_jerk','cell':cell,'tick':clock})
   for half in [1,2]:
    dt=h*t+.002*half;ss=os+dt*orr+.5*dt*dt*b;rr=orr+dt*b
    if not(0<=ss<=1 and 0<=rr<=.2):events.append({'kind':'half_progress_domain','cell':cell,'tick':clock,'half':half,'s':float(ss),'r':float(rr)})
   ns=s+h*pr+.5*h*h*b;nr=pr+h*b
   if not(0<=ns<=1 and 0<=nr<=.2):events.append({'kind':'recursive_progress_domain','cell':cell,'tick':clock,'s':float(ns),'r':float(nr)})
   C,w,s,pr,previous,pb=nC,nw,ns,nr,implied,b
 return {'maximum_original_SI_violation':float(v[worst]),'worst_row':worst,'worst_label':labels[worst][0],'worst_units':labels[worst][1],'rows_above_1e_7':int(np.sum(v>1e-7)),'terminal_affine_residual':float(np.max(np.abs(E@U-rhs))),'literal_history_failures':events,'literal_max_command_jerk':maxjerk,'literal_final_w':w.tolist(),'literal_final_r':float(pr),'last_alpha':U[-8:-1].tolist(),'last_b':float(U[-1]),'exact_zero_tail':bool(np.all(w==0) and pr==0 and np.all(U[-8:]==0)),'cycles':clock,'literal_C':C.tolist()}
forensicdiag=diagnostics(p+Z@(D*rawx));refdiag=diagnostics(Uref)
quick={'scope':'EXTERNAL_SLSQP_REFERENCE_ONLY_NOT_NATIVE_SOLVED_OR_CANDIDATE','forensic':forensicdiag,'external_reference':refdiag,'guess_state_history_bitwise_match_actual_A2':True,'oracle_inputs_exact_actual_A2':True}
(OUT/'quick_oracle_postgate.json').write_text(json.dumps(quick,indent=2,allow_nan=False)+'\n')
print('quick_reference',json.dumps({k:v for k,v in refdiag.items() if k!='literal_history_failures'}));print('reference_history_failure_count',len(refdiag['literal_history_failures']));print('reference_first_history_failure',refdiag['literal_history_failures'][:1])

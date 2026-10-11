"""Actual A7 exact-beta0 subset and strict history file arithmetic; no native/model/solver."""
import json,hashlib,struct,re
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent;PACK=Path('/private/tmp/phase5_task_start_stabilization_checkpoint_v2_20261010');A2=Path('/private/tmp/phase5_task_start_a_checkpoint_v1_20261010')
SS=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();pins={}
def pin(p,expected=None):
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
 if expected:assert h==expected,(str(p),h,expected)
 pins[str(p)]={'bytes':len(b),'sha256':h};return b
rb=pin(PACK/'READY.json','5146ccede2eef1edeac17d1b7c3674675a2c3065633cafa0ca349497b7667294');manifest=json.loads(rb)['files'];assert len(manifest)==149
for n,v in manifest.items():b=pin(PACK/n,v['sha256']);assert len(b)==v['bytes']
oldm=json.loads(pin(A2/'READY.json','17d59d457b1ba039141883a211e5259717a012f6dd8a48c5b81f892e5dbef3b6'))['files']
for n,v in oldm.items():
 if n.endswith(('inline_qp.bin','qp_equality_reduction.bin','observation_before.bin','original_nominal.bin','actual_warmup.bin','actual_step_journal.csv')):pin(A2/n,v['sha256'])
sm=json.loads(pin(OUT/'SOURCE_READ_MANIFEST.json'))['files']
for n,v in sm.items():pin(OUT/'source-read-snapshot'/n,v['sha256'])
BASE=PACK/'actual-dell/session-task-start-stabilization-v2-20261010-attempt7/run-attempt1/artifacts';OLD_BASE=A2/'actual-dell/repair2/run-attempt1/artifacts'
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
def reduction(b):
 r=Reader(b,'STRUCTURED_ORIGINAL_TERMINAL_EQUALITY_REDUCTION');result={'policy':r.text(),'stage':r.text(),'valid':r.u()}
 for name,fn in [('Z',r.mat),('p',r.vec),('E',r.mat),('rhs',r.vec),('eq',r.ids),('rows',r.ids),('Hr',r.mat),('gr',r.vec),('Ar',r.mat),('lr',r.vec),('ur',r.vec),('D',r.vec),('Fr',r.mat),('seed',r.vec),('usablex',r.vec),('usabley',r.vec),('R',r.vec),('Hs',r.mat),('gs',r.vec),('As',r.mat),('ls',r.vec),('us',r.vec),('Fs',r.mat),('solver_seed',r.vec)]:result[name]=fn()
 result['tag']=r.text();result['forensic_flags']=[r.u() for _ in range(5)];result['rawx'],result['rawy']=r.vec(),r.vec();result['slots']=r.u();result['certificates']=[r.d() for _ in range(5)];r.end();return result
def snapshot(b):
 r=Reader(b,'ACTUAL_NATIVE_SESSION_SNAPSHOT');r.text();r.text();boundary=[r.u(),r.u()];complete=r.u();r.text();error=r.text();counts=[r.u() for _ in range(3)];time,age=r.d(),r.d();contact=r.u();state=r.nums(30);alpha=r.nums(7);b=r.d();available=r.u();v,a=r.nums(7),r.nums(7);physical=r.u();source=r.text();ib,ia=r.vec(),r.vec();r.end();assert complete==available==contact==1 and not error and np.array_equal(ib,ia)
 return state,alpha,b,boundary,time,physical,v,a,ib
def nominal_result_suffix(b):
 r=Reader(b,'ORIGINAL_GENUINE_NOMINAL_BEFORE_ADAPTER');[r.text() for _ in range(5)]
 def identity():r.text();r.text();r.u()
 for _ in range(4):identity()
 r.text()
 for _ in range(r.u()):identity()
 for _ in range(r.u()):identity()
 r.text();r.u();r.u()
 for _ in range(2):[r.text() for _ in range(r.u())]
 for _ in range(4):[r.u() for _ in range(r.u())]
 for _ in range(6):r.vec()
 r.nums(30);r.nums(7);r.d();r.u();[r.u() for _ in range(r.u())]
 for _ in range(r.u()):r.u();r.vec();r.d()
 return b[r.i:]
newinline=inline(pin(BASE/'inline_qp.bin'));oldinline=inline((OLD_BASE/'inline_qp.bin').read_bytes())
for i in range(8):assert np.array_equal(newinline[i],oldinline[i])
assert newinline[8:]==oldinline[8:]
red=reduction(pin(BASE/'qp_equality_reduction.bin'));oldred=reduction((OLD_BASE/'qp_equality_reduction.bin').read_bytes())
cols=np.array([k*8+j for k in range(18) for j in range(7)])
for key in ['p','E','rhs','eq','rows','lr','ur','R']:assert np.array_equal(red[key],oldred[key]),key
for key in ['Z','Ar','Fr','As','Fs']:assert np.array_equal(red[key],oldred[key][:,cols]),key
for key in ['gr','D','seed','gs']:assert np.array_equal(red[key],oldred[key][cols]),key
for key in ['Hr','Hs']:assert np.array_equal(red[key],oldred[key][np.ix_(cols,cols)]),key
assert red['Z'].shape==(160,126) and red['rawx'].shape==(126,) and red['usablex'].shape==red['usabley'].shape==(126,)
assert np.array_equal(red['Z'][7::8],np.zeros((20,126))) and np.array_equal(red['p'][7::8],np.zeros(20))
assert red['forensic_flags']==[1,1,1,1,1] and red['usablex'].shape==red['usabley'].shape==(126,)
assert np.array_equal(red['usablex'],red['rawx'])
obs=snapshot(pin(BASE/'observation_before.bin'));after=snapshot(pin(BASE/'observation_after.bin'));oldobs=snapshot((OLD_BASE/'observation_before.bin').read_bytes())
for i in range(len(obs)):assert np.array_equal(obs[i],oldobs[i]) and np.array_equal(obs[i],after[i])
for name in ['actual_warmup.bin','actual_step_journal.csv']:assert pin(BASE/name)==(OLD_BASE/name).read_bytes()
assert nominal_result_suffix(pin(BASE/'original_nominal.bin'))==nominal_result_suffix((OLD_BASE/'original_nominal.bin').read_bytes())
H,g,A,l,u,F,f,seed,k,labels,_=newinline;profile=json.loads(next(PACK.glob('actual-dell/*attempt7/profile-version1/active_input.json')).read_text())
r=Reader(pin(BASE/'external_numeric_guess.bin'),'STABILIZATION_B_ZERO_PRIMAL_DUAL_GUESS_V1_NOT_CANDIDATE');gpath,gsha,origdig,scaledig=[r.text() for _ in range(4)];subsettag=r.text();gx,gy=r.vec(),r.vec();gstate=r.nums(30);ga=r.nums(7);gb=r.d();r.end()
assert gpath==profile['numeric_guess']['path'] and gsha==profile['numeric_guess']['sha256'] and any(x==profile['numeric_guess'] for x in profile['dependencies'])
assert gx.shape==(126,) and gy.shape==(6211,) and np.isfinite(gx).all() and np.isfinite(gy).all() and np.array_equal(gx,red['solver_seed'])
assert gstate.astype('<f8').tobytes()==obs[0].astype('<f8').tobytes() and ga.astype('<f8').tobytes()==obs[1].astype('<f8').tobytes() and struct.pack('<d',gb)==struct.pack('<d',obs[2])
def digest(arrays,c=None):
 h=hashlib.sha256()
 for a in arrays:
  for n in a.shape:h.update(struct.pack('<Q',n))
  h.update(np.asarray(a,dtype='<f8').tobytes(order='C'))
 if c is not None:h.update(struct.pack('<d',c))
 return h.hexdigest()
assert origdig==digest([H,g,A,l,u,F,f],k) and scaledig==digest([red[x] for x in ['Hs','gs','As','ls','us']])
# KKT arithmetic of the recorded seed, not proof of how the seed was generated.
gax=red['As']@gx;gstation=red['Hs']@gx+red['gs']+red['As'].T@gy;gbox=np.maximum(np.maximum(red['ls']-gax,gax-red['us']),0)
gcp=np.maximum(gy,0)*(red['us']-gax)+np.maximum(-gy,0)*(gax-red['ls'])
r=Reader(pin(BASE/'candidate.bin'),'SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');stop=r.text();ci=[r.u() for _ in range(7)];backendworst=r.signed();U=r.vec();cf=[r.d() for _ in range(14)];reuse=[r.u() for _ in range(4)];reset=r.text();counts=[r.u() for _ in range(4)];rowviol=r.vec();mode=r.u();timings=[r.d() for _ in range(4)];flags=[r.u() for _ in range(2)];preview=r.u();previewdata=None
if preview:
 previewdata={key:r.nums(7).tolist() for key in ['C_next','w_next','alpha','implied_alpha','command_jerk']}
 previewdata.update({key:r.d() for key in ['s_next','r_next','b','progress_jerk']});previewdata['half_s']=r.nums(2).tolist();previewdata['half_r']=r.nums(2).tolist();previewdata['boundary']=[r.u(),r.u()]
tail=r.u();taildata=None
if tail:taildata={'w':r.nums(7).tolist(),'alpha':r.nums(7).tolist(),'r':r.d(),'b':r.d(),'exact':r.u()}
request=r.u();requestdata=None
if request:
 requestdata={'initial':r.nums(30).tolist(),'boundary':[r.u(),r.u()],'identities':[r.text(),r.text(),r.text()],'cycles':[r.u() for _ in range(20)],'controls':[]}
 for _ in range(r.u()):requestdata['controls'].append(r.nums(8).tolist())
r.end()
assert ci[:3]==[0,1,1] and ci[4:]==[1,0,1] and U.shape==(160,) and rowviol.shape==(13156,) and preview==1 and tail==request==1 and cf[9:12]==[1e-9,1e-9,.1]
assert np.max(np.abs(U-(red['p']+red['Z']@(red['D']*red['usablex']))))<1e-14
ax=A@U;vio=np.maximum(np.maximum(l-ax,ax-u),0);vi=int(vio.argmax());voldiff=float(np.max(np.abs(vio-rowviol)));assert voldiff<1e-11 and vio.max()<=1e-7
# Exact literal strict path, initialized with REAL accepted histories.
x0,previous,priorb=obs[:3];C=x0[14:21].copy();w=x0[21:28].copy();s,pr=x0[28:];previous=previous.copy();pb=priorb;h=.004;mesh=[1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40];events=[];tick=0;labelidx={x[0]:i for i,x in enumerate(labels)}
for cell,n in enumerate(mesh):
 os,orr=s,pr;alpha=U[cell*8:cell*8+7];b=U[cell*8+7]
 for t in range(n):
  tick+=1;nw=w+h*alpha;nC=C+h*nw;implied=(nw-w)/h;jerk=(implied-previous)/h
  for j in range(7):
   for kind,value,cap in [('alpha',abs(alpha[j]),1),('implied_alpha',abs(implied[j]),1),('command_jerk',abs(jerk[j]),20),('speed',abs(nw[j]),.0625)]:
    if value>cap:events.append({'kind':kind,'tick':tick,'joint':j,'value':float(value),'cap':cap})
   ix=labelidx[f'command/C/tick/{tick}/{j}'];offset=x0[14+j]+tick*h*x0[21+j]
   if nC[j]<l[ix]+offset or nC[j]>u[ix]+offset:events.append({'kind':'C_position','tick':tick,'joint':j})
  progressjerk=(b-pb)/h
  if abs(b)>.5 or abs(progressjerk)>5:events.append({'kind':'b_or_progress_jerk','tick':tick,'cell':cell,'b':float(b),'previous_b':float(pb),'progress_jerk':float(progressjerk),'cap':5})
  for half in [1,2]:
   dt=h*t+.002*half;ss=os+dt*orr+.5*dt*dt*b;rr=orr+dt*b
   if not(0<=ss<=1 and 0<=rr<=.2):events.append({'kind':'half_progress','tick':tick,'half':half,'s':float(ss),'r':float(rr)})
  ns=s+h*pr+.5*h*h*b;nr=pr+h*b
  if not(0<=ns<=1 and 0<=nr<=.2):events.append({'kind':'recursive_progress','tick':tick,'s':float(ns),'r':float(nr)})
  C,w,s,pr,previous,pb=nC,nw,ns,nr,implied,b
assert events==[] and np.array_equal(U[7::8],np.zeros(20)) and s==pr==priorb==0 and tick==200
assert stop=='CANDIDATE_FORWARD_REQUIRED_NO_EXECUTION_PERMISSION'
def function(s,needle):
 i=s.index(needle);masked=re.sub(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"',lambda m:' '*len(m.group()),s,flags=re.S);a=masked.index('{',i);depth=0
 for j in range(a,len(s)):
  depth+=int(masked[j]=='{')-int(masked[j]=='}')
  if depth==0:return s[i:j+1]
oldpath=Path('/private/tmp/root_independent_task_start_a_primaldual_review_20261010/source-read-snapshot');oldcore=(oldpath/'integrated_horizon_qp.cpp').read_text();newcore=(OUT/'source-read-snapshot/integrated_horizon_qp.cpp').read_text();oldbackend=(oldpath/'solver_forensics.cpp').read_text();newbackend=(OUT/'source-read-snapshot/solver_forensics.cpp').read_text()
for name in ['void solveOnce(','void solveOnceWithNumericGuess(','void solveOnceWithPrimalDualNumericGuess(']:assert function(oldcore,name)==function(newcore,name)
for name in ['QpResult solveQpImpl(','QpResult solveCertified(']:assert function(oldbackend,name)==function(newbackend,name)
before=pin(next(PACK.glob('actual-dell/*attempt7/run-attempt1/BEFORE_INPUT_IDENTITIES.json')));afterpins=pin(next(PACK.glob('actual-dell/*attempt7/run-attempt1/AFTER_INPUT_IDENTITIES.json')));assert before==afterpins
r=Reader(pin(BASE/'entry_completion.bin'),'ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING');stage,error=r.text(),r.text();same,session=r.u(),r.u();se=r.text();native=r.u();ne=r.text();wall=r.d();steps,commits=r.u(),r.u();r.end();assert same==session==native==1 and steps==1000 and commits==0 and error==""
assert profile['numeric_guess']['bytes']<=512*1024 and obs[0][28]==obs[0][29]==obs[2]==0
assert requestdata['initial']==obs[0].tolist() and requestdata['boundary']==[0,0] and requestdata['cycles']==mesh and np.array_equal(requestdata['controls'],U.reshape(20,8))
assert np.array_equal(taildata['w'],w) and taildata['r']==pr==0 and taildata['b']==0 and taildata['alpha']==[0]*7
summary={'scope':'ACTUAL_A7_EXACT_BETA0_STABILIZATION_COMPONENT_ONLY_NO_PROGRESS_TASK_OPTIMALITY_CLAIM','source_sha256':SS,'input_pins':pins,'packet_files':len(manifest),'packet_bytes':sum(v['bytes'] for v in manifest.values()),'source_files':len(sm),'original_full_H_g_F_f_c_A_l_u_E_exact_A2':True,'actual_history_and_nominal_maps_warmup_exact_A2':True,'beta0_subspace':{'dimension':126,'selected_original144_columns':cols.tolist(),'Z_shape':list(red['Z'].shape),'all20_beta_offset_and_rows_exact_zero':True,'initial_s_r_previous_b_exact_zero':True,'full144_optimality_NOT_claimed':True,'inherited144_D_R_then_column_subset_exact':True},'recorded_external_guess':{'primal_shape':list(gx.shape),'dual_shape':list(gy.shape),'file_bytes':profile['numeric_guess']['bytes'],'declared_hash':gsha,'finite_and_actual_state_history_bitwise_bound':True,'original_and_scaled_digests':[origdig,scaledig],'source_fullguess_derivation_not_in_packet':True},'loader_source':{'512KiB_preparse_cap':True,'O_NOFOLLOW_opened_regular_fd_exact_size':True,'parsed_exact_bounded_read_EOF_SHA_bytes':True,'seven_history_shape_checks':True,'no_hostile_yaml_or_fault_injection_tested':True},'actual_native':{'status':ci[3],'raw_status':ci[4],'api_error':ci[5],'iterations':ci[6],'polish':counts[3],'setup':cf[3],'solve':cf[4],'primal':cf[1],'dual':cf[2],'numerical_U_count':len(U)},'full_original_SI':{'scanned':len(rowviol),'recorded_max':float(rowviol.max()),'independent_max':float(vio.max()),'row_vector_error':voldiff,'passed1e_7':True},'strict_history':{'200cycles':tick,'failure_count':len(events),'all_beta_s_r_b_jerk_exact_zero':True,'final_w':w.tolist(),'tail_exact_zero_flag':taildata['exact'],'infinite_hold_NOT_certified':True},'data_only_request':{'present':request,'full20cell_controls_match_U':True,'no_execution_permission':ci[0]==0,'no_nonlinear_B_call':True,'no_commit':commits==0,'first_preview':previewdata,'tail':taildata},'legacy_functions_preserved':True,'runtime_pin_before_after_exact':True,'warmup_steps':steps,'task_commits':commits,'stop':stop,'firstcause_history_A6_retained_in_packet':True,'new_model_native_solver_calls':0,'phase5':'NOT_ACCEPTED'}
for path,v in pins.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==v['sha256']
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==SS
(OUT/'results.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ('input_pins','data_only_request','beta0_subspace')},indent=2))

"""A3 saved primal-warm attempt compared with immutable A2 proof; no solve/model."""
import hashlib,json,struct,time
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent;PACK=Path('/private/tmp/phase5_task_start_a_warm_checkpoint_v1_20261010');OLD=Path('/private/tmp/phase5_task_start_a_checkpoint_v1_20261010');ORACLE=Path('/private/tmp/phase5_task_start_oracle_checkpoint_v2_20261010')
SS=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();pins={}
def pin(path,expected=None):
 b=path.read_bytes();h=hashlib.sha256(b).hexdigest()
 if expected:assert h==expected,(str(path),h,expected)
 pins[str(path)]={'bytes':len(b),'sha256':h};return b
ready=pin(PACK/'READY.json','2ea0ba48063e6e3999fa906d87ddc3f36ee855a6a681b4501770674db410a3e6');m=json.loads(ready)['files'];assert len(m)==128 and sum(v['bytes'] for v in m.values())==72084442
for name,v in m.items():b=pin(PACK/name,v['sha256']);assert len(b)==v['bytes']
oldready=pin(OLD/'READY.json','17d59d457b1ba039141883a211e5259717a012f6dd8a48c5b81f892e5dbef3b6');oldm=json.loads(oldready)['files']
BASE=PACK/'actual-dell/session-task-start-a-warm-v1-20261010-attempt3/run-attempt1/artifacts';OLD_BASE=OLD/'actual-dell/repair2/run-attempt1/artifacts'
for n in ['inline_qp.bin','qp_equality_reduction.bin','original_nominal.bin','actual_warmup.bin','actual_step_journal.csv','observation_before.bin']:
 rel='actual-dell/repair2/run-attempt1/artifacts/'+n;pin(OLD/rel,oldm[rel]['sha256'])
sm=json.loads(pin(OUT/'SOURCE_READ_MANIFEST.json'))
for name,v in sm.items():pin(OUT/'source-read-snapshot'/name,v['sha256'])
priorproof=Path('/private/tmp/root_independent_task_start_a_review_20261010');pready=pin(priorproof/'READY.json','a7cecbf2181485032cbf52af5090ce6be7321a7742d4219923a93add8068b099');pr=json.loads(pready)['files'];pin(priorproof/'results.json',pr['results.json']['sha256']);prior=json.loads((priorproof/'results.json').read_text())
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
newinline=inline(pin(BASE/'inline_qp.bin'));oldinline=inline((OLD_BASE/'inline_qp.bin').read_bytes())
for i in range(8):assert np.array_equal(newinline[i],oldinline[i])
assert newinline[8:]==oldinline[8:]
red=reduction(pin(BASE/'qp_equality_reduction.bin'));oldred=reduction((OLD_BASE/'qp_equality_reduction.bin').read_bytes())
for key in ['Z','p','E','rhs','eq','rows','Hr','gr','Ar','lr','ur','D','Fr','seed','R','Hs','gs','As','ls','us','Fs','certificates']:assert np.array_equal(red[key],oldred[key]),key
assert red['usablex'].size==red['usabley'].size==0 and red['forensic_flags']==[1,1,7,1,1]
assert pin(BASE/'actual_warmup.bin')==(OLD_BASE/'actual_warmup.bin').read_bytes() and pin(BASE/'actual_step_journal.csv')==(OLD_BASE/'actual_step_journal.csv').read_bytes()
def snapshot(b):
 r=Reader(b,'ACTUAL_NATIVE_SESSION_SNAPSHOT');r.text();r.text();boundary=[r.u(),r.u()];complete=r.u();r.text();error=r.text();counts=[r.u() for _ in range(3)];time,age=r.d(),r.d();contact=r.u();state=r.nums(30);alpha=r.nums(7);b=r.d();available=r.u();v,a=r.nums(7),r.nums(7);physical=r.u();source=r.text();ib,ia=r.vec(),r.vec();r.end();assert complete==available==contact==1 and not error and np.array_equal(ib,ia)
 return state,alpha,b,boundary,time,physical,v,a,ib
obs=snapshot(pin(BASE/'observation_before.bin'));obs2=snapshot((OLD_BASE/'observation_before.bin').read_bytes());after=snapshot(pin(BASE/'observation_after.bin'))
for i in range(len(obs)):assert np.array_equal(obs[i],obs2[i]) and np.array_equal(obs[i],after[i]),i
assert obs[3]==[0,0] and obs[5]==1000
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
assert nominal_result_suffix(pin(BASE/'original_nominal.bin'))==nominal_result_suffix((OLD_BASE/'original_nominal.bin').read_bytes())
H,g,A,l,u,F,f,seed,k,labels,_=newinline
oready=pin(ORACLE/'READY.json','337fb7eb6d282b9e6a4c33b4bbed9be8ee1b259de18e19ddd333abe39dc60fc7');om=json.loads(oready)['files'];grel='actual-dell/task-start-numeric-guess-v1-20261010/guess.json';guessbytes=pin(ORACLE/grel,om[grel]['sha256']);guess=json.loads(guessbytes)
profile=json.loads(next(PACK.glob('actual-dell/*/profile-version1/active_input.json')).read_text());assert profile['numeric_guess']['bytes']==len(guessbytes) and profile['numeric_guess']['sha256']==hashlib.sha256(guessbytes).hexdigest()
assert any(x==profile['numeric_guess'] for x in profile['dependencies'])
r=Reader(pin(BASE/'external_numeric_guess.bin'),'EXTERNAL_ALGEBRA_OPTIMIZER_GUESS_NOT_CANDIDATE');gpath,gsha,original_digest,scaled_digest=[r.text() for _ in range(4)];gx=r.vec();gstate=r.nums(30);galpha=r.nums(7);gb=r.d();r.end()
assert gpath==profile['numeric_guess']['path'] and gsha==profile['numeric_guess']['sha256'] and np.array_equal(gx,guess['solver_coordinates']) and np.array_equal(gx,red['solver_seed']) and gx.shape==(144,) and np.isfinite(gx).all()
assert np.array_equal(gstate,obs[0]) and np.array_equal(galpha,obs[1]) and gb==obs[2]
assert gstate.astype('<f8').tobytes()==struct.pack('<30d',*(guess['q']+guess['v']+guess['C']+guess['w']+[guess['s'],guess['r']]))
def digest(arrays,c=None):
 h=hashlib.sha256()
 for a in arrays:
  for n in a.shape:h.update(struct.pack('<Q',n))
  h.update(np.asarray(a,dtype='<f8').tobytes(order='C'))
 if c is not None:h.update(struct.pack('<d',c))
 return h.hexdigest()
assert original_digest==guess['original_problem_sha256']==digest([H,g,A,l,u,F,f],k)
assert scaled_digest==guess['transformed_problem_sha256']==digest([red[x] for x in ['Hs','gs','As','ls','us']])
r=Reader(pin(BASE/'candidate.bin'),'SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');stop=r.text();ci=[r.u() for _ in range(7)];worst=r.signed();usable=r.vec();cf=[r.d() for _ in range(14)];reuse=[r.u() for _ in range(4)];reset=r.text();counts=[r.u() for _ in range(4)];rowviol=r.vec();mode=r.u();timings=[r.d() for _ in range(4)];flags=[r.u() for _ in range(2)];preview,tail,request=r.u(),r.u(),r.u();r.end()
assert ci==[0,1,1,6,7,0,20000] and usable.size==rowviol.size==0 and preview==tail==request==0 and worst==-1 and cf[9:12]==[1e-9,1e-9,.1]
r=Reader(pin(BASE/'entry_completion.bin'),'ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING');finishstage,finisherror=r.text(),r.text();same,session=r.u(),r.u();session_error=r.text();native=r.u();native_error=r.text();wall=r.d();steps,commits=r.u(),r.u();r.end();assert same==session==native==1 and steps==1000 and commits==0
oldcpp=(Path('/private/tmp/root_independent_task_start_a_review_20261010/source-read-snapshot')/'integrated_horizon_qp.cpp').read_text();newcpp=(OUT/'source-read-snapshot/integrated_horizon_qp.cpp').read_text();oldbody=oldcpp[oldcpp.index('void solveOnce('):oldcpp.index('Eigen::VectorXd shiftControlGuess')].strip();assert newcpp[newcpp.index('void solveOnce('):].startswith(oldbody)
oldbackend=Path('/private/tmp/root_independent_task_start_a_review_20261010/source-read-snapshot/solver_forensics.cpp').read_bytes();assert oldbackend==(OUT/'source-read-snapshot/solver_forensics.cpp').read_bytes()
before=pin(next(PACK.glob('actual-dell/*/run-attempt1/BEFORE_INPUT_IDENTITIES.json')));afterpins=pin(next(PACK.glob('actual-dell/*/run-attempt1/AFTER_INPUT_IDENTITIES.json')));assert before==afterpins
rawU=red['p']+red['Z']@(red['D']*red['rawx']);ax=A@rawU;vio=np.maximum(np.maximum(l-ax,ax-u),0);vi=int(vio.argmax())
summary={'scope':'ACTUAL_A3_EXTERNAL_PRIMAL_WARM_FAILURE_FILE_AND_SEPARATE_API_REVIEW_ONLY','source_sha256':SS,'input_pins':pins,'packet_files':len(m),'packet_bytes':sum(x['bytes'] for x in m.values()),'source_snapshot_files':len(sm),'legacy_solveOnce_body_byte_preserved':True,'forensic_backend_byte_preserved':True,'new_API':'solveOnceWithNumericGuess','warmup_binary_and_journal_bit_identical_A2':True,'actual_state_history_and_400nominal_map_result_bytes_exact_A2':True,'all_original_and_transformed_array_values_exact_A2_except_solver_seed':True,'guess_file_bytes':len(guessbytes),'finite_shape144_verified':True,'generic_loader_byte_cap_NOT_present':True,'fulloriginal_and_scaled_digests':[original_digest,scaled_digest],'actual_recorded_solver_seed_equals_external_guess':True,'guess_is_not_old_unsolved_iterate':not np.array_equal(gx,oldred['rawx']),'external_reference_strict129FAIL_retained_from_A2':prior['external_reference']['diagnostics'],'runtime_before_after_exact':True,'actual_result':{'status':ci[3],'raw_status':ci[4],'iterations':ci[6],'setup_seconds':cf[3],'solve_seconds':cf[4],'primal_transformed':cf[1],'dual_transformed':cf[2],'rho_updates':counts[2],'rho_estimate':cf[12],'usable_count':len(usable),'original_SI_rows_scanned':len(rowviol),'collector_fullSI':'UNMEASURED','preview':preview,'tail':tail,'request':request,'steps_warmup':steps,'task_commits':commits,'stop':stop},'new_forensic_unusable_only':{'max_original_violation':float(vio[vi]),'row':vi,'label':labels[vi][0],'rows_over1e_7':int(np.sum(vio>1e-7))},'prior_algebra_proof_READY_sha256':'a7cecbf2181485032cbf52af5090ce6be7321a7742d4219923a93add8068b099','no_B_or_new_model_evaluation':True,'native_model_solver_calls':0,'phase5':'NOT_ACCEPTED'}
for path,v in pins.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==v['sha256']
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==SS
(OUT/'results.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ('input_pins','external_reference_strict129FAIL_retained_from_A2')},indent=2))

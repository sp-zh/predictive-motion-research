"""Pure saved warmup file arithmetic. No native/model/kinematics/geometry calls."""
import argparse,csv,hashlib,json,math,struct,time
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--ready-sha',required=True);args=ap.parse_args()
OUT=Path(__file__).resolve().parent;PACK=Path('/private/tmp/phase5_task_warmup_checkpoint_v1_20261010')
SS=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();pins={}
def pin(p,expected=None):
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
 if expected:assert h==expected,(str(p),h,expected)
 pins[str(p)]={'bytes':len(b),'sha256':h};return b
ready=pin(PACK/'READY.json',args.ready_sha);manifest=json.loads(ready)['files']
for name,v in manifest.items():
 b=pin(PACK/name,v['sha256']);assert len(b)==v['bytes']
src=json.loads(pin(OUT/'SOURCE_READ_MANIFEST.json'))['files']
source_match={}
for name,v in src.items():
 pin(OUT/'source-read-snapshot'/name,v['sha256'])
 actual=PACK/'actual-dell/repair2/src'/name
 if actual.exists():source_match[name]=hashlib.sha256(actual.read_bytes()).hexdigest()==v['sha256']
assert all(source_match[n] for n in ['runtime_observer.cpp','runtime_observer.hpp','active_task_warmup.cpp','lossless_evidence.cpp','lossless_evidence.hpp'])
class Reader:
 def __init__(self,b,role):self.b=b;self.i=0;assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1' and self.text()==role
 def u(self):assert self.i+8<=len(self.b);v=struct.unpack_from('<Q',self.b,self.i)[0];self.i+=8;return v
 def d(self):assert self.i+8<=len(self.b);v=struct.unpack_from('<d',self.b,self.i)[0];self.i+=8;return v
 def text(self):n=self.u();assert n<=len(self.b)-self.i;v=self.b[self.i:self.i+n].decode();self.i+=n;return v
 def nums(self,n):return [self.d() for _ in range(n)]
 def vec(self):return self.nums(self.u())
 def end(self):assert self.i==len(self.b),(self.i,len(self.b))
def scalar(s):
 if s in ('true','false'):return s=='true'
 if s.isdecimal():return int(s)
 if s.startswith('"'):return json.loads(s)
 return s
def artifacts(attempt):
 base=PACK/'actual-dell'/attempt/'run-attempt1/artifacts';receipts={};fields={};current=None
 for line in pin(base/'MANIFEST.yaml').decode().splitlines():
  if line=='files:':continue
  if line.startswith('  - file: '):name=scalar(line[len('  - file: '):]);assert name not in receipts;current={};receipts[name]=current
  elif line.startswith('    '):k,v=line[4:].split(': ',1);assert k not in current;current[k]=scalar(v)
  else:k,v=line.split(': ',1);assert k not in fields;fields[k]=scalar(v)
 for n,v in receipts.items():
  assert v['created'] and v['complete'] and v['hash_valid'] and not v['error'];b=pin(base/n,v['sha256']);assert len(b)==v['bytes'];Reader(b,v['role'])
 assert sum(x['bytes'] for x in receipts.values())==fields['output_bytes']
 return base,fields,receipts
base,fields,receipts=artifacts('repair2');oldbase,oldfields,oldreceipts=artifacts('attempt1')
assert fields['schema']=='ACTIVE_SESSION_EVIDENCE_MANIFEST_V1' and fields['execution_permission'] is False
r=Reader(pin(base/'actual_warmup.bin'),'ACTUAL_TASK_INITIALIZATION_AND_PHYSICAL_WARMUP_V1')
entered,assigned,success,seed=[r.u() for _ in range(4)];stage,error=r.text(),r.text();initial=r.nums(7);pe,re=r.d(),r.d();units=r.text();n=r.u();points=[]
assert [entered,assigned,success,seed]==[1,1,1,91011] and not error and n==1000
for _ in range(n):
 p={'substep':r.u(),'time':r.d()}
 for k in ['q','v','C','a','j']:p[k]=r.nums(7)
 for k in ['jerk_available','geometry_complete','observer_guard','contacts']:p[k]=r.u()
 p['warnings']=[r.u() for _ in range(8)];p['true'],p['cover'],p['queries']=r.d(),r.d(),r.u();p['stage'],p['error']=r.text(),r.text();points.append(p)
r.end()
profile=json.loads(pin(PACK/'actual-dell/repair2/profile-version1/input.json'));assert profile['seed']==seed
csvpath=Path('/Users/uot/Documents/ChatGPT/ros/results/cad/path_screening_aabb/feasible_path.csv');csvbytes=pin(csvpath,profile['feasible_csv']['sha256']);values=[float(x) for x in csvbytes.decode().splitlines()[1].split(',')]
# Standard MT19937 initialization/twist/temper implemented independently.
mt=[seed]
for i in range(1,624):mt.append((1812433253*(mt[-1]^(mt[-1]>>30))+i)&0xffffffff)
for i in range(624):
 y=(mt[i]&0x80000000)|(mt[(i+1)%624]&0x7fffffff);mt[i]=mt[(i+397)%624]^(y>>1)^ (0x9908b0df if y&1 else 0)
rngvalues=[]
for a in mt[:7]:
 a^=a>>11;a^=(a<<7)&0x9d2c5680;a^=(a<<15)&0xefc60000;a^=a>>18;rngvalues.append(a&0xffffffff)
initialref=[values[-7+j]+(rngvalues[j]/4294967295.-.5)*.0002 for j in range(7)]
assert initial==initialref
previous=[0.]*7;previousa=None;adiff=jdiff=timediff=0.;maxa=maxj=maxv=0.;allwarnings=0
for i,p in enumerate(points):
 assert p['substep']==i+1 and p['C']==initial and p['geometry_complete']==p['observer_guard']==1 and p['queries']>0 and not p['error']
 assert all(math.isfinite(x) for name in ['q','v','C','a'] for x in p[name]) and math.isfinite(p['true']) and math.isfinite(p['cover'])
 a=[(p['v'][j]-previous[j])/.002 for j in range(7)];adiff=max(adiff,max(abs(a[j]-p['a'][j]) for j in range(7)))
 assert p['jerk_available']==int(i>0)
 if i==0:assert all(math.isnan(x) for x in p['j'])
 else:
  assert all(math.isfinite(x) for x in p['j']);j=[(a[d]-previousa[d])/.002 for d in range(7)];jdiff=max(jdiff,max(abs(j[d]-p['j'][d]) for d in range(7)));maxj=max(maxj,max(abs(x) for x in j))
 previous,previousa=p['v'],a;maxa=max(maxa,max(abs(x) for x in a));maxv=max(maxv,max(abs(x) for x in p['v']));timediff=max(timediff,abs(p['time']-.002*(i+1)));allwarnings=max(allwarnings,max(p['warnings']))
assert adiff==jdiff==0 and timediff<1e-10
last=points[-1];endgate={'elapsed2s':abs(last['time']-2)<=1e-10,'contact0':last['contacts']==0,'true_and_cover_at_least_5mm':min(last['true'],last['cover'])>=.005,'velocity_at_most_1e_4':max(abs(x) for x in last['v'])<=1e-4};assert all(endgate.values())
r=Reader(pin(base/'actual_current.bin'),'ACTUAL_NATIVE_SESSION_SNAPSHOT');identities=[r.text(),r.text()];boundary=[r.u(),r.u()];complete=r.u();ostage,ofail=r.text(),r.text();counts=[r.u() for _ in range(3)];simtime,age=r.d(),r.d();contactfree=r.u();state=r.nums(30);previousalpha=r.nums(7);previousb=r.d();accavailable=r.u();lastv,lasta=r.nums(7),r.nums(7);steps=r.u();physicalsource=r.text();ibefore,iafter=r.vec(),r.vec();r.end()
assert boundary==[0,0] and complete==accavailable==contactfree==1 and not ofail and steps==1000 and simtime==last['time']
assert state[:7]==last['q'] and state[7:14]==last['v'] and state[14:21]==initial and state[21:]==[0.]*9
assert previousalpha==[0.]*7 and previousb==0 and lastv==last['v'] and lasta==last['a'] and ibefore==iafter
r=Reader(pin(base/'warmup_completion.bin'),'ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING');cstage,cerror=r.text(),r.text();csuccess,terminal,attempts,completed,commits,models,nominals=[r.u() for _ in range(7)];scope=r.text();r.end();assert csuccess==terminal==1 and not cerror and attempts==completed==1000 and commits==models==nominals==0
r=Reader(pin(base/'bootstrap.bin'),'ACTUAL_DIRECT_SESSION_API_ENTRIES');bootstrap=[r.u() for _ in range(9)];r.end();assert bootstrap[7:]==[1000,0]
old=Reader(pin(oldbase/'warmup_completion.bin'),'ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING');oldstage,olderror=old.text(),old.text();oldvalues=[old.u() for _ in range(7)];oldscope=old.text();old.end();assert oldvalues[0]==0 and oldvalues[2:]==[0]*5
before=pin(PACK/'actual-dell/repair2/run-attempt1/BEFORE_INPUT_IDENTITIES.json');after=pin(PACK/'actual-dell/repair2/run-attempt1/AFTER_INPUT_IDENTITIES.json');assert before==after
runplan=json.loads(pin(PACK/'actual-dell/repair2/warmup_run_plan.json'));runresult=json.loads(pin(PACK/'actual-dell/repair2/run-attempt1/compile-1.result.json'));assert runresult['exit']==0
assert any(x['requested_path'].endswith('/profile-version1/input.json') and x['sha256']==hashlib.sha256((PACK/'actual-dell/repair2/profile-version1/input.json').read_bytes()).hexdigest() for x in runplan['input_files'])
result={'scope':'ACTUAL_RECORDED_WARMUP_COMPONENT_ONLY_FILE_ARITHMETIC_NOT_TASK_OR_PHASE_ACCEPTANCE','source_sha256':SS,'input_pins':pins,'source_read_matches_actual_core_files':source_match,'seed':seed,'independent_mt19937_first7':rngvalues,'initial_q':initial,'held_accepted_target_verified_all1000':True,'physical_substeps':1000,'task_boundary':boundary,'task_commits':commits,'bootstrap_counters_load_make_reset_forward_copy_getstate_observations_step_commits':bootstrap,'derivatives':{'max_abs_v':maxv,'max_abs_acc':maxa,'max_abs_available_jerk':maxj,'recorded_acc_error':adiff,'recorded_jerk_error':jdiff,'first_acc_available_from_declared_v0':True,'first_jerk_available':False,'first_jerk_NaN_exactly_preserved':True},'clock_max_error':timediff,'endgate':endgate,'final':{'time':last['time'],'max_abs_v':max(abs(x) for x in last['v']),'minimum_true':last['true'],'minimum_cover':last['cover'],'contacts':last['contacts'],'geometry_queries':last['queries'],'position_error_stored_not_recomputed':pe,'rotation_error_stored_not_recomputed':re},'whole_warmup':{'max_warning_count':allwarnings,'max_contacts':max(p['contacts'] for p in points),'minimum_true':min(p['true'] for p in points),'minimum_cover':min(p['cover'] for p in points),'query_counts':sorted(set(p['queries'] for p in points)),'safety_gate_over_all_warmup_NOT_claimed':True},'actual_current_B_history':{'physical_velocity_matches_actual_last_point':True,'physical_acceleration_matches_actual_last_point':True,'physical_source_id':physicalsource,'accepted_w_alpha_progress_zero_are_held_target_history_NOT_measured_velocity':True,'capture_age_recorded':age,'current_online_age_not_proven_by_offline_record':True},'identity_layers':{'run_before_after_exact_equal':True,'run_inputs_count':len(runplan['input_files']),'entry_input_not_internal_dependency_but_runner_pinned':True,'ELF_record_sha':runresult['argv'][3],'local_ELF_bytes_verified':False,'compile_link_empty_identity_arrays_not_buildclosure':True},'preserved_attempt1_failure':{'stage':oldstage,'error':olderror,'completion_fields':oldvalues},'independent_geometry_or_TCP_calls':0,'model_native_solver_calls':0,'phase5':'NOT_ACCEPTED'}
for name,v in pins.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==v['sha256']
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==SS
(OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('input_pins','source_read_matches_actual_core_files')},indent=2))

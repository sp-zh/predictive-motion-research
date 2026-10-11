"""Pure saved warmup file arithmetic. No native/model/kinematics/geometry calls."""
import argparse,csv,hashlib,json,math,struct,time
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--ready-sha',required=True);args=ap.parse_args()
OUT=Path(__file__).resolve().parent;PACK=Path('/private/tmp/phase5_task_warmup_checkpoint_v2_20261010')
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
 actual=PACK/'actual-dell/session-task-warmup-v2-20261010-repair7/src'/name
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
base,fields,receipts=artifacts('session-task-warmup-v2-20261010-repair7')
assert fields['schema']=='ACTIVE_SESSION_EVIDENCE_MANIFEST_V1' and fields['execution_permission'] is False
r=Reader(pin(base/'actual_warmup.bin'),'ACTUAL_TASK_INITIALIZATION_AND_PHYSICAL_WARMUP_V2')
entered,assigned,success,seed=[r.u() for _ in range(4)];stage,error=r.text(),r.text();initial=r.nums(7);pe,re=r.d(),r.d();units=r.text();n=r.u();points=[]
assert [entered,assigned,success,seed]==[1,1,1,91011] and not error and n==1000
for _ in range(n):
 p={'substep':r.u(),'time':r.d(),'native_returned':r.u(),'native_joints':r.u(),'scratch_joints':r.u()}
 for k in ['q','v','C','a','j']:p[k]=r.nums(7)
 for k in ['jerk_available','geometry_complete','observer_guard','contacts']:p[k]=r.u()
 p['warnings']=[r.u() for _ in range(8)];p['true'],p['cover'],p['queries']=r.d(),r.d(),r.u();p['tcp_frame_error'],p['arm_frame_error']=r.d(),r.d();p['stage'],p['error']=r.text(),r.text();points.append(p)
r.end()
assert len((base/'actual_warmup.bin').read_bytes())==504405 and hashlib.sha256((base/'actual_warmup.bin').read_bytes()).hexdigest()=='ddfe59b603e0caa2ef85b0bb3e3e14a75e4f57a639cc22f8bad2fda249802901'
jb=pin(base/'actual_step_journal.csv','eea9da2c74e5b8e20776e7e0df04e8926c9ab278117fcce5c9fb03ac16927313');assert len(jb)==1813021 and jb.endswith(b'\n')
csvrows=list(csv.reader(jb.decode().splitlines()));assert len(csvrows)==3000 and all(len(x)==58 for x in csvrows)
events=['BEFORE_NATIVE_STEP_ATTEMPT','NATIVE_STEP_RETURNED_BEFORE_SCRATCH','COMPLETE_ACTUAL_OBSERVATION_AND_GEOMETRY']
nanaware_error=0.;journal_frame_error=0.;max_line=max(len(x) for x in jb.splitlines(keepends=True));assert max_line<=4096 and len(jb)<=12582912
for i,p in enumerate(points):
 for phase in range(3):
  row=csvrows[3*i+phase];assert row[0]==events[phase] and int(row[1])==p['substep']
  vals=[float(x) for x in row[2:]]
  native_returned,native_read,scratch_read=[int(x) for x in row[3:6]]
  assert [native_returned,native_read,scratch_read]==([0,0,0] if phase==0 else [1,7,0] if phase==1 else [1,7,7])
  assert [int(x) for x in row[50:53]]==([0,0,0] if phase<2 else [p['jerk_available'],1,1])
  assert [float(x) for x in row[29:36]]==p['C']
  if phase==0:
   assert float(row[2])==0 and [float(x) for x in row[15:29]]==[0.]*14
   assert all(math.isnan(float(row[x])) for x in [53,54,56,57])
  else:
   assert float(row[2])==p['time'] and int(row[6])==p['contacts'] and [int(x) for x in row[7:15]]==p['warnings']
   assert [float(x) for x in row[15:22]]==p['q'] and [float(x) for x in row[22:29]]==p['v']
  if phase==2:
   expected=p['a']+p['j']+[float(p['jerk_available']),1.,1.,p['true'],p['cover'],float(p['queries']),p['tcp_frame_error'],p['arm_frame_error']
   actual=[float(x) for x in row[36:]];assert len(actual)==len(expected)
   for a,b in zip(actual,expected):
    if math.isnan(b):assert math.isnan(a)
    else:nanaware_error=max(nanaware_error,abs(a-b));assert a==b
   journal_frame_error=max(journal_frame_error,float(row[56]),float(row[57]))
jr=Reader(pin(base/'journal_receipt.bin'),'ACTUAL_DURABLE_WARMUP_JOURNAL_PREFIX_V2');journalpath,journalsha=jr.text(),jr.text();seen,stored,ack_events,newlines,partial=[jr.u() for _ in range(5)];prefixscope=jr.text();jr.end()
assert journalsha==hashlib.sha256(jb).hexdigest() and seen==stored==len(jb) and ack_events==newlines==3000 and partial==0
journal_results={'bytes':len(jb),'sha256':journalsha,'complete_lines':len(csvrows),'three_event_roster_exact':True,'max_line_bytes_including_newline':max_line,'line_cap':4096,'separate_journal_cap':12582912,'receipt_bytes_seen_and_stored':[seen,stored],'receipt_fsync_ack_events':ack_events,'receipt_newlines':newlines,'receipt_partial_tail':partial,'binary_vs_complete_journal_error_nanaware':nanaware_error,'pending_before_event_fields_not_observations':True,'source_fsync_before_native_step':True,'normal_success_record_NOT_fault_injection_or_powerloss_proof':True,'prefix_scope':prefixscope}
profile=json.loads(pin(PACK/'actual-dell/session-task-warmup-v2-20261010-repair7/profile-version1/input.json'));assert profile['seed']==seed
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
 assert p['native_returned']==1 and p['native_joints']==p['scratch_joints']==7 and math.isfinite(p['tcp_frame_error']) and math.isfinite(p['arm_frame_error']) and max(p['tcp_frame_error'],p['arm_frame_error'])<=1e-8
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
before=pin(PACK/'actual-dell/session-task-warmup-v2-20261010-repair7/run-attempt1/BEFORE_INPUT_IDENTITIES.json');after=pin(PACK/'actual-dell/session-task-warmup-v2-20261010-repair7/run-attempt1/AFTER_INPUT_IDENTITIES.json');assert before==after
runplan=json.loads(pin(PACK/'actual-dell/session-task-warmup-v2-20261010-repair7/warmup_run_plan.json'));runresult=json.loads(pin(PACK/'actual-dell/session-task-warmup-v2-20261010-repair7/run-attempt1/compile-1.result.json'));assert runresult['exit']==0
assert any(x['requested_path'].endswith('/profile-version1/input.json') and x['sha256']==hashlib.sha256((PACK/'actual-dell/session-task-warmup-v2-20261010-repair7/profile-version1/input.json').read_bytes()).hexdigest() for x in runplan['input_files'])
result={'scope':'ACTUAL_RECORDED_WARMUP_COMPONENT_ONLY_FILE_ARITHMETIC_NOT_TASK_OR_PHASE_ACCEPTANCE','source_sha256':SS,'input_pins':pins,'source_read_matches_actual_core_files':source_match,'packet_files_count':len(manifest),'packet_payload_total_bytes':sum(v['bytes'] for v in manifest.values()),'seed':seed,'independent_mt19937_first7':rngvalues,'initial_q':initial,'held_accepted_target_verified_all1000':True,'physical_substeps':1000,'actual_all_points_native_returned_and_read7':all(p['native_returned']==1 and p['native_joints']==p['scratch_joints']==7 for p in points),'max_tcp_frame_error':max(p['tcp_frame_error'] for p in points),'max_arm_frame_error':max(p['arm_frame_error'] for p in points),'journal':journal_results,'task_boundary':boundary,'task_commits':commits,'bootstrap_counters_load_make_reset_forward_copy_getstate_observations_step_commits':bootstrap,'derivatives':{'max_abs_v':maxv,'max_abs_acc':maxa,'max_abs_available_jerk':maxj,'recorded_acc_error':adiff,'recorded_jerk_error':jdiff,'first_acc_available_from_declared_v0':True,'first_jerk_available':False,'first_jerk_NaN_exactly_preserved':True},'clock_max_error':timediff,'endgate':endgate,'final':{'time':last['time'],'max_abs_v':max(abs(x) for x in last['v']),'minimum_true':last['true'],'minimum_cover':last['cover'],'contacts':last['contacts'],'geometry_queries':last['queries'],'position_error_stored_not_recomputed':pe,'rotation_error_stored_not_recomputed':re},'whole_warmup':{'max_warning_count':allwarnings,'max_contacts':max(p['contacts'] for p in points),'minimum_true':min(p['true'] for p in points),'minimum_cover':min(p['cover'] for p in points),'query_counts':sorted(set(p['queries'] for p in points)),'safety_gate_over_all_warmup_NOT_claimed':True},'actual_current_B_history':{'physical_velocity_matches_actual_last_point':True,'physical_acceleration_matches_actual_last_point':True,'physical_source_id':physicalsource,'accepted_w_alpha_progress_zero_are_held_target_history_NOT_measured_velocity':True,'capture_age_recorded':age,'current_online_age_not_proven_by_offline_record':True},'identity_layers':{'run_before_after_exact_equal':True,'run_inputs_count':len(runplan['input_files']),'entry_input_not_internal_dependency_but_runner_pinned':True,'ELF_record_sha':runresult['argv'][3],'local_ELF_bytes_verified':False,'compile_link_empty_identity_arrays_not_buildclosure':True},'independent_geometry_or_TCP_calls':0,'model_native_solver_calls':0,'phase5':'NOT_ACCEPTED'}
for name,v in pins.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==v['sha256']
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==SS
(OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('input_pins','source_read_matches_actual_core_files')},indent=2))

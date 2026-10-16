from pathlib import Path
import os,sys,json,struct,ast,hashlib,collections
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root63_nominal_reader_v4 as nominal
import root64_merged_reader_v4 as merged
strict=nominal.strict
T=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.ClassDef)and x.name=='R'],type_ignores=[]),'<reader>','exec'))
P=Path('/private/tmp/phase5_controlled_stop_roundoff_command_terminal64_v1_20261016');O=Path('/private/tmp/root64_actual_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);M=Path('/private/tmp/phase5_roundoff_command64_source_v1_20261016/full_archive64_v1/readback');archive={e['path']:e for e in json.loads((M/'SOURCE_MANIFEST.json').read_text())['files']};ready=json.loads((P/'READY.json').read_text());assert hashlib.sha256((P/'READY.json').read_bytes()).hexdigest()=='6196da0ddb5e1777f27eb3024dc7496891d730e16c82f1838d9878797f14c66f'and len(ready['payload'])==1154 and sum(e['bytes']for e in ready['payload'])==93512344;receipts=[];bound=0
for e in ready['payload']:
 p=P/e['path'];b=p.read_bytes();assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256']
 if e['path'].startswith('actual-dell/'):
  k='native64/'+str(Path(e['path']).relative_to(Path(*Path(e['path']).parts[:2])));a=archive[k];assert(e['bytes'],e['sha256'])==(a['bytes'],a['sha256']);bound+=1
 if p.suffix=='.bin':receipts.append(strict.verify_artifact(p))
assert len(receipts)==489 and all(e['source_complete']for e in receipts)
B=next(P.glob('actual-dell/*/run-attempt1'));A=B/'artifacts';before=(B/'BEFORE_INPUT_IDENTITIES.json').read_bytes();assert before==(B/'AFTER_INPUT_IDENTITIES.json').read_bytes()and len(json.loads(before))==1737
r=R(A/'entry_completion.bin','ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING');entry=dict(stage=r.text(),error=r.text(),boundary_unchanged=r.u(),session_termination=r.u(),session_error=r.text(),native_termination=r.u(),native_error=r.text(),wall_seconds=r.d(),physical_step_attempts=r.u(),commits=r.u());r.end();assert entry['commits']==87 and entry['physical_step_attempts']==1174 and entry['session_termination']==entry['native_termination']==1 and entry['error']=='finite current near-boundary diagnostic cap (stop12288,active1024)'
whole=[]
for i in range(88):
 r=R(A/f'cycle-{i}/whole_current_cycle.bin','ALL_REJECTED_TRIALS_THROUGH_ONE_ACTUAL_CYCLE_WALL_SCOPE_V1');w=dict(zip(['cycle','trials_entered','physical_complete'],r.take('<3Q')));w.update(wall=r.d(),deadline_miss=r.u(),last_B_error=r.text(),fatal_error=r.text());w.update(zip(['trials_total','forecasts','steps','commits'],r.take('<4Q')));w['scope']=r.text();r.end();assert w['cycle']==i and w['deadline_miss']==int(w['wall']>.004)==1 and w['commits']==min(i+1,87)and w['steps']==2*w['commits']and w['physical_complete']==int(i<87)
 if 32<=i<87:assert w['trials_entered']==1 and not w['last_B_error']and not w['fatal_error']
 whole.append(w)
assert whole[-1]['trials_total']==123 and whole[-1]['forecasts']==245 and whole[-1]['fatal_error']==entry['error']
r=R(A/'actual_stop_dwell.bin','ACTUAL_PHYSICAL_V_A_ACCEPTED_HISTORY_STOP_DWELL_V2');passed,failed,dwell,required,maximum=r.take('<5Q');limits=r.take('<8d');assert limits==(1e-4,1e-3,1e-6,1e-4,1e-6,1e-4,1e-6,1e-6)and(passed,failed,dwell,required,maximum)==(0,0,0,50,178);count=r.u();assert count==110;rows=[];failcounts=[0]*6
for i in range(count):
 half,time=r.take('<Qd');v,a,C,w,alpha=[r.arr(7)for _ in range(5)];s,rate,b=r.take('<3d');guards,below,hold,consecutive=r.take('<4Q');Cd,sd=r.take('<2d');norms=[float(np.max(np.abs(x)))for x in[v,a,w,alpha]]+[rate,abs(b)];assert np.isfinite(norms).all()and min(norms)>=0 and half==1065+i and abs(time-(2.13+.002*i))<1e-12 and guards==1 and below==int(all(x<=y for x,y in zip(norms,limits[:6])))==0 and hold==consecutive==0 and Cd==sd==0
 for k,(value,limit)in enumerate(zip(norms,limits[:6])):failcounts[k]+=int(value>limit)
 rows.append(dict(global_half=half,time_s=time,v=norms[0],a=norms[1],w=norms[2],alpha=norms[3],s=s,r=rate,b=b,below=below,hold=hold,consecutive=consecutive,C_drift=Cd,s_drift=sd))
r.text();r.end();constants=json.loads(Path('/private/tmp/root62_stop_cause_review_v1_20261016/PINNED_PUBLIC_CONSTANTS.json').read_text());modes=[];warmcases=[];previous=None
for i in range(32,88):
 prevtrial=whole[i-1]['trials_entered']-1;p=A/f'cycle-{i-1}/trial-{prevtrial}/candidate.bin';r=R(p,'SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');r.text();permission,attempts,wrappers=r.take('<3Q');status,raw,api,nit,violationrow=r.take('<5Q');x=r.vec();assert permission==0 and attempts==wrappers==raw==1 and api==0 and len(x)==160;old=x.reshape(20,8);warm=np.zeros((20,8));begin=1
 for k,width in enumerate(nominal.MESH):
  end=begin+width;oldbegin=0
  for j,ow in enumerate(nominal.MESH):
   oldend=oldbegin+ow;left=max(begin,oldbegin);right=min(end,oldend)
   if right>left:warm[k]+=(float(right-left)/width)*old[j]
   oldbegin=oldend
  begin=end
 m=nominal.parse(A/f'cycle-{i}/trial-0/stop_objective_mode.bin');assert m['cycle']==i and m['trial']==0 and m['regenerate'];f=nominal.replay(m,constants,warm);ws=[c for c,s0 in enumerate(m['summary'])if s0[0]==(148 if c==7 else132)]
 if ws:warmcases.append(dict(cycle=i,channels=ws,previous_accepted_candidate_SHA256=hashlib.sha256(p.read_bytes()).hexdigest()))
 if previous is not None:
  C0,w0,s0,r0=previous;expectedw=[w0[j]+.004*float(old[0,j])for j in range(7)];expectedC=[C0[j]+.004*expectedw[j]for j in range(7)];expectedr=r0+.004*float(old[0,7]);expecteds=s0+.004*r0+.5*.004*.004*float(old[0,7]);assert max(abs(a-b0)for a,b0 in zip(expectedw,m['w']))<1e-18 and max(abs(a-b0)for a,b0 in zip(expectedC,m['C']))<1e-14 and abs(expectedr-m['r'])<1e-18 and abs(expecteds-m['s'])<1e-18
 previous=m['C'],m['w'],m['s'],m['r'];modes.append(dict(cycle=i,attempts=len(m['records']),selected=[s0[0]for s0 in m['summary']],replay=f))
r=R(A/'cycle-87/trial-0/candidate.bin','SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');assert r.text()==entry['error']and r.take('<3Q')==(0,1,0);q=r.take('<5Q');assert q[1:4]==(0,0,0)and len(r.vec())==0
report=dict(schema='ROOT64_ACTUAL87C_ALL_SELECTED_NOMINAL_PROVENANCE_STOP_AND_BOUNDARY_FAILURE_REVIEW_V1',payload_files=1154,payload_bytes=93512344,all_selected_native_payloads_bound_to_full_archive_manifest=bound,all489_codecs_source_complete=True,before_after1737_inputs_byte_equal=True,entry=entry,active_commands=32,braking_commands=55,task_halves=174,task_duration_ms=348,whole_boundaries=88,whole_4ms_misses=88,last_whole=whole[-1],all55_brake_cycles_one_trial_no_Berror=True,stop=dict(records=110,all_below_false=True,dwell=0,required=50,threshold_failure_counts=dict(zip(['physical_v','physical_a','accepted_w','accepted_alpha','progress_r','progress_b'],failcounts)),last=rows[-1]),all56_current_nominal_records_recomputed_with_authentic_previous_candidate_overlap_shift=True,warm_cases=warmcases,all55_sequential_command_progress_histories_reconstructed=True,last87_no_native_wrapper_SOLVED_B_C=True,scope='Actual64 clears commandw/alpha and progress thresholds and crosses old63 failure, but physical v/a remain above thresholds in every110 observations, dwell0/50.55 of64 declared brake commands finish; current87 terminates at original near-boundary12288 cap before nativeSOLVED/B/C. Codec source completion is independent of incomplete numeric hint. Scalar/provenance/stop review is not independent reproof of every geometric/nonlinear B, nor complete task/realtime/phase success. No64 replay/extension; full persisted archive check separate.')
for name,obj in [('ACTUAL64_RESULT.json',report),('STOP_ROWS.json',rows),('WHOLE_CYCLES.json',whole),('ALL56_NOMINAL_HISTORY_REPLAY.json',modes),('CODEC_RECEIPTS.json',receipts)]:bounded_write(O/name,json.dumps(obj,indent=2)+'\n')
print(json.dumps({'payloads':1154,'codecs':489,'nominals':56,'warm_cases':warmcases,'stop_fail_counts':failcounts,'last':rows[-1]}))

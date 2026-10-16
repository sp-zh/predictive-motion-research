from pathlib import Path
import sys,os,json,struct,hashlib,ast,importlib.util,math
import numpy as np
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
ROOT=Path('/Users/uot/Documents/ChatGPT/ros');P=Path('/private/tmp/phase5_controlled_stop_negative_leaving_terminal59_v1_20261016');O=Path('/private/tmp/root59_actual_review_v1_20261016');O.mkdir(exist_ok=True);os.environ['P5_DERIVED53_ROOT']=str(O)
spec=importlib.util.spec_from_file_location('strict',ROOT/'tools/cold_storage_verification_v1/strict_codec_reader.py');strict=importlib.util.module_from_spec(spec);spec.loader.exec_module(strict)
tree=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='R'],type_ignores=[]),'<Reader-only>','exec'))
def sha(b):return hashlib.sha256(b).hexdigest()
ready=json.loads((P/'READY.json').read_text());assert sha((P/'READY.json').read_bytes())=='19aea2dcb34cb58193996cc3f3029fcbf1f50be9173c20aec8692a1f201cc5c5';receipts=[]
for e in ready['payload']:
 p=P/e['path'];b=strict.bounded_read(p,256*1024**2);assert len(b)==e['bytes']and sha(b)==e['sha256']
 if p.suffix=='.bin':receipts.append(strict.verify_artifact(p))
assert len(ready['payload'])==435 and sum(e['bytes']for e in ready['payload'])==47489969 and all(e['source_complete']for e in receipts)
B=next(P.glob('actual-dell/*/run-attempt1'));A=B/'artifacts';T=A/'cycle-0/trial-0';before=(B/'BEFORE_INPUT_IDENTITIES.json').read_bytes();assert before==(B/'AFTER_INPUT_IDENTITIES.json').read_bytes()and len(json.loads(before))==1723
r=R(A/'entry_completion.bin','ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING');entry=dict(stage=r.text(),error=r.text(),boundary_unchanged=r.u(),session_termination=r.u(),session_error=r.text(),native_termination=r.u(),native_error=r.text(),wall_seconds=r.d(),physical_step_attempts=r.u(),commits=r.u());r.end();assert entry['error']=='bounded fixed artifact names'and entry['commits']==1 and entry['physical_step_attempts']==1002 and entry['session_termination']==entry['native_termination']==1
r=R(A/'cycle-0/whole_current_cycle.bin','ALL_REJECTED_TRIALS_THROUGH_ONE_ACTUAL_CYCLE_WALL_SCOPE_V1');w=dict(zip(['cycle','trials_entered','physical_complete'],r.take('<3Q')));w.update(wall=r.d(),deadline_miss=r.u(),last_B_error=r.text(),fatal_error=r.text());w.update(zip(['trials_total','forecasts','steps','commits'],r.take('<4Q')));w['scope']=r.text();r.end();assert (w['cycle'],w['trials_entered'],w['physical_complete'],w['trials_total'],w['forecasts'],w['steps'],w['commits'])==(0,1,1,1,2,2,1)and w['deadline_miss']==int(w['wall']>.004)==1
r=R(A/'actual_stop_dwell.bin','ACTUAL_PHYSICAL_V_A_ACCEPTED_HISTORY_STOP_DWELL_V2');passed,failed,dwell,required,maximum=r.take('<5Q');limits=r.take('<8d');count=r.u();assert count==0 and (passed,failed,dwell,required,maximum)==(0,0,0,50,178)and limits==(1e-4,1e-3,1e-6,1e-4,1e-6,1e-4,1e-6,1e-6);r.text();r.end()
r=R(T/'hint_negative_leaving_events.bin','STOP_ONLY_SMALLEST_CURRENT_ROW_NEGATIVE_MULTIPLIER_LEAVING_DIAGNOSTICS_V1');assert r.take('<6Q')==(0,0,1,0,0,0);r.text();r.end()
entries=strict.manifest_entries(T/'MANIFEST.yaml');assert len(entries)==24 and 'fine_timing.bin'in entries and 'cycle_timing.bin'not in entries and not(T/'cycle_timing.bin').exists()
assert all(x['created']and x['hash_valid']and x['complete']for x in entries.values())
r=R(T/'actual_task_errors.bin','ACTUAL_WORLD_TCP_TASK_ERROR_TWO_PHYSICAL_HALVES_V1');assert r.take('<3Q')==(0,0,1)and r.text()==''and r.u()==2;points=[]
for k in range(2):
 half,time=r.take('<Qd');raw=r.u();elapsed,logical_elapsed,s,rate=r.take('<4d');assert raw==1
 p1,q1,p2,q2=r.arr(3),r.arr(9).reshape(3,3),r.arr(3),r.arr(9).reshape(3,3);measured=r.u();assert measured==1;distance,angle=r.take('<2d');within,passed=r.take('<2Q');stage,error=r.text(),r.text()
 independent_d=float(np.linalg.norm(p1-p2));independent_angle=math.acos(float(np.clip((np.trace(q2.T@q1)-1)/2,-1,1)))
 assert half==k+1 and abs(time-(2.002+.002*k))<1e-12 and abs(distance-independent_d)<1e-15 and abs(angle-independent_angle)<1e-7 and within==int(distance<=.01 and angle<=.05)==1 and passed==1 and error==''
 points.append(dict(substep=half,time_s=time,translation_m=distance,orientation_rad=angle,translation_independent=independent_d,orientation_independent=independent_angle,original_task_flag=within,passed_record=passed,logical_s=s,logical_r=rate,stage=stage))
r.text();r.end()
out=dict(schema='ROOT59_REAL_EARLY_INTEGRATION_FAILURE_INDEPENDENT_SELECTED_REVIEW_V1',payload_files=435,payload_bytes=47489969,complete_binary_files=len(receipts),raw_binary_bytes=sum(x['raw_bytes']for x in receipts),all_stored_raw_SHA_CRC_singleEOF_passed=True,before_after1723_inputs_byte_equal=True,entry=entry,whole=w,task_halves=2,task_duration_ms=4,actual_task_points=points,stop_observations=0,stop_dwell=0,required_stop_dwell=50,new_stop_leaving_policy_not_activated=True,trial_manifest_complete_files=24,missing_25th='cycle_timing.bin',all24_trial_receipts_complete=True,cause_scope='lossless_evidence.cpp:56 receipts_.size()<24 rejects25th file; this is a fixed per-directory file-count bound, not enumerated filename whitelist. FirstC and afterobservation/fine timing exist; separate cycle_timing does not. Outer whole timing remains available and misses4ms.',scope='Retained original once59 early integration failure, not a Bland numerical failure at74, stopping or task success. PhysicalC count and two saved actual task points verified; not a complete independent B/C/SI re-audit. Original59 consumed, no replay/capture retry or old-limit expansion.')
for name,obj in [('RESULT.json',out),('CODEC_RECEIPTS.json',receipts),('TRIAL0_ARTIFACT_ROSTER.json',entries)]:bounded_write(O/name,json.dumps(obj,indent=2)+'\n')
print(json.dumps(out))

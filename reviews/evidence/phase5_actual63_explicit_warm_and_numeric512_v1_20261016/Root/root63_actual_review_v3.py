from pathlib import Path
import sys,os,json,hashlib,ast,struct,collections
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root63_nominal_reader_v4 as nominal
strict=nominal.strict
T=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.ClassDef)and x.name in['R','RV4']],type_ignores=[]),'<saved-readers>','exec'))
P=Path('/private/tmp/phase5_controlled_stop_explicit_warm_nominal_terminal63_v1_20261016');O=Path('/private/tmp/root63_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);M=Path('/private/tmp/phase5_current_braking_nominal63_source_v1_20261016/full_archive63_v2/readback');archive={e['path']:e for e in json.loads((M/'SOURCE_MANIFEST.json').read_text())['files']};ready=json.loads((P/'READY.json').read_text());assert len(ready['payload'])==902 and sum(e['bytes']for e in ready['payload'])==92107973;receipts=[];bound=0
for e in ready['payload']:
 p=P/e['path'];b=p.read_bytes();assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256']
 if e['path'].startswith('actual-dell/'):
  k='native63/'+str(Path(e['path']).relative_to(Path(*Path(e['path']).parts[:2])));a=archive[k];assert(e['bytes'],e['sha256'])==(a['bytes'],a['sha256']);bound+=1
 if p.suffix=='.bin':
  meta=strict.manifest_entries(p.parent/'MANIFEST.yaml')[p.name];assert meta['complete'];receipts.append(strict.verify_artifact(p))
B=next(P.glob('actual-dell/*/run-attempt1'));A=B/'artifacts';before=(B/'BEFORE_INPUT_IDENTITIES.json').read_bytes();assert before==(B/'AFTER_INPUT_IDENTITIES.json').read_bytes()and len(json.loads(before))==1734
r=R(A/'entry_completion.bin','ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING');entry=dict(stage=r.text(),error=r.text(),boundary_unchanged=r.u(),session_termination=r.u(),session_error=r.text(),native_termination=r.u(),native_error=r.text(),wall_seconds=r.d(),physical_step_attempts=r.u(),commits=r.u());r.end();assert entry['commits']==63 and entry['physical_step_attempts']==1126 and entry['session_termination']==entry['native_termination']==1 and entry['stage']=='FRESH_CURRENT_MATRIX_HINT_AND_NATIVE_SOLVER' and entry['error']=='current numeric iteration cap512'
whole=[]
for i in range(64):
 r=R(A/f'cycle-{i}/whole_current_cycle.bin','ALL_REJECTED_TRIALS_THROUGH_ONE_ACTUAL_CYCLE_WALL_SCOPE_V1');w=dict(zip(['cycle','trials_entered','physical_complete'],r.take('<3Q')));w.update(wall=r.d(),deadline_miss=r.u(),last_B_error=r.text(),fatal_error=r.text());w.update(zip(['trials_total','forecasts','steps','commits'],r.take('<4Q')));w['scope']=r.text();r.end();assert w['cycle']==i and w['deadline_miss']==int(w['wall']>.004)==1 and w['commits']==min(i+1,63)and w['steps']==2*w['commits']and w['physical_complete']==int(i<63)
 if 32<=i<63:assert w['trials_entered']==1 and not w['last_B_error']and not w['fatal_error']
 whole.append(w)
assert whole[-1]['trials_total']==99 and whole[-1]['forecasts']==197 and whole[-1]['fatal_error']==entry['error']
r=R(A/'actual_stop_dwell.bin','ACTUAL_PHYSICAL_V_A_ACCEPTED_HISTORY_STOP_DWELL_V2');passed,failed,dwell,required,maximum=r.take('<5Q');limits=r.take('<8d');assert limits==(1e-4,1e-3,1e-6,1e-4,1e-6,1e-4,1e-6,1e-6)and(passed,failed,dwell,required,maximum)==(0,0,0,50,178);count=r.u();assert count==62;rows=[]
for i in range(count):
 half,time=r.take('<Qd');v,a,C,w,alpha=[r.arr(7)for _ in range(5)];s,rate,b=r.take('<3d');guards,below,hold,consecutive=r.take('<4Q');Cd,sd=r.take('<2d');norms=[float(np.max(np.abs(x)))for x in[v,a,w,alpha]]+[rate,abs(b)];assert np.isfinite(norms).all()and min(norms)>=0 and half==1065+i and abs(time-(2.13+.002*i))<1e-12 and guards==1 and below==int(all(x<=y for x,y in zip(norms,limits[:6])))==0 and hold==consecutive==0 and Cd==sd==0;rows.append(dict(global_half=half,time_s=time,v=norms[0],a=norms[1],w=norms[2],alpha=norms[3],s=s,r=rate,b=b,below=below,hold=hold,consecutive=consecutive,C_drift=Cd,s_drift=sd))
r.text();r.end()
constants=json.loads(Path('/private/tmp/root62_stop_cause_review_v1_20261016/PINNED_PUBLIC_CONSTANTS.json').read_text())
mode32=nominal.parse(A/'cycle-32/trial-0/stop_objective_mode.bin');m32=nominal.replay(mode32,constants)
# Decode authentic previous accepted candidate's solver vector; the data-only permission stays false.
p=A/'cycle-52/trial-0/candidate.bin';r=R(p,'SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');reason=r.text();permission,attempts,wrappers=r.take('<3Q');status,raw_status,api_error,iterations,violation_row=r.take('<5Q');x=r.vec();assert permission==0 and attempts==wrappers==1 and raw_status==1 and api_error==0 and x.shape==(160,)and whole[52]['physical_complete']==1 and whole[52]['trials_entered']==1
# Independent overlap-average of original mesh, including zero beyond the horizon; retain exact source summation order.
warm=np.zeros((20,8));old=x.reshape(20,8);begin=1
for k,mesh in enumerate(nominal.MESH):
 end=begin+mesh;oldbegin=0
 for j,width in enumerate(nominal.MESH):
  oldend=oldbegin+width;left=max(begin,oldbegin);right=min(end,oldend)
  if right>left:warm[k]+=(float(right-left)/mesh)*old[j]
  oldbegin=oldend
 begin=end
mode53=nominal.parse(O/'actual53/stop_objective_mode.bin');m53=nominal.replay(mode53,constants,warm);assert len(mode53['records'])==156 and mode53['summary'][7][:2]==(148,149)and whole[53]['physical_complete']==1
assert np.array_equal(mode53['controls'][:,7],warm[:,7]);m53['previous_candidate_file_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();m53['previous_accepted_cycle']=52;m53['warm_progress_terminal_rate']=mode53['summary'][7][3];m53['all_original_scalar_constraints_replayed']=True
mode63=nominal.parse(A/'cycle-63/trial-0/stop_objective_mode.bin')
# There is no warm attempt in last63 nominal; require explicit input if future data adds one.
m63=nominal.replay(mode63,constants)
hint=nominal.m61.parse(A/'cycle-63/trial-0/hint_kkt_rank_events.bin');assert hint['cycle']==63 and hint['trial']==0 and len(hint['ranks'])==509 and len(hint['chosen'])==226 and hint['exact']==1 and not hint['indices']
r=R(A/'cycle-63/trial-0/candidate.bin','SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');assert r.text()=='current numeric iteration cap512' and r.take('<3Q')==(0,1,0);lastfields=r.take('<5Q');assert lastfields[1:4]==(0,0,0) and len(r.vec())==0
report=dict(schema='ROOT63_ACTUAL_SELECTED_COMPLETE_CODEC_WARM53_AND_NUMERIC512_FAILURE_REVIEW_V1',payload_files=902,payload_bytes=92107973,all_native_selected_files_bound_to_independently_verified_full_archive=bound,all_binary_codec_streams=len(receipts),source_complete_codecs=len(receipts),closed_source_failure_prefixes=0,before_after1734_inputs_byte_equal=True,entry=entry,task_halves=126,task_duration_ms=252,active_commands=32,braking_commands=31,whole_boundaries=64,whole_4ms_misses=64,last_whole=whole[-1],all31_completed_brake_cycles_one_trial_no_Berror=True,stop=dict(records=62,passed=0,failed=0,dwell=0,required=50,all_original_predicates_recomputed=True,first=rows[0],last=rows[-1]),first32=m32,warm53=m53,last63_nominal=m63,last63_hint=dict(rank_events=509,negative_leaving_events=226,exact_two_cycle_eligible=False,eligible_rows=0,no_native_SOLVED_B_or_C_at_failed_current=True),scope='Online63 crosses old62 failure at53 with explicit current-history shifted warm family, then fails512 numeric hint at63. Full63 original warm record extracted from independently copied archive, never inferred from final controls. Recorded previous52 candidate was a one-trial committed cycle; no prior execution owner/permission transferred. Scalar and stored-data review does not independently reprove every Model/geometric/nonlinear/B/C gate. No successful stop/task/realtime/phase acceptance; no63 replay/extension.')
for n,v in[('ACTUAL63_RESULT.json',report),('STOP_ROWS.json',rows),('WHOLE_CYCLES.json',whole),('CODEC_RECEIPTS.json',receipts),('WARM53_FAMILY_RECORDS.json',mode53['records']),('WARM53_INPUT_CONTROLS.json',warm.tolist())]:bounded_write(O/n,json.dumps(v,indent=2)+'\n')
print(json.dumps({'payload':902,'codecs':len(receipts),'source_complete':True,'commits':63,'braking_commands':31,'dwell':0,'warm53_replayed':True,'failure63':'numeric512','last':rows[-1]}))

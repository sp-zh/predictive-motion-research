from pathlib import Path
import sys,os,json,struct,hashlib,ast
import numpy as np
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
import root60_merged_parser_and_tests_v1 as m60
strict=m60.strict
from initializer_codec58_v4 import initializer_v4
ROOT=Path('/Users/uot/Documents/ChatGPT/ros');P=Path('/private/tmp/phase5_controlled_stop_merged_hint_terminal60_v2_20261016');O=Path('/private/tmp/root60_actual_review_v1_20261016');O.mkdir(exist_ok=True);os.environ['P5_DERIVED53_ROOT']=str(O)
tree=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.ClassDef)and x.name in ['R','RV4']],type_ignores=[]),'<Reader-only>','exec'))
sha=lambda b:hashlib.sha256(b).hexdigest();ready=json.loads((P/'READY.json').read_text());assert sha((P/'READY.json').read_bytes())=='8b75a6fdd499ef7dbe6c4b6b894234dd64a911b2c11c410b74ca20e87d46ac85';receipts=[]
for e in ready['payload']:
 p=P/e['path'];b=strict.bounded_read(p,256*1024**2);assert len(b)==e['bytes']and sha(b)==e['sha256']
 if p.suffix=='.bin':receipts.append(strict.verify_artifact(p))
assert len(ready['payload'])==682 and sum(e['bytes']for e in ready['payload'])==70492047 and len(receipts)==138 and all(e['source_complete']for e in receipts)
B=next(P.glob('actual-dell/*/run-attempt1'));A=B/'artifacts';before=(B/'BEFORE_INPUT_IDENTITIES.json').read_bytes();assert before==(B/'AFTER_INPUT_IDENTITIES.json').read_bytes()and len(json.loads(before))==1725
r=R(A/'entry_completion.bin','ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING');entry=dict(stage=r.text(),error=r.text(),boundary_unchanged=r.u(),session_termination=r.u(),session_error=r.text(),native_termination=r.u(),native_error=r.text(),wall_seconds=r.d(),physical_step_attempts=r.u(),commits=r.u());r.end();assert entry['error']=='current numeric iteration cap512'and entry['commits']==43 and entry['physical_step_attempts']==1086 and entry['session_termination']==entry['native_termination']==1
whole=[]
for i in range(44):
 r=R(A/f'cycle-{i}/whole_current_cycle.bin','ALL_REJECTED_TRIALS_THROUGH_ONE_ACTUAL_CYCLE_WALL_SCOPE_V1');w=dict(zip(['cycle','trials_entered','physical_complete'],r.take('<3Q')));w.update(wall=r.d(),deadline_miss=r.u(),last_B_error=r.text(),fatal_error=r.text());w.update(zip(['trials_total','forecasts','steps','commits'],r.take('<4Q')));w['scope']=r.text();r.end();assert w['cycle']==i and w['deadline_miss']==int(w['wall']>.004)==1 and w['commits']==min(i+1,43)and w['steps']==2*w['commits']and w['physical_complete']==int(i<43);whole.append(w)
assert whole[-1]['trials_total']==92 and whole[-1]['forecasts']==183
r=R(A/'actual_stop_dwell.bin','ACTUAL_PHYSICAL_V_A_ACCEPTED_HISTORY_STOP_DWELL_V2');passed,failed,dwell,required,maximum=r.take('<5Q');limits=r.take('<8d');assert limits==(1e-4,1e-3,1e-6,1e-4,1e-6,1e-4,1e-6,1e-6)and(passed,failed,dwell,required,maximum)==(0,0,0,50,178);count=r.u();assert count==22;rows=[]
for i in range(count):
 half,t=r.take('<Qd');v,a,C,w,alpha=[r.arr(7)for _ in range(5)];s,rate,b=r.take('<3d');guards,below,hold,consecutive=r.take('<4Q');Cd,sd=r.take('<2d');norms=[float(np.max(np.abs(x)))for x in [v,a,w,alpha]]+[rate,abs(b)];assert np.isfinite(norms).all()and min(norms)>=0 and half==1065+i and abs(t-(2.13+.002*i))<1e-12 and guards==1 and below==int(all(x<=lim for x,lim in zip(norms,limits[:6])))==0 and hold==consecutive==0 and Cd==sd==0
 rows.append(dict(global_half=half,time_s=t,v=norms[0],a=norms[1],w=norms[2],alpha=norms[3],s=s,r=rate,b=b,below=below,hold=hold,consecutive=consecutive,C_drift=Cd,s_drift=sd))
r.text();r.end()
def hint(path):
 r=R(path,'BOUNDED_CURRENT_MATRIX_OPTIMIZER_HINT_NOT_CANDIDATE');assert r.u()==1;complete,error=r.u(),r.text();x,y=r.vec(),r.vec();n=r.u();assert n<=512;events=[r.take('<3q4d')for _ in range(n)];faces=[r.take('<2q')for _ in range(r.u())];r.text();r.end();assert x.shape==(144,)and np.isfinite(x).all()and np.isfinite(y).all()and len(faces)<=144
 for i,e in enumerate(events):assert e[0]==i and 0<=e[1]<=144 and -1<=e[2]<len(y)and np.isfinite(e[3:]).all()and e[6]<=1e-10
 for row,side in faces:assert 0<=row<len(y)and side in [-1,1]
 return dict(complete=complete,error=error,x=x,y=y,events=events,faces=faces)
T0=A/'cycle-0/trial-0';T=A/'cycle-43/trial-0';h0=hint(T0/'current_numeric_hint.bin');h=hint(T/'current_numeric_hint.bin');assert h0['complete']==1 and h0['error']==''and h['complete']==0 and h['error']=='current numeric iteration cap512'and len(h['events'])==512
m0=m60.merged(T0/'hint_kkt_rank_events.bin',len(h0['y']),h0['events']);m=m60.merged(T/'hint_kkt_rank_events.bin',len(h['y']),h['events']);assert(m0['cycle'],m0['trial'],m0['requested_stop'],m0['policy_activated'])==(0,0,0,0)and not m0['chosen'];assert(m['cycle'],m['trial'],m['requested_stop'],m['policy_activated'])==(43,0,1,1)
entries=strict.manifest_entries(T0/'MANIFEST.yaml');assert len(entries)==24 and 'cycle_timing.bin'in entries and 'hint_negative_leaving_events.bin'not in entries and all(x['complete']and x['created']and x['hash_valid']for x in entries.values())
r=R(T0/'cycle_timing.bin','ACTUAL_OFFLINE_CYCLE_SEGMENTS_AND_4MS_MISS');cycle,complete=r.take('<2Q');wall=r.d();miss=r.u();stages=[r.take('<Qd')for _ in range(6)];commits,forecasts,steps,originalslots,separateslots=r.take('<5Q');r.text();r.end();assert(cycle,complete,commits,forecasts,steps)==(0,1,1,2,2)and miss==int(wall>.004)==1 and all(f in[0,1]and np.isfinite(v)and v>=0 for f,v in stages)
crossing=dict(schema='ROOT60_ACTUAL_FIRST_CROSSED59_FILE_COUNT_FAILURE_V1',trial0_complete_binary_receipts=24,final_cycle_timing_present_complete=True,new_merged_role_correct=True,standalone25th_diagnostic_absent=True,cycle_timing_decoded=dict(cycle=cycle,complete=complete,wall=wall,deadline_miss=miss,commits=commits,forecasts=forecasts,task_steps=steps),scope='Actual first transaction saved output chain, not only synthetic. Original24 cap unchanged; cycle timing still misses4ms. No stopping/task/phase acceptance.')
r=R(T/'qp_equality_reduction.bin','ORIGINAL_AND_NUMERICAL_PLANNING_TERMINAL_REDUCTION_V2');r.text();r.text();r.u();r.mat();r.vec();r.mat();r.vec();r.vec()
for _ in range(2):
 for __ in range(r.u()):r.u()
H,g,AA,lo,hi,D,F,seed,sy,ry,rs,Hs,gs,As,ls,us,Fs,solver_seed=[fn()for fn in[r.mat,r.vec,r.mat,r.vec,r.vec,r.vec,r.mat,r.vec,r.vec,r.vec,r.vec,r.mat,r.vec,r.mat,r.vec,r.vec,r.mat,r.vec]]
r.text();wrapper,native_attempts,status,px,py=r.take('<5Q');r.vec();r.vec();r.u();r.take('<5d');r.end();assert wrapper==native_attempts==0
z=initializer_v4(strict.read_artifact_bytes(T/'numeric_feasible_initializer.bin'),RV4,len(ls));assert z['complete']and z['seed'].tobytes()==solver_seed.tobytes();nominal=seed/D;mask=np.array([j%8!=7 for j in range(144)]);assert nominal[mask].tobytes()==solver_seed[mask].tobytes();delta=float(np.max(np.abs(D*(solver_seed-nominal))));sv=max(0.,float(np.max(ls-As@solver_seed)),float(np.max(As@solver_seed-us)));assert delta<=1e-6 and sv<=1e-12
def fixturehash(arrays):
 b=b''
 for a in arrays:b+=(struct.pack('<2Q',*a.shape)if a.ndim==2 else struct.pack('<Q',len(a)))+a.astype('<f8').tobytes()
 return sha(b)
binding=dict(schema='ROOT60_CURRENT43_FAILED512_ORIGINAL_ARRAYS_AND_DIAGNOSTICS_BINDING_V1',initialized_six_field_fixture_sha256=fixturehash([Hs,gs,As,ls,us,solver_seed]),original_nominal_and_D_seven_field_fixture_sha256=fixturehash([Hs,gs,As,ls,us,nominal,D]),rows=len(ls),original_nominal_sha256=sha(nominal.astype('<f8').tobytes()),D_sha256=sha(D.astype('<f8').tobytes()),initializer_complete=True,initializer_global_entered=z['global_scope_entered'],initializer_corrections=len(z['corrections']),nonbeta_bits_equal=True,seed_physical_delta_inf=delta,seed_fullrow_numpy_violation=sv,hint_complete=False,retained_hint_events=len(h['events']),retained_ordered_final_faces=len(h['faces']),faces_sha256=sha(b''.join(struct.pack('<2q',*e)for e in h['faces'])),events_sha256=sha(b''.join(struct.pack('<3q4d',*e)for e in h['events'])),partial_xy_sha256=sha(b''.join(struct.pack('<Q',len(a))+a.astype('<f8').tobytes()for a in[h['x'],h['y']])),merged_rank_records=len(m['ranks']),merged_chosen_records=len(m['chosen']),native_wrapper_attempts=0,native_solve_attempts=0,scope='New actual43 saved matrix/state failure distinct from old successful fixtures. Nominal Model forecast executed; failing hint prevents nativeOSQP/B/C for that trial. Scalar merged fields bind old true-min events but do not reconstruct all eligible working sets. Incomplete hint is not a successful optimization or infeasibility proof.')
report=dict(schema='ROOT60_SELECTED_TERMINAL_FIRST_CAPACITY_CROSSING_AND_NEW512_FAILURE_REVIEW_V1',payload_files=682,payload_bytes=70492047,complete_binary_files=len(receipts),raw_binary_bytes=sum(x['raw_bytes']for x in receipts),all_stored_raw_SHA_CRC_singleEOF_passed=True,before_after1725_inputs_byte_equal=True,entry=entry,whole_boundaries=44,whole4ms_misses=44,last_whole=whole[-1],active_commands=32,braking_commands=11,task_halves=86,task_duration_ms=172,stop=dict(records=22,passed=passed,failed=failed,dwell=0,required=50,all_original_predicates_anchor_resets_recomputed=True,first=rows[0],last=rows[-1]),actual0_output_fix_crossed=True,failed43=binding,scope='Retained actual60 integration repair plus new numerical failure. Selected data verification is not complete original SI/nonlinear/B/C independent re-audit; no full task/stop/realtime/hardware/phase acceptance.60v2 consumed; fresh61 repair must retain this failure and original budgets.')
for name,obj in [('RESULT.json',report),('STOP_ROWS.json',rows),('WHOLE_CYCLES.json',whole),('CODEC_RECEIPTS.json',receipts),('FIRST_C0_CAPACITY_CROSSING.json',crossing),('FAIL43_MATRIX_BINDING.json',binding)]:bounded_write(O/name,json.dumps(obj,indent=2)+'\n')
print(json.dumps(dict(payload=682,codecs=len(receipts),actual43binding=binding,stop_last=rows[-1],firstC0fix=crossing)))

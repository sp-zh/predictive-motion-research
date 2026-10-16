from pathlib import Path
import os,sys,json,hashlib,ast,struct
import numpy as np
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
import root61_parser_and_formal_review_v1 as m61
strict=m61.strict
from initializer_codec58_v4 import initializer_v4
ROOT=Path('/Users/uot/Documents/ChatGPT/ros');P=Path('/private/tmp/phase5_controlled_stop_exact_cycle_terminal61_v1_20261016');O=Path('/private/tmp/root61_actual_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O)
tree=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.ClassDef)and x.name in['R','RV4']],type_ignores=[]),'<saved-reader-only>','exec'))
tree=ast.parse(Path('/private/tmp/root60_actual_review_v1.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name in['hint','fixturehash']],type_ignores=[]),'<saved-functions-only>','exec'))
sha=lambda b:hashlib.sha256(b).hexdigest()
ready=json.loads((P/'READY.json').read_text());assert sha((P/'READY.json').read_bytes())=='fb3315bc4aaf38d9017e8f19df46ed6baa6a9399eda212ee29eebd69548a7d73';receipts=[]
for e in ready['payload']:
 p=P/e['path'];b=strict.bounded_read(p,256*1024**2);assert len(b)==e['bytes']and sha(b)==e['sha256']
 if p.suffix=='.bin':receipts.append(strict.verify_artifact(p))
assert len(ready['payload'])==1019 and sum(e['bytes']for e in ready['payload'])==136822475 and len(receipts)==316 and all(x['source_complete']for x in receipts)
B=next(P.glob('actual-dell/*/run-attempt1'));A=B/'artifacts';before=(B/'BEFORE_INPUT_IDENTITIES.json').read_bytes();assert before==(B/'AFTER_INPUT_IDENTITIES.json').read_bytes()and len(json.loads(before))==1728
r=R(A/'entry_completion.bin','ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING');entry=dict(stage=r.text(),error=r.text(),boundary_unchanged=r.u(),session_termination=r.u(),session_error=r.text(),native_termination=r.u(),native_error=r.text(),wall_seconds=r.d(),physical_step_attempts=r.u(),commits=r.u());r.end();assert entry['error']=='actual stop thresholds not reached in declared64 brake commands'and entry['commits']==96 and entry['physical_step_attempts']==1192 and entry['session_termination']==entry['native_termination']==1
whole=[]
for i in range(96):
 r=R(A/f'cycle-{i}/whole_current_cycle.bin','ALL_REJECTED_TRIALS_THROUGH_ONE_ACTUAL_CYCLE_WALL_SCOPE_V1');w=dict(zip(['cycle','trials_entered','physical_complete'],r.take('<3Q')));w.update(wall=r.d(),deadline_miss=r.u(),last_B_error=r.text(),fatal_error=r.text());w.update(zip(['trials_total','forecasts','steps','commits'],r.take('<4Q')));w['scope']=r.text();r.end();assert w['cycle']==i and w['deadline_miss']==int(w['wall']>.004)==1 and w['commits']==i+1 and w['steps']==2*w['commits']and w['physical_complete']==1 and not w['fatal_error'];whole.append(w)
assert whole[-1]['trials_total']==173 and whole[-1]['forecasts']==346 and whole[43]['trials_entered']==2
r=R(A/'actual_stop_dwell.bin','ACTUAL_PHYSICAL_V_A_ACCEPTED_HISTORY_STOP_DWELL_V2');passed,failed,dwell,required,maximum=r.take('<5Q');limits=r.take('<8d');assert limits==(1e-4,1e-3,1e-6,1e-4,1e-6,1e-4,1e-6,1e-6)and(passed,failed,dwell,required,maximum)==(0,0,0,50,178);count=r.u();assert count==128;rows=[]
for i in range(count):
 half,t=r.take('<Qd');v,a,C,w,alpha=[r.arr(7)for _ in range(5)];s,rate,b=r.take('<3d');guards,below,hold,consecutive=r.take('<4Q');Cd,sd=r.take('<2d');norms=[float(np.max(np.abs(x)))for x in[v,a,w,alpha]]+[rate,abs(b)];assert np.isfinite(norms).all()and min(norms)>=0 and half==1065+i and abs(t-(2.13+.002*i))<1e-12 and guards==1 and below==int(all(x<=lim for x,lim in zip(norms,limits[:6])))==0 and hold==consecutive==0 and Cd==sd==0
 rows.append(dict(global_half=half,time_s=t,v=norms[0],a=norms[1],w=norms[2],alpha=norms[3],s=s,r=rate,b=b,below=below,hold=hold,consecutive=consecutive,C_drift=Cd,s_drift=sd))
r.text();r.end()
T=A/'cycle-43/trial-0';h=hint(T/'current_numeric_hint.bin');assert h['complete']==1 and h['error']==''and len(h['events'])==284
m=m61.parse(T/'hint_kkt_rank_events.bin',len(h['y']),h['events']);assert(m['cycle'],m['trial'],m['stop'],m['policy'],m['exact'])==(43,0,1,1,1)and len(m['indices'])==6
r=R(T/'qp_equality_reduction.bin','ORIGINAL_AND_NUMERICAL_PLANNING_TERMINAL_REDUCTION_V2');r.text();r.text();r.u();r.mat();r.vec();r.mat();r.vec();r.vec()
for _ in range(2):
 for __ in range(r.u()):r.u()
H,g,AA,lo,hi,D,F,seed,sy,ry,rs,Hs,gs,As,ls,us,Fs,solver_seed=[fn()for fn in[r.mat,r.vec,r.mat,r.vec,r.vec,r.vec,r.mat,r.vec,r.vec,r.vec,r.vec,r.mat,r.vec,r.mat,r.vec,r.vec,r.mat,r.vec]]
r.text();wrapper,native_attempts,status,px,py=r.take('<5Q');r.vec();r.vec();r.u();r.take('<5d');r.end();assert wrapper==native_attempts==1
z=initializer_v4(strict.read_artifact_bytes(T/'numeric_feasible_initializer.bin'),RV4,len(ls));assert z['complete']and solver_seed.tobytes()==h['x'].tobytes();nominal=seed/D
assert fixturehash([Hs,gs,As,ls,us,z['seed']])=='e8b14e198bafc29885419f2a42d54681d172b4ba1bd7f80aeca79f1044e43254'
Q=Path('/private/tmp/phase5_bland_cycle43_analysis61_v1_20261016');assert D.astype('<f8').tobytes()==(Q/'ORIGINAL_SCALE_D144.bin').read_bytes()and nominal.astype('<f8').tobytes()==(Q/'ORIGINAL_NOMINAL_SCALED_SEED144.bin').read_bytes()
xy=b''.join(struct.pack('<Q',len(x))+x.astype('<f8').tobytes()for x in[h['x'],h['y']]);assert sha(xy)=='31e7612c6c9fc52cb714ae52225d8d38634547bfb8989bfe3dc42bebf9ceab97'
FML=Path('/private/tmp/phase5_exact_cycle_endpoint61_source_v1_20261016/production_math_pure_v1/readback/stop_actual60_43_0');assert xy==Path(str(FML)+'.finalxy.bin').read_bytes()and b''.join(struct.pack('<3q4d',*e)for e in h['events'])==Path(str(FML)+'.states.bin').read_bytes()
primal=max(0.,float(np.max(ls-As@h['x'])),float(np.max(As@h['x']-us)));stat=float(np.max(np.abs(Hs@h['x']+gs+As.T@h['y'])));assert primal<=1e-12 and stat<=1e-10
binding=dict(schema='ROOT61_ACTUAL43_ORIGINAL_FAILED_QP_AND_FORMAL_OUTPUT_BITEXACT_V1',initialized_fixture_sha256=fixturehash([Hs,gs,As,ls,us,z['seed']]),D_and_original_nominal_bitexact=True,finalxy_sha256=sha(xy),events=284,all_events_and_finalxy_bitexact_formal=True,primal_numpy=primal,stationarity_numpy=stat,native_wrapper_attempts=wrapper,native_solve_attempts=native_attempts,merged_eligibility_indices=m['indices'],eligible_rows=[m['chosen'][i][1]for i in m['indices']],current43_trials=2,scope='Trial43/0 repaired numerical hint and native entry; actual C for current43 belongs to the full two-trial transaction. Source/pure witness establishes exact cycle policy; native scalar indices do not reconstruct all optimizer states. Not independent full SI/nonlinear/geometric/B/C acceptance.')
report=dict(schema='ROOT61_SELECTED_TERMINAL_STOP_FAILURE_AND_NUMERICAL_CROSSING_REVIEW_V1',payload_files=1019,payload_bytes=136822475,complete_binary_files=len(receipts),raw_binary_bytes=sum(x['raw_bytes']for x in receipts),all_stored_raw_SHA_CRC_singleEOF_passed=True,before_after1728_inputs_byte_equal=True,entry=entry,whole_boundaries=96,whole4ms_misses=96,last_whole=whole[-1],active_commands=32,braking_commands=64,task_halves=192,task_duration_ms=384,stop=dict(records=128,passed=passed,failed=failed,dwell=0,required=50,all_original_predicates_anchor_resets_recomputed=True,first=rows[0],last=rows[-1]),actual43=binding,scope='Complete declared64 braking prefix and retained original stop failure. Last physical_complete1 is per-current before post-loop stop refusal; it is not session stop success. Selected review not independent full original SI/nonlinear/geometric/B/C audit. No full task/stop/realtime/hardware/phase acceptance. Offline61 consumed and ended manualwait; no62 or development without direct human resume.')
for name,obj in [('RESULT.json',report),('STOP_ROWS.json',rows),('WHOLE_CYCLES.json',whole),('CODEC_RECEIPTS.json',receipts),('ACTUAL43_MATRIX_AND_FORMAL_BINDING.json',binding)]:bounded_write(O/name,json.dumps(obj,indent=2)+'\n')
print(json.dumps(dict(payload=1019,codecs=len(receipts),commits=96,stop_count=128,dwell=0,actual43=binding)))

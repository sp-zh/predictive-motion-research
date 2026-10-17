from pathlib import Path
import os,sys,json,struct,ast,hashlib,base64,zlib,math
import numpy as np
sys.path.insert(0,'/private/tmp');sys.path.insert(0,'/private/tmp/root65_codec_independent_review_v1_20261016')
from bounded_derived_bytes53_v1 import bounded_write
import reader as new
import root63_nominal_reader_v4 as old
strict=old.strict
T=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());cls=next(x for x in T.body if isinstance(x,ast.ClassDef)and x.name=='R');cls.name='FileR';exec(compile(ast.Module(body=[cls],type_ignores=[]),'<path-reader>','exec'))
R=old.R
T=ast.parse(Path('/private/tmp/root_independent_controlled_stop52_review_20261012/reference_source/audit_geometry_qp_actual.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.FunctionDef)and x.name=='snapshot'],type_ignores=[]),'<snapshot-only>','exec'))
O=Path('/private/tmp/root65_actual_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);S=O/'selected/native65';A=S/'run-attempt1/artifacts';B=Path('/Users/uot/Documents/ChatGPT/ros/transfer/cold-backups/native65-complete-direct-mac-20261016-v1');source=json.loads((B/'PRODUCER_PREPARED.json').read_text())['native_source']
records=json.loads((B/'FULL_NATIVE_CODEC_READBACK.json').read_text())['files'];rawmeta={str(Path(e['file']).relative_to(source)):e for e in records};receipts=[]
for p in A.rglob('*.bin'):receipts.append(strict.verify_artifact(p))
assert all(e['source_complete']for e in receipts)
assert (S/'run-attempt1/BEFORE_INPUT_IDENTITIES.json').read_bytes()==(S/'run-attempt1/AFTER_INPUT_IDENTITIES.json').read_bytes();assert len(json.loads((S/'run-attempt1/BEFORE_INPUT_IDENTITIES.json').read_text()))==1743
r=FileR(A/'entry_completion.bin','ACTIVE_SESSION_FINAL_SCOPE_AND_TIMING');entry=dict(stage=r.text(),error=r.text(),boundary_unchanged=r.u(),session_termination=r.u(),session_error=r.text(),native_termination=r.u(),native_error=r.text(),wall_seconds=r.d(),physical_step_attempts=r.u(),commits=r.u());r.end()
assert entry['commits']==50 and entry['physical_step_attempts']==1100 and entry['session_termination']==entry['native_termination']==1 and entry['error']=='strict current-history first-command contraction planning gate; no clipping'
whole=[];bundled=json.loads((O/'ALL51_WHOLE_STORED_BYTES.json').read_text())
for i in range(51):
 name=f'cycle-{i}/whole_current_cycle.bin';data=base64.b64decode(bundled[name]);e=rawmeta['run-attempt1/artifacts/'+name];assert len(data)==e['stored_bytes']and hashlib.sha256(data).hexdigest()==e['stored_sha256']
 z=zlib.decompressobj(31);raw=z.decompress(data,65536);assert z.eof and not z.unused_data and not z.unconsumed_tail and len(raw)==e['raw_bytes']and hashlib.sha256(raw).hexdigest()==e['raw_sha256']
 r=R(raw,'ALL_REJECTED_TRIALS_THROUGH_ONE_ACTUAL_CYCLE_WALL_SCOPE_V1');w=dict(zip(['cycle','trials_entered','physical_complete'],r.take('<3Q')));w.update(wall=r.d(),deadline_miss=r.u(),last_B_error=r.text(),fatal_error=r.text());w.update(zip(['trials_total','forecasts','steps','commits'],r.take('<4Q')));w['scope']=r.text();r.end();assert w['cycle']==i and w['deadline_miss']==int(w['wall']>.004)==1 and w['commits']==min(i+1,50)and w['steps']==2*w['commits']and w['physical_complete']==int(i<50)
 if 32<=i<50:assert w['trials_entered']==1 and not w['last_B_error']and not w['fatal_error']
 whole.append(w)
assert whole[-1]['trials_total']==86 and whole[-1]['forecasts']==171 and whole[-1]['fatal_error']==entry['error']
r=FileR(A/'actual_stop_dwell.bin','ACTUAL_PHYSICAL_V_A_ACCEPTED_HISTORY_STOP_DWELL_V2');passed,structfailed,dwell,required,maximum=r.take('<5Q');limits=r.take('<8d');assert limits==(1e-4,1e-3,1e-6,1e-4,1e-6,1e-4,1e-6,1e-6)and(passed,structfailed,dwell,required,maximum)==(0,0,0,50,178);count=r.u();assert count==36;rows=[];failcounts=[0]*6
for i in range(count):
 half,time=r.take('<Qd');v,a,C,w,alpha=[r.arr(7)for _ in range(5)];s,rate,b=r.take('<3d');guards,below,hold,consecutive=r.take('<4Q');Cd,sd=r.take('<2d');norms=[float(np.max(np.abs(x)))for x in[v,a,w,alpha]]+[rate,abs(b)];assert np.isfinite(norms).all()and half==1065+i and abs(time-(2.13+.002*i))<1e-12 and guards==1 and below==int(all(x<=y for x,y in zip(norms,limits[:6])))==0 and hold==consecutive==0 and Cd==sd==0
 for k,(value,limit)in enumerate(zip(norms,limits[:6])):failcounts[k]+=int(value>limit)
 rows.append(dict(global_half=half,time_s=time,v=norms[0],a=norms[1],w=norms[2],alpha=norms[3],s=s,r=rate,b=b,below=below,hold=hold,consecutive=consecutive,C_drift=Cd,s_drift=sd))
r.text();r.end();assert failcounts==[36]*6
base=snapshot(strict.read_artifact_bytes(A/'observation_before.bin'));bias=base['x'][14:21]-base['x'][:7];constants=json.loads(Path('/private/tmp/root62_stop_cause_review_v1_20261016/PINNED_PUBLIC_CONSTANTS.json').read_text());modes=[];warmcases=[];previous=None
for i in range(32,51):
 prevtrial=whole[i-1]['trials_entered']-1;p=A/f'cycle-{i-1}/trial-{prevtrial}/candidate.bin';r=FileR(p,'SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');r.text();permission,attempts,wrappers=r.take('<3Q');status,raw,api,nit,violationrow=r.take('<5Q');x=r.vec();assert permission==0 and attempts==wrappers==raw==1 and api==0 and len(x)==160;prior=x.reshape(20,8);warm=np.zeros((20,8));begin=1
 for k,width in enumerate(old.MESH):
  end=begin+width;oldbegin=0
  for j,ow in enumerate(old.MESH):
   oldend=oldbegin+ow;left=max(begin,oldbegin);right=min(end,oldend)
   if right>left:warm[k]+=(float(right-left)/width)*prior[j]
   oldbegin=oldend
  begin=end
 m=new.parse(A/f'cycle-{i}/trial-0/stop_objective_mode.bin');f=new.replay(m,constants,warm);before=snapshot(strict.read_artifact_bytes(A/f'cycle-{i}/trial-0/observation_before.bin'));assert m['cycle']==i and m['trial']==0 and m['ordinal']==i-31
 for key,value in [('q',before['x'][:7]),('v',before['x'][7:14]),('C',before['x'][14:21]),('w',before['x'][21:28]),('alpha',before['alpha']),('baseline_offset',bias)]:assert np.array_equal(m[key],value),key
 assert m['s']==before['x'][28]and m['r']==before['x'][29]and m['b']==before['b']
 ws=[c for c,summary in enumerate(m['summary'])if summary[0]==(148 if c==7 else 132)]
 if ws:warmcases.append(dict(cycle=i,channels=ws,previous_candidate_stored_SHA256=hashlib.sha256(p.read_bytes()).hexdigest()))
 if previous is not None:
  C0,w0,s0,r0=previous;wn=[w0[j]+.004*float(prior[0,j])for j in range(7)];Cn=[C0[j]+.004*wn[j]for j in range(7)];rn=r0+.004*float(prior[0,7]);sn=s0+.004*r0+.5*.004*.004*float(prior[0,7]);assert max(abs(a-b0)for a,b0 in zip(wn,m['w']))<1e-18 and max(abs(a-b0)for a,b0 in zip(Cn,m['C']))<1e-14 and abs(rn-m['r'])<1e-18 and abs(sn-m['s'])<1e-18
 previous=m['C'],m['w'],m['s'],m['r'];modes.append(dict(cycle=i,attempts=len(m['records']),selected=[s0[0]for s0 in m['summary']],replay=f))
final_before=snapshot(strict.read_artifact_bytes(A/'cycle-50/trial-0/observation_before.bin'));last_after=snapshot(strict.read_artifact_bytes(A/'cycle-49/trial-0/observation_after.bin'));assert final_before['x'].tobytes()==last_after['x'].tobytes()and final_before['alpha'].tobytes()==last_after['alpha'].tobytes()and final_before['b']==last_after['b']
r=FileR(A/'cycle-50/trial-0/candidate.bin','SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');assert r.text()==entry['error']and r.take('<3Q')==(0,1,1);status,raw,api,nit,violationrow=r.take('<5Q');assert(status,raw,api,nit)==(0,1,0,1);assert len(r.vec())==160
report=dict(schema='ROOT65_ACTUAL50C_ALL19_NOMINAL_STOP_HISTORY_AND_SCOPE_REVIEW_V1',selected_payloads_all_SHA_bound=True,selected_sourcecomplete_codecs=len(receipts),before_after1743_inputs_byte_equal=True,entry=entry,active_commands=32,braking_commands=18,task_halves=100,task_duration_ms=200,trials=86,forecasts=171,whole_boundaries=51,whole_4ms_misses=51,last_whole=whole[-1],all18_braking_cycles_one_trial_no_Berror=True,stop=dict(records=36,all_below_false=True,structural_error_flag=0,structural_flag_is_not_threshold_pass_counter=True,dwell=0,required=50,threshold_failure_counts=dict(zip(['physical_v','physical_a','accepted_w','accepted_alpha','progress_r','progress_b'],failcounts)),hold_anchor_unavailable_not_actual_drift_violation=True,last=rows[-1]),all19_nominal_families_and_authentic_prior_candidate_shift_replayed=True,warm_cases=warmcases,all18_history_recurrences_reconstructed=True,failed50_native_SOLVED_but_no_forward_B_C=True,failed50_actual_state_equals_last49_after_bitexact=True,archive_SHA256='3ab9e379944389ce50233a7de6ef0fd2bbbcc9fea5708c26e1cc459b024aaaf5',scope='Actual retained failed development run. Not physical stopping, realtime, full task or phase acceptance. Saved family/history/stop arithmetic is independent; sampled originalSI/B400/C2 review separate, no Model/solver rerun.')
for name,value in [('ACTUAL65_RESULT.json',report),('STOP_ROWS.json',rows),('WHOLE_CYCLES.json',whole),('ALL19_NOMINAL_HISTORY_REPLAY.json',modes),('SELECTED_CODEC_RECEIPTS.json',receipts)]:bounded_write(O/name,json.dumps(value,indent=2)+'\n')
print(json.dumps({'nominals':len(modes),'records_replayed':sum(x['attempts']for x in modes),'warm_cases':warmcases,'stop_failures':failcounts,'last':rows[-1]}))

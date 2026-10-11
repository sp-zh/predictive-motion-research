"""Ongoing36 closeout retention/history/bounds only; no new model/solver/native."""
from pathlib import Path
import hashlib,json,sys,importlib.util,ast,csv
import numpy as np
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;PACK=Path('/Users/uot/Documents/ChatGPT/ros/results/phase5-reference/nonzero-progress-actual-v1-20261011/runtime-import1');BASE=PACK/'artifacts';PROFILE=Path('/private/tmp/phase5_nonzero_progress_tail_runtime_profile_v1_20261011')
pins={}
def pin(p,h=None):
 b=p.read_bytes();sha=hashlib.sha256(b).hexdigest();assert h is None or sha==h;pins[str(p)]={'bytes':len(b),'sha256':sha};return b
helper=Path('/private/tmp/root_independent_geometry_qp_actual_review_20261011/audit_geometry_qp_actual.py');spec=importlib.util.spec_from_file_location('root_file_parser',helper);m=importlib.util.module_from_spec(spec);pin(helper,'b648463d205992e217480407e8b2a5e553ac0401137b3a1ce084f1bcc3597c5b');spec.loader.exec_module(m);m.pin=pin
b=pin(OUT/'audit_actual36.py');tree=ast.parse(b);ctx={'R':m.R};exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ['reduction','metrics']],type_ignores=[]),'<frozen-local-schema>','exec'),ctx)
profile=json.loads(pin(PROFILE/'profile-version1/active_input.json'));producer=json.loads(pin(PROFILE/'profile-version1/PRODUCER.json'));plan=json.loads(pin(PROFILE/'active_run_plan.json'));before=m.snapshot(pin(BASE/'observation_before.bin'))
r=m.R(pin(BASE/'actual_warmup.bin'),'ACTUAL_TASK_INITIALIZATION_AND_PHYSICAL_WARMUP_V2');flags=[r.u() for _ in range(4)];stage,error=r.text(),r.text();held=r.nums(7);translation,rotation=r.d(),r.d();r.text();count=r.u();assert count==1000 and not error;warm=[];maxa=maxj=0.
for i in range(count):
 p={'step':r.u(),'time':r.d(),'returned':r.u(),'native_read':r.u(),'scratch_read':r.u()}
 for k in ['q','v','C','a','j']:p[k]=r.nums(7)
 for k in ['ja','geo','observer','contacts']:p[k]=r.u()
 p['warnings']=[r.u() for _ in range(8)];p.update(true=r.d(),cover=r.d(),queries=r.u(),tcp=r.d(),arm=r.d(),stage=r.text(),error=r.text())
 assert p['step']==i+1 and p['returned']==1 and p['native_read']==p['scratch_read']==7 and p['geo']==p['observer']==1 and not p['error'] and p['C'].tobytes()==held.tobytes() and p['contacts']==0 and p['warnings']==[0]*8 and p['queries']==9035 and p['tcp']<=1e-8 and p['arm']<=1e-8
 if i:
  aa=(p['v']-warm[-1]['v'])/.002;assert aa.tobytes()==p['a'].tobytes();jj=(aa-warm[-1]['a'])/.002;assert jj.tobytes()==p['j'].tobytes()
 maxa=max(maxa,m.maxabs(p['a']));maxj=max(maxj,m.maxabs(p['j'])) if p['ja'] else maxj;warm.append(p)
r.end();last=warm[-1];assert last['q'].tobytes()==before['x'][:7].tobytes() and last['v'].tobytes()==before['x'][7:14].tobytes()==before['v'].tobytes() and last['a'].tobytes()==before['a'].tobytes() and last['time']==before['time'] and before['steps']==1000 and before['boundary']==[0,0]
journal=pin(BASE/'actual_step_journal.csv');jrows=list(csv.reader(journal.decode().splitlines()));assert len(jrows)==3000 and all(len(x)==58 for x in jrows)
for i,p in enumerate(warm):
 trip=jrows[i*3:i*3+3];assert [x[0] for x in trip]==['BEFORE_NATIVE_STEP_ATTEMPT','NATIVE_STEP_RETURNED_BEFORE_SCRATCH','COMPLETE_ACTUAL_OBSERVATION_AND_GEOMETRY']
 for phase,row in enumerate(trip):
  v=np.array([float(x) for x in row[1:]]);assert v[0]==i+1 and v[28:35].tobytes()==held.tobytes()
  if phase==2:assert v[14:21].tobytes()==p['q'].tobytes() and v[21:28].tobytes()==p['v'].tobytes() and v[35:42].tobytes()==p['a'].tobytes() and v[42:49].tobytes()==p['j'].tobytes()
constants=json.loads(pin(Path('/private/tmp/public_live_affine_v2_integrated_first_cycle_canonical_protocol_repair_v2_20261010/proposed-files/inputs/public_constants.json'),profile['constants']['sha256']));qr=np.array(constants['joint_range']).reshape(7,2);cr=np.array(constants['control_range']).reshape(7,2);speed=np.array(profile['physical_speed'])
rootR=m.R(pin(BASE/'retained_commit_history.bin'),'ALL_ACTUAL_COMMIT_OUTCOMES_AND_TASK_ERRORS_V2');assert rootR.u()==3;retained=[m.commit_record(rootR) for _ in range(3)];assert rootR.u()==3;retained_metrics=[ctx['metrics'](rootR) for _ in range(3)];rootR.text();rootR.end()
compmax=0.;allvalue=0
for cycle in range(3):
 cb=BASE/f'cycle-{cycle}';value=m.candidate_value(pin(cb/'candidate_value.bin'));B=m.validation(pin(cb/'candidate_validation.bin'));d=ctx['reduction'](pin(cb/'qp_equality_reduction.bin'));hint=m.parse_current_hint(pin(cb/'current_numeric_hint.bin'))
 for p,bb in zip(value['points'],B['points']):
  assert np.all(p['q']>=qr[:,0]+.005) and np.all(p['q']<=qr[:,1]-.005) and np.all(p['C']>=cr[:,0]+.005) and np.all(p['C']<=cr[:,1]-.005) and np.all(abs(p['v'])<=speed) and m.maxabs(p['w'])<=.0625 and 0<=p['s']<=1 and 0<=p['r']<=.2
  assert np.isfinite([bb[k] for k in ['true','cover','sigma','geometry_lower','sigma_lower','affine_error','trust']]).all() and min(bb['true'],bb['cover'])>=.005 and bb['sigma']>=1e-6;allvalue+=1
 hx=d['As']@hint['x'];hy=hint['y'];comp=np.where(hy>=0,hy*(d['us']-hx),-hy*(hx-d['ls']));compmax=max(compmax,m.maxabs(comp));assert m.maxabs(comp)<=1e-10
 r=m.R(pin(cb/'actual_commit.bin'),'TWO_REAL_2MS_HELD_TARGET_COMMIT_OR_RETAINED_PARTIAL_V1');actual=m.commit_record(r);r.end()
 def same(a,b):
  assert a.keys()==b.keys()
  for k in a:
   if isinstance(a[k],np.ndarray):assert a[k].tobytes()==b[k].tobytes(),k
   elif isinstance(a[k],list) and a[k] and isinstance(a[k][0],dict):
    assert len(a[k])==len(b[k]);[same(x,y) for x,y in zip(a[k],b[k])]
   else:assert a[k]==b[k],k
 same(actual,retained[cycle])
 r=m.R(pin(cb/'actual_task_errors.bin'),'ACTUAL_WORLD_TCP_TASK_ERROR_TWO_PHYSICAL_HALVES_V1');te=ctx['metrics'](r);r.end();rt=retained_metrics[cycle]
 assert te['before']==rt['before'] and te['success']==rt['success'] and te['error']==rt['error'] and te['scope']==rt['scope']
 for a,b in zip(te['points'],rt['points']):
  for key in a:
   if key in ['actual','desired']:
    for x,y in zip(a[key],b[key]):assert x.tobytes()==y.tobytes()
   else:assert a[key]==b[key]
 for p in actual['points']:assert np.all(abs(p['v'])<=speed) and np.all(p['q']>=qr[:,0]+.005) and np.all(p['q']<=qr[:,1]-.005)
rows=json.loads(pin(PACK/'BEFORE_INPUT_IDENTITIES.json'));assert pin(PACK/'BEFORE_INPUT_IDENTITIES.json')==pin(PACK/'AFTER_INPUT_IDENTITIES.json');assert len(rows)==len(plan['input_files'])==1703
for a,b in zip(rows,plan['input_files']):
 for key in ['requested_path','bytes','sha256']:assert a[key]==b[key]
 if 'resolved_path' in b:assert a['resolved_path']==b['resolved_path']
assert pin(PACK/'BEFORE_READONLY_ROSTERS.json')==pin(PACK/'AFTER_READONLY_ROSTERS.json')
batch=json.loads(pin(PACK/'BATCH_PREFIX.json'));argv=batch['records'][0]['argv'];assert argv==plan['compile_argv'][0] and argv[2]==hashlib.sha256((PROFILE/'profile-version1/active_input.json').read_bytes()).hexdigest() and argv[3]==producer['sha256']
r=m.R(pin(BASE/'bootstrap.bin'),'ACTUAL_DIRECT_SESSION_API_ENTRIES');facts=[r.u() for _ in range(9)];r.end();assert facts==[1,2,1,1016,1014,2040,8,1006,3]
for p,i in pins.items():b=Path(p).read_bytes();assert len(b)==i['bytes'] and hashlib.sha256(b).hexdigest()==i['sha256']
result={'schema':'ROOT_ACTUAL36_RETENTION_CLOSEOUT_V1','warm_points':1000,'warm_journal_rows':3000,'warm_final_state_and_actual_history_match_task0':True,'startup_physical_derivatives_excluded':{'max_a':maxa,'max_available_j':maxj,'first_j_available':warm[0]['ja']},'all1200_value_bounds_checked':allvalue,'hint_signed_complementarity_max':compmax,'all3_retained_actual_commit_and_task_metric_records_exact':True,'actual6_bounds_checked':True,'all1703_profile_before_after_records_exact':True,'profile_bound_actual_single_dispatch':True,'facts':facts,'input_pins':pins,'scope':'Saved-file arithmetic/provenance only; full queryraw not retained, no fault injection, runtime SDK proof beyond recorded pins/Root passive proof, task/stop/realtime/Phase5 acceptance.'}
(OUT/'RETENTION_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='input_pins'}))

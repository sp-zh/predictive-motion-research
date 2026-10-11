"""Supplemental actual D3 frozen-file arithmetic; no Model/native/optimizer."""
from pathlib import Path
import json,hashlib,csv,struct,importlib.util,sys
sys.dont_write_bytecode=True
import numpy as np
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('own_schema',OUT/'audit_geometry_qp_actual.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
PACK=Path('/private/tmp/phase5_geometry_qp_actual_checkpoint_v1_20261011');UNIT=PACK/'actual-dell/session-geometry-qp-three-cycle-v4-20261011-attempt30';RUN=UNIT/'run-attempt1';BASE=RUN/'artifacts'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ready=PACK/'READY.json';assert sha(ready)=='ade56cd0ac41beaa989b31f402693a7a16231131b53866d2769a613c8116334b'
manifest=json.loads(ready.read_bytes())['files'];inputs={str(PACK/n):(v['bytes'],v['sha256']) for n,v in manifest.items()};inputs[str(ready)]=(ready.stat().st_size,sha(ready))
before=a.snapshot(a.pin(BASE/'observation_before.bin'));r=a.R(a.pin(BASE/'actual_warmup.bin','ddfe59b603e0caa2ef85b0bb3e3e14a75e4f57a639cc22f8bad2fda249802901'),'ACTUAL_TASK_INITIALIZATION_AND_PHYSICAL_WARMUP_V2');flags=[r.u() for _ in range(4)];stage,error=r.text(),r.text();held=r.nums(7);position,rotation=r.d(),r.d();r.text();count=r.u();assert count==1000 and not error;maxa=maxj=0;warm=[]
for i in range(count):
 p={'step':r.u(),'time':r.d(),'returned':r.u(),'native_read':r.u(),'scratch_read':r.u()}
 for k in ['q','v','C','a','j']:p[k]=r.nums(7)
 for k in ['ja','geo','observer','contacts']:p[k]=r.u()
 p['warnings']=[r.u() for _ in range(8)];p.update(true=r.d(),cover=r.d(),queries=r.u(),tcp=r.d(),arm=r.d(),stage=r.text(),error=r.text())
 assert p['step']==i+1 and p['returned']==1 and p['native_read']==p['scratch_read']==7 and p['geo']==p['observer']==1 and not p['error'] and p['C'].tobytes()==held.tobytes()
 maxa=max(maxa,a.maxabs(p['a']));maxj=max(maxj,a.maxabs(p['j'])) if p['ja'] else maxj
 warm.append(p)
r.end();last=warm[-1];assert last['q'].tobytes()==before['x'][:7].tobytes() and last['v'].tobytes()==before['x'][7:14].tobytes()==before['v'].tobytes() and last['a'].tobytes()==before['a'].tobytes() and last['time']==before['time'] and before['steps']==1000
jdata=a.pin(BASE/'actual_step_journal.csv');rows=list(csv.reader(jdata.decode().splitlines()));assert len(rows)==3000 and all(len(x)==58 for x in rows)
phases=['BEFORE_NATIVE_STEP_ATTEMPT','NATIVE_STEP_RETURNED_BEFORE_SCRATCH','COMPLETE_ACTUAL_OBSERVATION_AND_GEOMETRY']
# Frozen actual journal spells the pre-entry event as declared by WarmupSpec.
assert len(set(x[0] for x in rows))==3
for i,p in enumerate(warm):
 trip=rows[3*i:3*i+3];assert [x[0] for x in trip]==[rows[j][0] for j in range(3)]
 for phase,row in enumerate(trip):
  v=np.asarray([float(x) for x in row[1:]]);assert v[0]==i+1 and v[28:35].tobytes()==held.tobytes()
  if phase==2:assert v[14:21].tobytes()==p['q'].tobytes() and v[21:28].tobytes()==p['v'].tobytes() and v[35:42].tobytes()==p['a'].tobytes()
profile=json.loads(a.pin(UNIT/'profile-version1/active_input.json'));consts=json.loads(a.pin(Path('/private/tmp/public_live_affine_v2_integrated_first_cycle_canonical_protocol_repair_v2_20261010/proposed-files/inputs/public_constants.json'),profile['constants']['sha256']))
qr=np.asarray(consts['joint_range']).reshape(7,2);cr=np.asarray(consts['control_range']).reshape(7,2);speed=np.asarray(profile['physical_speed']);r=a.R(a.pin(BASE/'model_open.bin'),'SESSION_STARTUP_VERIFIED_METADATA');metadata=a.metadata(r);r.end();allvalue=0;Ccontacts=0
for cycle in range(3):
 cb=BASE/f'cycle-{cycle}';n=a.nominal(a.pin(cb/'original_nominal.bin'));v=a.candidate_value(a.pin(cb/'candidate_value.bin'));assessment=a.validation(a.pin(cb/'candidate_validation.bin'));assert n['metadata']==metadata
 if cycle==0:assert v['metadata']==metadata
 for p,b in zip(v['points'],assessment['points']):
  assert np.all(p['q']>=qr[:,0]+.005) and np.all(p['q']<=qr[:,1]-.005) and np.all(p['C']>=cr[:,0]+.005) and np.all(p['C']<=cr[:,1]-.005) and np.all(abs(p['v'])<=speed) and a.maxabs(p['w'])<=.0625 and p['control_clips']==p['force_clips']==0
  assert all(np.isfinite(b[k]) for k in ['true','cover','sigma','geometry_lower','sigma_lower','affine_error','trust']) and b['sigma']>=1e-6 and min(b['true'],b['cover'])>=.005
  allvalue+=1
 hint=a.parse_current_hint(a.pin(cb/'current_numeric_hint.bin'));red=a.reduction(a.pin(cb/'qp_equality_reduction.bin'));hx=red['As']@hint['x'];hy=hint['y'];comp=np.where(hy>=0,hy*(red['us']-hx),(-hy)*(hx-red['ls']));assert a.maxabs(comp)<1e-10
 r=a.R(a.pin(cb/'actual_commit.bin'),'TWO_REAL_2MS_HELD_TARGET_COMMIT_OR_RETAINED_PARTIAL_V1');commit=a.commit_record(r);r.end()
 for p in commit['points']:assert np.all(abs(p['v'])<=speed) and np.all(p['q']>=qr[:,0]+.005) and np.all(p['q']<=qr[:,1]-.005);Ccontacts+=p['contacts']
plan=json.loads(a.pin(PACK/'phase5_geometry_qp_runtime_profile_v2_20261011/active_run_plan.json'));runtime_in=a.pin(UNIT/'profile-version1/active_input.json');producer=json.loads(a.pin(UNIT/'profile-version1/PRODUCER.json'));dispatch=json.loads(a.pin(RUN/'BATCH_PREFIX.json'));release=json.loads(a.pin(PACK/'ROOT_ONE_GEOMETRY_THREE_CYCLE_RELEASE.json'))
assert dispatch['records'][0]['argv']==release['exact_argv']==plan['compile_argv'][0] and dispatch['records'][0]['argv'][2]==hashlib.sha256(runtime_in).hexdigest() and dispatch['records'][0]['argv'][3]==producer['sha256']
actualpins=json.loads(a.pin(RUN/'BEFORE_INPUT_IDENTITIES.json'));assert len(actualpins)==len(plan['input_files'])==1701
for observed,expected in zip(actualpins,plan['input_files']):
 for key in ['requested_path','bytes','sha256']:assert observed[key]==expected[key]
 if 'resolved_path' in expected:assert observed['resolved_path']==expected['resolved_path']
assert a.pin(RUN/'BEFORE_READONLY_ROSTERS.json')==a.pin(RUN/'AFTER_READONLY_ROSTERS.json')
summary=json.loads((OUT/'RESULT.json').read_text());walls=np.array([c['timing']['wall'] for c in summary['cycles']]);quant=np.quantile(walls,[.5,.95,.99,1],method='linear');assert sum(c['binary_receipts']['files'] for c in summary['cycles'])+summary['root_binary_receipts']['files']==56
facts=summary['bootstrap'];assert facts==[1,2,1,1016,1014,2040,8,1006,3]
# getstate: warm2000; observations2x8; each validation1+commit entry1+two halves2 each; geometry pre/post2 percycle.
assert facts[5]==2000+2*8+3*(1+1+2*2)+3*2
result={'input_packet_sha256':sha(ready),'all56_binary_receipts':True,'warm1000_values_match_actual_boundary':True,'warm3000_journal_rows':3000,'warmup_derivatives_startup_excluded':{'max_a':maxa,'max_available_jerk':maxj,'first_jerk_available':warm[0]['ja']},'all1200_value_q_v_C_w_bounds_and_geometry_stored_fields_checked':allvalue,'all6_actual_joint_speed_and_position_checked':True,'source6_predictive_step_calls_not_per_ctor':True,'actual_contacts':Ccontacts,'recorded_driver_exact_release':True,'readonly_rosters_before_after_equal':True,'native_facts':facts,'wall_three_sample_descriptive_linear_quantiles':{'p50':float(quant[0]),'p95':float(quant[1]),'p99':float(quant[2]),'max':float(quant[3]),'misses':3,'samples':3},'scope':'No actual current/new optimizer or Model/native calls; saved geometry counts/minima are not per-query raw witness retention or continuous physical certificate.'}
for path,(n,h) in inputs.items():p=Path(path);assert p.stat().st_size==n and sha(p)==h
(OUT/'SUPPLEMENT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

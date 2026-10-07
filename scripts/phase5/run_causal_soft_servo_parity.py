#!/usr/bin/env python3
import copy,datetime,hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np,yaml
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/causal-soft-servo-cpp-v1';base.mkdir(exist_ok=False);ref=p/'results/phase5/development/causal-soft-servo-cpp-reference-v1';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
ready=json.loads((ref/'READY.json').read_text())
for name in ['oracle.json','MODEL_SNAPSHOT.json','SOURCE_SNAPSHOT.py']:assert sha(ref/name)==ready['files'][name]['sha256']
assert ready['source_sha256']=='c63f524d2002323ca635574addcf8ef04a498154ea171ac5a58deda088853710'
assert ready['frozen_model_sha256']=='984ee85d086aeba7da8260a20b21b301e23dfd2c698a6c61ace0ff956bbec1bb'
oracle=json.loads((ref/'oracle.json').read_text());real=json.loads((ref/'MODEL_SNAPSHOT.json').read_text())
# Exact separate n1 algebraic fixture published by root; no fit or new oracle run.
synthetic={'mass_effective_kg_m2':[.2],'bias_Nm':[.01],'public_parameters':{'kp_Nm_rad':[1000.],'damping_Nm_s_rad':[100.],'friction_bound_Nm':[.3],'impedance':[.9],'reference_decay_s_inv':[100.]},'local_box':{'q_min':[-.01],'q_max':[.01],'v_abs_max':.05,'target_error_min':[-.001],'target_error_max':[.001]}}
cases=[{k:c[k] for k in ['name','initial','controls','mesh_s']}|{'model':synthetic if c['n']==1 else real} for c in oracle['cases']]
rejections=[];c=cases[1];n=7
for name,index,value in [('initial_q',0,real['local_box']['q_max'][0]+.001),('initial_v',n,real['local_box']['v_abs_max']+.001),('initial_error',2*n,c['initial'][0]+real['local_box']['target_error_max'][0]+.001),('initial_progress_speed',4*n+1,.3),('initial_progress_position',4*n,1.1)]:
 z=c['initial'].copy();z[index]=value;rejections.append({'name':name,'model':real,'initial':z,'control':[0.]*(n+1),'mesh_s':.004})
for name,index in [('next_target_error',0),('next_progress_speed',n)]:
 u=[0.]*(n+1);u[index]=1000.;rejections.append({'name':name,'model':real,'initial':c['initial'],'control':u,'mesh_s':.004})
for h in [.041,0.,-.004]:rejections.append({'name':'invalid_mesh_'+str(h),'model':real,'initial':c['initial'],'control':[0.]*(n+1),'mesh_s':h})
fixture=base/'input.yaml';fixture.write_text(yaml.safe_dump({'cases':cases,'rejection_cases':rejections},sort_keys=False))
binary=p/'build-causal-soft-servo-v1/causal_soft_servo_probe';sources=[p/'tools/phase5_causal_servo/causal_soft_servo.hpp',p/'tools/phase5_causal_servo/causal_soft_servo_probe.cpp',p/'tools/phase5_causal_servo/CMakeLists.txt',Path(__file__),p/'build-causal-soft-servo-v1/CMakeCache.txt',binary,fixture]+list(ref.iterdir())
freeze={'before_probe_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{str(f):sha(f) for f in sources},'comparison_threshold':5e-12,'scope':'Causal frozen local model and derivatives/mesh sensitivities only; no fitting, root oracle regeneration, native QP, plant or main MPC integration'}
(base/'frozen.json').write_text(json.dumps(freeze,indent=2)+'\n')
proc=subprocess.run([str(binary),str(fixture),str(base/'actual.json')],capture_output=True,text=True);(base/'stdout.log').write_text(proc.stdout);(base/'stderr.log').write_text(proc.stderr)
failures=[];reports=[]
if proc.returncode:failures.append({'reason':'probe failed','return_code':proc.returncode,'stderr':proc.stderr})
else:
 actual=json.loads((base/'actual.json').read_text())
 for a,e in zip(actual['cases'],oracle['cases']):
  assert a['name']==e['name'];errors={}
  for k in ['states','cell_A','cell_B','cell_defect','condensed_offsets','control_sensitivities','initial_sensitivities']:
   av,ev=np.array(a[k]),np.array(e[k]);assert av.shape==ev.shape;errors[k]=float(np.max(abs(av-ev)))
  assert len(a['history'])==len(e['history']);branch_equal=all(x['branches_2ms']==y['branches_2ms'] for x,y in zip(a['history'],e['history']));history_error=max(float(np.max(abs(np.array(x['state'])-y['state']))) for x,y in zip(a['history'],e['history']));time_error=max(abs(x['time_s']-y['time_s']) for x,y in zip(a['history'],e['history']));errors['all_cycle_states']=history_error;errors['clock']=time_error
  if not branch_equal or max(errors.values())>5e-12:failures.append({'case':a['name'],'reason':'parity threshold or branch mismatch'})
  reports.append({'case':a['name'],'n':e['n'],'duration_s':e['duration_s'],'cells':len(e['mesh_s']),'actual4ms_cycles':len(a['history']),'physical2ms_steps':2*len(a['history']),'errors':errors,'all_branches_equal':branch_equal,'clip_equalities':a['clip_equalities']})
 if len(actual['rejections'])!=10 or not all(x['rejected'] for x in actual['rejections']):failures.append({'reason':'domain or mesh negative control accepted'})
unchanged=all(sha(f)==h for f,h in freeze['files'].items());assert unchanged
report={'gate':'PASS_ISOLATED_CAUSAL_SOFT_CPP_PARITY' if not failures else 'FAIL_RETAINED','root_oracle_sha256':sha(ref/'oracle.json'),'root_source_sha256':ready['source_sha256'],'model_sha256':ready['frozen_model_sha256'],'cases':reports,'rejections':actual['rejections'] if not proc.returncode else [],'failures':failures,'source_binary_inputs_unchanged':unchanged,'scope':'Model-only local transition/Jacobian/cell defect/condensed sensitivities parity; no current code cost or lifted-state elimination implementation claim, no FD rerun or new oracle, no physical/command limit enforcement or solver guard integration; initial/full forecast frozen domain checked; no Phase5 acceptance'}
(base/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(failures))

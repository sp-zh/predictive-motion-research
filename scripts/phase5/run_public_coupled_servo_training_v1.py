#!/usr/bin/env python3
"""Freeze public-only baseline, cross-check root fixtures and score TRAIN only."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import csv,datetime,hashlib,importlib,json,subprocess,sys,time
from collections import Counter
from pathlib import Path
import numpy as np
import pinocchio as pin
from public_coupled_servo_v1 import PublicServo
from coupled_friction_box_v1 import solve_box

p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/public-coupled-servo-v1-training';base.mkdir(exist_ok=False)
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-identification-v1-training/raw.csv');assert sha(raw)=='ab9d14efa1a5886c0683db25345f24d5cacd55343e2768eb60536fa180a11dce'
scene=p/'experiments/generated/inspection/scene.xml';xml=scene.with_name('inspection_fr3.xml');reader=p/'build-public-coupled-servo-v1/public_servo_constants'
constants=json.loads(subprocess.check_output([str(reader),str(scene)],text=True));(base/'public_constants.json').write_text(json.dumps(constants,indent=2)+'\n')
model=PublicServo(xml,constants)
ref=p/'results/phase5/development/public-coupled-servo-v1-reference';ready=json.loads((ref/'READY.json').read_text());assert sha(ref/'oracle.json')==ready['files']['oracle.json']['sha256']=='54fffcd5332425530d3110d9cd6db44bb520c64eeca381a30e59c0544cde2e18'
protocol={'status':'FROZEN_PUBLIC_BASELINE_NOT_ACCEPTED','no_calibration':True,'training_seed':91011,'forbidden_fit_inputs':'Any seen91012/v3 or evaluation/final outputs','dt_s':.002,'control_dt_s':.004,'equations':'M(q)=symmetrized upper CRBA(inspection MJCF), armature already included; tau=clipped affine actuator minus passive damping*v minus full rigid-body bias; W=M^-1; H=W+diag(R),ell=W*tau+B*v; coupled box force solves H/ell with original KKT; v+=h solve(M+hD,tau+f),q+=h v_next','static_R':'max(mjMINVAL,(1-d)/d*static compiled dof_invweight0); not current diag(W) or fitted masses','force_derivative_contract':'Integrator D=passive_damping-bias_velocity stays full even at actuator/joint force clamp; distinct from ordinary derivative of clipped force. No transition derivatives implemented.','assumptions':'Seven instantaneous joint affine actuators; zero contact/limit/equality constraints; no applied/unknown/fluid/spring/gravity-comp forces. Parser/runtime mismatch and finite engine termination are possible sources of error. Model forecasts own q/v only.','window_contract':'Each complete4ms-aligned start takes actual past/start q_before/v_before once. Future accepted target sequence is recorded conditional input only. No future observed physical q/v resets. Score final model state against actual q_post/v_post after each2/4/40/800ms window; retain every full active window including stopping. Warmup starts reported separately.','horizons':[{'substeps':n,'q_limit_rad':1e-6 if n<3 else 1e-4,'v_limit_rad_s':1e-4 if n<3 else 1e-3} for n in [1,2,20,400]],'box_KKT_tolerance':1e-10,'box_max_iterations':100,'root_force_fixture_tolerance':5e-10,'model_domain':'Only contact/limit-free public rigid-body calculation, strict joint ranges and finite inputs; no validated accuracy box or physics/command safety guarantee','numerical_threads':1}
(base/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
ext=Path(importlib.import_module('pinocchio.pinocchio_pywrap_default').__file__)
files=[Path(__file__),p/'scripts/phase5/public_coupled_servo_v1.py',p/'scripts/phase5/coupled_friction_box_v1.py',p/'tools/phase5_public_servo_constants/public_servo_constants.cpp',reader,scene,xml,raw,base/'public_constants.json',base/'protocol.json',ref/'oracle.json',ref/'READY.json',ext,Path(pin.__file__),p/'.vendor/mujoco-3.3.7/lib/libmujoco.so.3.3.7',Path('/opt/ros/jazzy/include/pinocchio/src/algorithm/crba.hxx')]
ldd=subprocess.check_output(['ldd',str(ext)],text=True);(base/'native_dependencies.txt').write_text(ldd)
for line in ldd.splitlines():
 parts=line.split();candidate=next((Path(x) for x in parts if x.startswith('/') and Path(x).is_file()),None)
 if candidate:files.append(candidate)
freeze={'frozen_before_training_prediction_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{str(f):sha(f) for f in files},'pinocchio_version':pin.__version__,'numpy_version':np.__version__,'scope':protocol['status'],'training_raw_sha256':sha(raw),'no_mjData_forward_step_or_validation_raw':True}
(base/'frozen.json').write_text(json.dumps(freeze,indent=2)+'\n')
oracle=json.loads((ref/'oracle.json').read_text());fixture_checks=[]
for case in oracle['fixtures']:
 force,info=solve_box(oracle['original_H'],case['ell'],oracle['friction_bounds']);error=float(np.max(abs(force-np.array(case['force']))));fixture_checks.append({'name':case['name'],'force_error':error,**info})
 assert error<=5e-10 and info['original_KKT']<=1e-10
(base/'root_fixture_checks.json').write_text(json.dumps(fixture_checks,indent=2)+'\n')
rows=list(csv.DictReader(raw.open()));assert all(int(r['substep'])==i%2+1 for i,r in enumerate(rows));assert all(int(r['tick'])==i//2 for i,r in enumerate(rows))
def data(prefix):return np.array([[float(r[prefix+str(j)]) for j in range(7)] for r in rows])
q,v,c,qpost,vpost=[data(k) for k in ['q_before_','v_before_','target_','q_post_','v_post_']]
assert np.array_equal(c[::2],c[1::2]);active=np.array([r['phase']!='warmup' for r in rows]);contacts=np.array([int(r['contacts']) for r in rows]);metrics=[];failures=[];global_branches=Counter();max_kkt=0.;max_iterations=0;clamps=Counter();last_update=time.monotonic()
for horizon in protocol['horizons']:
 count=horizon['substeps'];starts=list(range(0,len(rows)-count+1,2));accumulators={kind:{'windows':0,'completed':0,'max_q':0.,'max_v':0.,'sum_q2':0.,'sum_v2':0.,'worst_q':None,'worst_v':None,'failed':0} for kind in ['active','warmup']}
 for number,i in enumerate(starts):
  kind='active' if active[i] else 'warmup';a=accumulators[kind];a['windows']+=1;qp,vp=q[i].copy(),v[i].copy()
  try:
   if np.any(contacts[i:i+count]):raise ValueError('recorded contact invalidates contact-free scoring regime')
   for k in range(count):
    qp,vp,info=model.step(qp,vp,c[i+k]);max_kkt=max(max_kkt,info['original_KKT']);max_iterations=max(max_iterations,info['iterations']);global_branches.update(info['branches']);clamps['controls']+=info['control_clips'];clamps['forces']+=info['force_clips']
   eq,ev=abs(qp-qpost[i+count-1]),abs(vp-vpost[i+count-1]);a['completed']+=1;a['sum_q2']+=float(np.sum(eq**2));a['sum_v2']+=float(np.sum(ev**2))
   if eq.max()>a['max_q']:a['max_q']=float(eq.max());a['worst_q']={'start_tick':int(rows[i]['tick']),'joint_index':int(eq.argmax()),'phase':rows[i]['phase']}
   if ev.max()>a['max_v']:a['max_v']=float(ev.max());a['worst_v']={'start_tick':int(rows[i]['tick']),'joint_index':int(ev.argmax()),'phase':rows[i]['phase']}
  except Exception as e:a['failed']+=1;failures.append({'horizon_s':count*.002,'start_tick':int(rows[i]['tick']),'phase':rows[i]['phase'],'type':type(e).__name__,'reason':str(e)})
  if time.monotonic()-last_update>20:print(json.dumps({'progress_horizon_s':count*.002,'starts_done':number+1,'starts_total':len(starts),'failed_windows_so_far':len(failures)}),flush=True);last_update=time.monotonic()
 for kind,a in accumulators.items():
  denominator=7*a['completed'];record={'scope':kind,'duration_s':count*.002,'windows':a['windows'],'completed_windows':a['completed'],'failed_windows':a['failed'],'max_q_error_rad':a['max_q'],'max_v_error_rad_s':a['max_v'],'rmse_q_rad':float(np.sqrt(a['sum_q2']/denominator)) if denominator else None,'rmse_v_rad_s':float(np.sqrt(a['sum_v2']/denominator)) if denominator else None,'q_limit_rad':horizon['q_limit_rad'],'v_limit_rad_s':horizon['v_limit_rad_s'],'q_worst':a['worst_q'],'v_worst':a['worst_v'],'passed':a['failed']==0 and a['max_q']<=horizon['q_limit_rad'] and a['max_v']<=horizon['v_limit_rad_s']};metrics.append(record)
 print(json.dumps({'completed_horizon_s':count*.002,'metrics':metrics[-2:]}),flush=True)
 (base/'metrics.partial.json').write_text(json.dumps(metrics,indent=2)+'\n');(base/'failures.partial.json').write_text(json.dumps(failures,indent=2)+'\n')
assert all(sha(f)==h for f,h in freeze['files'].items())
result={'gate':'PASS_PUBLIC_COUPLED_TRAINING_ONLY' if all(m['passed'] for m in metrics if m['scope']=='active') else 'FAIL_PUBLIC_COUPLED_TRAINING_RETAINED','scope':'Uncalibrated public-only surrogate; TRAIN91011, not holdout/controller/Phase5 acceptance. Original scalar failures untouched.','metrics':metrics,'failures':failures,'phase_rows':dict(Counter(r['phase'] for r in rows)),'root_fixture_checks':fixture_checks,'prediction_evaluations_branch_counts':dict(global_branches),'max_original_force_QP_KKT':max_kkt,'max_force_QP_iterations':max_iterations,'predicted_force_control_clips':dict(clamps),'input_hashes_unchanged':True,'physical_future_state_resets':False,'all_complete_active_windows_retained':True,'overlapping_windows_not_independent_trials':True,'public_parameter_calibration':False}
(base/'training_report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if result['gate'].startswith('PASS') else 1)

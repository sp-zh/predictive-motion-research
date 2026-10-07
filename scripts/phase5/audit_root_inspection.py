#!/usr/bin/env python3
"""Independent recorded-state audit of FR3 inspection diagnostics.

Requires NumPy. No production controller, Pinocchio or plant APIs are called.
This checks recorded samples, not continuous physical safety or real-time.
"""
import argparse,csv,hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.phase4.audit_root_csv import prepare_model,residual_norms,quaternion_rotation

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--raw',type=Path,required=True);p.add_argument('--protocol',type=Path,required=True)
p.add_argument('--urdf',type=Path,required=True);p.add_argument('--reference',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--method',choices=['predictive','reactive_qp'],required=True)
p.add_argument('--current-command-guard',type=float,required=True);a=p.parse_args()
if not np.isfinite(a.current_command_guard) or a.current_command_guard<=0:p.error('Invalid current command guard')
if a.output.exists():p.error('Refuse audit overwrite')
rows=list(csv.DictReader(a.raw.open()))
if not rows:p.error('Empty raw file')
cfg=json.loads(a.protocol.read_text())['config'];ref=json.loads(a.reference.read_text())
fk,lo,hi=prepare_model(a.urdf);dt=cfg['control_dt_s'];subdt=cfg['physics_substep_s']
def col(name):return np.array([float(r[name]) for r in rows])
def mat(prefix):return np.column_stack([col(prefix+str(i)) for i in range(7)])
q,v,target,vc=mat('q_post_'),mat('dq_post_'),mat('q_accepted_'),mat('dq_accepted_')
requested_v=mat('dq_requested_')
ca,cj,pa,pj=mat('command_acc_'),mat('command_jerk_'),mat('physical_acc_'),mat('physical_jerk_')
sub,t,tick=col('substep'),col('time_s'),col('tick');physical=sub>0
evaluation_start_tick=round(cfg['warmup_s']/dt)
active=physical&(tick>=evaluation_start_tick);checks={}
def count(name,condition):checks[name]=int(np.count_nonzero(condition))
scalar_names=['time_s','tick','substep','s','r','b','contacts','true_clearance_m','euclidean_position_m','se3_translation_m','rotation_rad','sigma_min','command_age_s']
if 'plan_origin_age_s' in rows[0]:scalar_names.append('plan_origin_age_s')
count('nonfinite_recorded_scalars',~np.isfinite(np.column_stack([col(name) for name in scalar_names])).all(axis=1))
count('nonfinite_state_command',~np.isfinite(np.hstack([q,v,target,vc,ca,cj,pa,pj])).all(axis=1))
count('urdf_position_bounds',((q<lo-1e-6)|(q>hi+1e-6)).any(axis=1))
count('accepted_urdf_position_margin',active&((target<lo+cfg['position_margin_rad']-1e-6)|(target>hi-cfg['position_margin_rad']+1e-6)).any(axis=1))
count('contact_rows',col('contacts')!=0)
count('reported_clearance_violation',col('true_clearance_m')<cfg['collision_safe_m']-1e-7)
urdf=ET.parse(a.urdf).getroot();physical_velocity=np.array([float(urdf.find(f"joint[@name='fr3_joint{i}']/limit").get('velocity')) for i in range(1,8)])
count('urdf_velocity_bounds',active&(np.abs(v)>physical_velocity+1e-6).any(axis=1))
count('accepted_velocity_cap',active&(np.abs(vc)>cfg['command_velocity_rad_s']+1e-6).any(axis=1))
unit_tolerance=cfg['solver_acceptance_tolerance']
count('command_acceleration_bound',active&(np.abs(ca)>cfg['command_acceleration_rad_s2']+unit_tolerance+1e-8).any(axis=1))
count('command_jerk_bound',active&(np.abs(cj)>cfg['command_jerk_rad_s3']+unit_tolerance+1e-8).any(axis=1))
count('physical_acceleration_bound',active&(np.abs(pa)>cfg['executed_acceleration_rad_s2']+1e-6).any(axis=1))
count('physical_jerk_bound',active&(np.abs(pj)>cfg['executed_jerk_rad_s3']+1e-6).any(axis=1))
count('progress_domain',((col('s')<-1e-9)|(col('s')>1+1e-9)))
count('progress_speed_domain',((col('r')<-1e-9)|(col('r')>cfg['progress_speed']+1e-9)))
count('progress_acceleration_bound',active&(np.abs(col('b'))>cfg['progress_acceleration']+1e-9))
idx=np.flatnonzero(physical)
count('time_step_mismatch',np.abs(np.diff(t[idx])-subdt)>1e-9)
count('physical_acc_reconstruction',np.max(np.abs(np.diff(v[idx],axis=0)/subdt-pa[idx[1:]]),axis=1)>1e-6)
count('physical_jerk_reconstruction',np.max(np.abs(np.diff(pa[idx],axis=0)/subdt-pj[idx[1:]]),axis=1)>1e-6)
count('progress_speed_reconstruction',np.abs(np.diff(col('r')[idx])-subdt*col('b')[idx[1:]])>1e-10)
count('progress_position_reconstruction',np.abs(np.diff(col('s')[idx])-subdt*col('r')[idx[:-1]]-.5*subdt**2*col('b')[idx[1:]])>1e-10)
commits=np.flatnonzero(active&(sub==1)&(col('command_issued')!=0))
count('issued_command_age_bounds',((col('command_age_s')[commits]<0)|(col('command_age_s')[commits]>a.current_command_guard+1e-9)))
count('progress_jerk_bound',np.abs((col('b')[commits]-col('b')[commits-1])/dt)>cfg['progress_jerk']+1e-6)
if 'applied_model_acc_0' in rows[0]:
 model=mat('applied_model_acc_');count('applied_model_input_mapping',np.max(np.abs(model[commits]-(vc[commits]-v[commits-1])/dt),axis=1)>1e-6)
count('target_integration',np.max(np.abs(target[commits]-target[commits-1]-dt*vc[commits]),axis=1)>1e-10)
count('command_acc_reconstruction',np.max(np.abs(ca[commits]-(vc[commits]-vc[commits-1])/dt),axis=1)>1e-6)
count('command_jerk_reconstruction',np.max(np.abs(cj[commits]-(ca[commits]-ca[commits-1])/dt),axis=1)>1e-6)
for i in np.flatnonzero(sub==0):
 if i and (t[i]!=t[i-1] or not np.array_equal(q[i],q[i-1])):raise ValueError('No-command record advances state')
stride=25;selected=sorted(set(range(0,len(rows),stride))|{len(rows)-1});max_e=max_log=max_r=0.
rd=quaternion_rotation(ref['quaternion_xyzw']);start=np.array(ref['start']);end=np.array(ref['end'])
for i in selected:
 s=float(rows[i]['s']);desired=(1-s)*start+s*end+np.array([0,ref['lateral_amplitude']*np.sin(2*np.pi*s),ref['vertical_amplitude']*np.sin(np.pi*s)])
 actual,r=fk(q[i]);log,angle=residual_norms(actual,r,desired,rd)
 max_e=max(max_e,abs(np.linalg.norm(actual-desired)-float(rows[i]['euclidean_position_m'])))
 max_log=max(max_log,abs(log-float(rows[i]['se3_translation_m'])))
 max_r=max(max_r,abs(angle-float(rows[i]['rotation_rad'])))
checks['independent_pose']=int(max(max_e,max_log,max_r)>1e-10)
d={'scope':'recorded FR3 inspection samples and pose/derivative consistency; no continuous or hardware safety proof',
 'status':'PASS' if not any(checks.values()) else 'FAIL','raw_rows':len(rows),'physical_samples':len(idx),
 'method':a.method,'evaluation_start_tick':evaluation_start_tick,'active_definition':'physical rows after frozen protocol warmup, independent of replay phase label','command_numeric_envelope':{'policy':'explicit acceleration/jerk SI rows, unchanged original row acceptance; does not infer whole-cycle age','unit_tolerance':unit_tolerance,'current_command_guard_s':a.current_command_guard},'bounds_scope':'URDF position/velocity and protocol command caps; exact MJCF intersection/virtual controller limits require additional explicit metadata',
 'issued_nonwarmup_commands':len(commits),
 'issued_commands_with_solved_predictive_plan':sum(a.method=='predictive' and rows[i]['phase']=='path' and rows[i]['status']=='SOLVED' for i in commits),
 'unmodified_predictive_commands':int(sum(a.method=='predictive' and rows[i]['phase']=='path' and rows[i]['status']=='SOLVED' and np.max(np.abs(vc[i]-requested_v[i]))<=1e-6 for i in commits)),
 'checked_pose_samples':len(selected),'checks':checks,
 'max_euclidean_error':max_e,'max_se3_error':max_log,'max_rotation_error':max_r,'numpy_version':np.__version__,
 'inputs_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [a.raw,a.protocol,a.urdf,a.reference,Path(__file__)]}}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({k:v for k,v in d.items() if k!='inputs_sha256'},indent=2))
raise SystemExit(0 if d['status']=='PASS' else 1)

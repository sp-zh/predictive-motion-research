from pathlib import Path
import csv,json,math,hashlib,sys,xml.etree.ElementTree as ET
import numpy as np
import yaml
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('/home/codextransfer/predictive_motion')
result=root/'results/phase4/frozen-v4';freeze=json.loads((result/'frozen.json').read_text())
progress=json.loads((result/'progress.json').read_text());cfg=freeze['config'];dt=cfg['period_s'];subdt=cfg['physics_substep_s']
if len(progress)!=20:raise SystemExit('Wait for all 20 trials')
for name,digest in freeze['files'].items():
    if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Frozen input changed: '+name)
urdf=ET.parse(root/'models/fr3/fr3_arm.urdf').getroot();low=[];high=[]
for i in range(1,8):
    lim=urdf.find(f"joint[@name='fr3_joint{i}']/limit");low.append(float(lim.get('lower')));high.append(float(lim.get('upper')))
low=np.array(low);high=np.array(high)
checks=[];all_rows=0;overall={'contacts':0,'state_nonfinite':0,'position_violations':0,'velocity_violations':0,
                          'command_acceleration_violations':0,'command_jerk_violations':0,'executed_acceleration_violations':0,'executed_jerk_violations':0,
                          'derivative_mismatches':0,'accepted_stale_commands':0,'observer_alignment_violations':0,'clearance_violations':0}
def vector(row,prefix):return np.array([float(row[f'{prefix}{i}']) for i in range(1,8)])
for entry in progress:
    path=Path(entry['raw_file']);counts=dict.fromkeys(overall,0);count=0;previous_dq=None;previous_acc=None;last_tick=None
    previous_cmd=np.zeros(7);previous_cmd_acc=np.zeros(7);timings=[];rows_path=0
    minclear=math.inf;maxcmdacc=maxcmdjerk=maxexecacc=maxexecjerk=0.0;max_derivative_error=0.0;previous_time=None
    with path.open() as handle:
        for row in csv.DictReader(handle):
            count+=1;time=float(row['time_s']);tick=int(row['tick']);sub=int(row['substep']);phase=row['phase']
            q=vector(row,'q_post_');dq=vector(row,'dq_post_');qcmd=vector(row,'q_accepted_');vcmd=vector(row,'dq_accepted_')
            acc=vector(row,'executed_acc_');jerk=vector(row,'executed_jerk_');cmdacc=vector(row,'command_acc_');cmdjerk=vector(row,'command_jerk_')
            if not all(np.isfinite(v).all() for v in [q,dq,qcmd,vcmd,acc,jerk,cmdacc,cmdjerk]):counts['state_nonfinite']+=1
            if sub and previous_time is not None and abs(time-previous_time-subdt)>1e-9:raise RuntimeError('Physical substep time gap')
            previous_time=time
            if sub and previous_dq is not None:
                e=max(np.max(np.abs(acc-(dq-previous_dq)/subdt)),np.max(np.abs(jerk-(acc-previous_acc)/subdt)))
                max_derivative_error=max(max_derivative_error,float(e));counts['derivative_mismatches']+=int(e>1e-6)
            if sub:previous_dq=dq;previous_acc=acc
            contacts=int(row['contacts']);counts['contacts']+=contacts;clear=float(row['true_clearance_m']);minclear=min(minclear,clear)
            counts['clearance_violations']+=int(clear<cfg['collision_safe_m']-1e-7)
            counts['observer_alignment_violations']+=int(float(row['fk_error'])>1e-8 or float(row['frame_error'])>1e-8)
            if phase=='warmup':continue
            rows_path+=1
            counts['position_violations']+=int((q<low-1e-6).any() or (q>high+1e-6).any() or (qcmd<low+cfg['position_margin_rad']-1e-6).any() or (qcmd>high-cfg['position_margin_rad']+1e-6).any())
            counts['velocity_violations']+=int((np.abs(dq)>np.array(cfg['velocity_rad_s'])+1e-6).any() or np.max(np.abs(vcmd))>cfg['kinematic_trust_step_rad']/dt+1e-6)
            # Propagate the explicitly declared 1e-6 velocity-row acceptance tolerance.
            counts['command_acceleration_violations']+=int(np.max(np.abs(cmdacc))>cfg['command_acceleration_rad_s2']+1e-6/dt+1e-8)
            counts['command_jerk_violations']+=int(np.max(np.abs(cmdjerk))>cfg['command_jerk_rad_s3']+1e-6/(dt*dt)+1e-8)
            if sub:
                counts['executed_acceleration_violations']+=int(np.max(np.abs(acc))>cfg['executed_acceleration_rad_s2']+1e-6)
                counts['executed_jerk_violations']+=int(np.max(np.abs(jerk))>cfg['executed_jerk_rad_s3']+1e-6)
            if tick!=last_tick and sub:
                e=max(np.max(np.abs(cmdacc-(vcmd-previous_cmd)/dt)),np.max(np.abs(cmdjerk-(cmdacc-previous_cmd_acc)/dt)))
                max_derivative_error=max(max_derivative_error,float(e));counts['derivative_mismatches']+=int(e>1e-6)
                previous_cmd=vcmd;previous_cmd_acc=cmdacc;last_tick=tick
                age=float(row['state_age_s']);timings.append(age);counts['accepted_stale_commands']+=int(age>cfg['max_state_age_s'])
            maxcmdacc=max(maxcmdacc,float(np.max(np.abs(cmdacc))));maxcmdjerk=max(maxcmdjerk,float(np.max(np.abs(cmdjerk))))
            maxexecacc=max(maxexecacc,float(np.max(np.abs(acc))));maxexecjerk=max(maxexecjerk,float(np.max(np.abs(jerk))))
    if count!=entry['rows']:raise RuntimeError('Summary/raw row mismatch')
    all_rows+=count
    for k,v in counts.items():overall[k]+=v
    checks.append({'method':entry['method'],'seed':entry['seed'],'split':entry['split'],'rows':count,'postwarmup_rows':rows_path,
                   'counts':counts,'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'minimum_clearance_m':minclear,
                   'max_command_acceleration':maxcmdacc,'max_command_jerk':maxcmdjerk,'max_executed_acceleration':maxexecacc,'max_executed_jerk':maxexecjerk,
                   'max_derivative_reconstruction_error':max_derivative_error,
                   'decision_age_mean_s':float(np.mean(timings)) if timings else None,'decision_age_p95_s':float(np.quantile(timings,.95)) if timings else None,
                   'decision_age_max_s':max(timings) if timings else None,'decision_age_over_4ms_count':sum(t>.004 for t in timings)})
units=[]
for path in (root/'build-phase4-math/predictive_motion_control/test_results/predictive_motion_control').glob('*.gtest.xml'):
    tree=ET.parse(path);cases=tree.findall('.//testcase');units.append({'file':path.name,'actual_cases':len(cases),'failed':len(tree.findall('.//failure'))})
report={'scope':'Phase4 integrated diagnostics only; no final predictive-controller research or hardware guarantee','trials':20,
        'completed':sum(bool(e.get('completed')) for e in progress),'raw_rows':all_rows,'independent_raw_audit':overall,'unit_tests':units,
        'actual_unit_cases':sum(u['actual_cases'] for u in units),'details':checks,'configuration_frozen':True,
        'timing_boundary':'observed-state capture through completed controller candidate validation and before command commit; next physics/observer separately recorded; no actual real-time cycle certification'}
(root/'results/phase4/raw_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='details'},indent=2))
if any(overall.values()) or any(u['failed'] for u in units):raise SystemExit('Audit violation: retain evidence for review')

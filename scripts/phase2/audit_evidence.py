"""Independent offline consistency audit of canonical raw C++ benchmark records."""
import csv
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import yaml

root=Path(__file__).resolve().parents[2]
results=root/'results/phase2'
design=yaml.safe_load((root/'config/phase2.yaml').read_text())
assert (root/'config/phase2.yaml').read_bytes()==(results/'frozen_design.yaml').read_bytes()
selected=yaml.safe_load((results/'selection.yaml').read_text())
assert selected['config_sha256']==hashlib.sha256((root/'config/phase2.yaml').read_bytes()).hexdigest()
assert (root/'config/phase2_weak.yaml').read_bytes()==(results/'frozen_weak_design.yaml').read_bytes()
for path in [root/'build/predictive_motion_control/test_results/predictive_motion_control/ik_test.gtest.xml',root/'build/phase2-math-only/predictive_motion_control/test_results/predictive_motion_control/ik_test.gtest.xml']:
    node=ET.parse(path).getroot()
    assert int(node.attrib['tests'])==7 and int(node.attrib['failures'])==0 and int(node.attrib['errors'])==0
assert json.loads((results/'diagnostics/summary.json').read_text())['status']=='PASS'
replay=[]
for path in (results/'evaluation').iterdir():
    if path.suffix in ('.csv','.yaml'):
        for folder in ['evaluation_final','evaluation_contract_final']:
            other=results/folder/path.name
            if other.exists():
                assert path.read_bytes()==other.read_bytes(),str(other)
                replay.append(dict(original=str(path.relative_to(results)),repeat=str(other.relative_to(results)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(results/'raw_replay_comparison.json').write_text(json.dumps(replay,indent=2)+'\n')
summary={}
total=0
def vec(row,name,n):return [float(row[f'{name}_{i}']) for i in range(n)]
def norm(v):return math.sqrt(sum(x*x for x in v))
for group,expected in [('development',44),('evaluation',12),('weak_direction',6)]:
    folder=results/group
    bounds=list(csv.DictReader((folder/'bounds.csv').open()))
    n=len(bounds);vmax=[float(x['velocity']) for x in bounds];lo=[float(x['lower']) for x in bounds];hi=[float(x['upper']) for x in bounds]
    trials=list(csv.DictReader((folder/'trials.csv').open()));assert len(trials)==expected
    observations=[]
    for trial in trials:
        name=f"{trial['kind']}_{trial['seed']}_{trial['method']}_{float(trial['damping']):.6f}.csv"
        rows=list(csv.DictReader((folder/name).open()));assert len(rows)==int(trial['steps'])==1500
        selection=yaml.safe_load((folder/f"search_{trial['seed']}_selection.yaml").read_text())
        start_index=selection['nominal_index'] if trial['kind']=='nominal' else selection['near_index']
        start=next(row for row in csv.DictReader((folder/f"search_{trial['seed']}.csv").open()) if int(row['index'])==start_index)
        target=vec(start,'q',n);previous=None;counts=[0,0,0];speed_sum=0;rawmax=0;acceptedmax=0;executedmax=0;maxratio=0
        pvalues=[];rvalues=[]
        for row in rows:
            for key,value in row.items():
                if key!='method':assert math.isfinite(float(value)),(name,key,value)
            requested=vec(row,'requested_dq',n);accepted=vec(row,'accepted_dq',n);nexttarget=vec(row,'accepted_q_target',n)
            measured=vec(row,'executed_q',n);speed=vec(row,'executed_dq',n);before=vec(row,'q_before',n)
            assert abs(float(row['time_after'])-float(row['time_before'])-design['period'])<1e-12
            for j in range(n):
                assert abs(accepted[j])<=vmax[j]+1e-10
                assert lo[j]-1e-12<=nexttarget[j]<=hi[j]+1e-12
                assert abs(nexttarget[j]-target[j]-design['period']*accepted[j])<1e-12
                if previous is not None:assert abs(before[j]-previous[j])<1e-12
            target=nexttarget;previous=measured
            velocity_violation=any(abs(speed[j])>vmax[j]+1e-9 for j in range(n))
            position_violation=any(measured[j]<lo[j]-1e-9 or measured[j]>hi[j]+1e-9 for j in range(n))
            assert velocity_violation==bool(int(row['measured_velocity_violation']))
            assert position_violation==bool(int(row['measured_position_violation']))
            counts[0]+=bool(int(row['velocity_intervention'])) or bool(int(row['position_intervention']))
            counts[1]+=velocity_violation;counts[2]+=position_violation
            if not int(row['velocity_intervention']) and not int(row['position_intervention']):assert norm([a-b for a,b in zip(requested,accepted)])<1e-9
            axyz=vec(row,'actual_tcp_xyz',3);dxyz=vec(row,'desired_tcp_xyz',3)
            assert abs(norm([a-b for a,b in zip(axyz,dxyz)])-float(row['position_error']))<1e-12
            aq=vec(row,'actual_tcp_xyzw',4);dq=vec(row,'desired_tcp_xyzw',4)
            assert abs(norm(aq)-1)<1e-12 and abs(norm(dq)-1)<1e-12
            va=aq[:3];vd=dq[:3]
            cross=[va[1]*vd[2]-va[2]*vd[1],va[2]*vd[0]-va[0]*vd[2],va[0]*vd[1]-va[1]*vd[0]]
            rel=[aq[3]*vd[j]-dq[3]*va[j]-cross[j] for j in range(3)]
            angle=2*math.atan2(norm(rel),abs(sum(a*b for a,b in zip(aq,dq))))
            assert abs(angle-float(row['rotation_error']))<1e-11
            rawmax=max(rawmax,max(map(abs,requested)));acceptedmax=max(acceptedmax,max(map(abs,accepted)));executedmax=max(executedmax,max(map(abs,speed)))
            maxratio=max(maxratio,max(abs(speed[j])/vmax[j] for j in range(n)))
            speed_sum+=norm(accepted);pvalues.append(float(row['position_error']));rvalues.append(float(row['rotation_error']))
        assert counts==[int(trial[x]) for x in ('interventions','measured_velocity_violations','measured_position_violations')]
        for key,value in [('mean_position_error',sum(pvalues)/len(rows)),('mean_rotation_error',sum(rvalues)/len(rows)),('peak_position_error',max(pvalues)),('peak_rotation_error',max(rvalues)),('final_position_error',pvalues[-1]),('final_rotation_error',rvalues[-1]),('raw_dq_max',rawmax),('accepted_dq_max',acceptedmax),('executed_dq_max',executedmax)]:
            assert abs(float(trial[key])-value)<1e-10,(name,key)
        if counts[1] or counts[2]:assert trial['code']=='EXECUTED_LIMIT_VIOLATION'
        if group!='weak_direction':assert trial['code']=='COMPLETED'
        objective=sum(pvalues)/len(rows)+design['rotation_length_scale']*sum(rvalues)/len(rows)+design['objective_speed_weight']*speed_sum/len(rows)+design['objective_intervention_weight']*counts[0]/len(rows)
        if trial['code']!='COMPLETED':objective+=design['objective_failure_penalty']
        assert abs(objective-float(trial['objective']))<1e-10
        observations.append(dict(seed=int(trial['seed']),kind=trial['kind'],method=trial['method'],code=trial['code'],measured_max_velocity_ratio=maxratio,raw_dq_max=rawmax,accepted_dq_max=acceptedmax,executed_dq_max=executedmax,interventions=counts[0],measured_velocity_violations=counts[1],mean_position_error=float(trial['mean_position_error']),mean_rotation_error=float(trial['mean_rotation_error']),peak_position_error=max(pvalues),peak_rotation_error=max(rvalues)))
        total+=len(rows)
    summary[group]=observations
summary['audit_status']='PASS'
summary['canonical_tracking_samples']=total
summary['gtest_cases']=7
summary['colcon_aggregate_tests']=8
summary['selection']=selected
(results/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(f'RAW_GUARD_STATE_POSE_SUMMARY_AUDIT_PASS samples={total}')

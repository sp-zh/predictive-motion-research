"""Phase2 correction audit: frozen damping, exact control replay, independent URDF FK."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import yaml
root=Path(__file__).resolve().parents[2]
original=root/'results/phase2';corrected=root/'results/phase2-observation-sync'
# Reuse only the independently written URDF math definitions; no C++/Pinocchio call.
source=(root/'scripts/phase3/audit_evidence.py').read_text()
prefix=source[:source.index('def dataset(')]
namespace={'__file__':str(root/'scripts/phase3/audit_evidence.py')}
exec(compile(prefix,'independent_urdf_definitions','exec'),namespace)
fk=namespace['independent_fk_j'];quatR=namespace['quaternion_rotation']
selected=yaml.safe_load((original/'selection.yaml').read_text())
assert selected['config_sha256']==hashlib.sha256((root/'config/phase2.yaml').read_bytes()).hexdigest()
def load(path):
    header=path.open().readline().strip().split(',');indices=[i for i,name in enumerate(header) if name!='method']
    a=np.loadtxt(path,delimiter=',',skiprows=1,usecols=indices,ndmin=2)
    return {header[i]:a[:,j] for j,i in enumerate(indices)}
def mat(d,name,n):return np.column_stack([d[f'{name}_{i}'] for i in range(n)])
rows_compared=0;fkchecks=0;maxP=0;maxR=0;maxPoseCorrection=0;codes=[];summary={}
for group,count in [('development',44),('evaluation',12),('weak_direction',6)]:
    newfolder=corrected/group;oldfolder=original/group
    oldtrials=list(csv.DictReader((oldfolder/'trials.csv').open()));trials=list(csv.DictReader((newfolder/'trials.csv').open()));assert len(trials)==count
    bounds=list(csv.DictReader((newfolder/'bounds.csv').open()));vmax=np.array([float(row['velocity']) for row in bounds]);lo=np.array([float(row['lower']) for row in bounds]);hi=np.array([float(row['upper']) for row in bounds]);n=len(vmax)
    for oldtrial,trial in zip(oldtrials,trials):
        name=f"{trial['kind']}_{trial['seed']}_{trial['method']}_{float(trial['damping']):.6f}.csv";old=load(oldfolder/name);new=load(newfolder/name);rows=len(new['time_after']);assert rows==int(trial['steps'])==1500
        for key in ('q_before','requested_dq','accepted_dq','accepted_q_target','executed_q','executed_dq','reference_q','desired_twist_body','residual'):
            width=6 if key in ('desired_twist_body','residual') else n
            assert np.array_equal(mat(old,key,width),mat(new,key,width)),(name,key)
        for key in ('time_before','time_after','damping','sigma_min','condition','rank','velocity_intervention','position_intervention','measured_velocity_violation','measured_position_violation'):
            assert np.array_equal(old[key],new[key]),(name,key)
        q=mat(new,'executed_q',n);before=mat(new,'q_before',n);accepted=mat(new,'accepted_dq',n);target=mat(new,'accepted_q_target',n);speed=mat(new,'executed_dq',n)
        assert np.max(np.abs(accepted)-vmax)<1e-9;assert np.min(target-lo)>-1e-12 and np.min(hi-target)>-1e-12
        assert np.max(np.abs(before[1:]-q[:-1]))<1e-12
        assert np.max(np.abs(target[1:]-target[:-1]-.004*accepted[1:]))<1e-12
        vv=np.any(np.abs(speed)>vmax+1e-9,axis=1);pv=np.any((q<lo-1e-9)|(q>hi+1e-9),axis=1)
        assert np.array_equal(vv,new['measured_velocity_violation']) and np.array_equal(pv,new['measured_position_violation'])
        if vv.any() or pv.any():assert trial['code']=='EXECUTED_LIMIT_VIOLATION'
        actualxyz=mat(new,'actual_tcp_xyz',3);desiredxyz=mat(new,'desired_tcp_xyz',3);actualquat=mat(new,'actual_tcp_xyzw',4);desiredquat=mat(new,'desired_tcp_xyzw',4)
        assert np.max(np.abs(np.linalg.norm(actualxyz-desiredxyz,axis=1)-new['position_error']))<1e-12
        v=actualquat[:,3,None]*desiredquat[:,:3]-desiredquat[:,3,None]*actualquat[:,:3]-np.cross(actualquat[:,:3],desiredquat[:,:3]);angle=2*np.arctan2(np.linalg.norm(v,axis=1),np.abs(np.sum(actualquat*desiredquat,axis=1)))
        assert np.max(np.abs(angle-new['rotation_error']))<1e-11
        maxPoseCorrection=max(maxPoseCorrection,float(np.linalg.norm(actualxyz-mat(old,'actual_tcp_xyz',3),axis=1).max()))
        for idx in range(0,rows,25):
            position,rotation,_=fk(q[idx]);pe=float(np.max(np.abs(position-actualxyz[idx])));re=float(np.max(np.abs(rotation-quatR(actualquat[idx]))));maxP=max(maxP,pe);maxR=max(maxR,re);assert pe<1e-11 and re<1e-11;fkchecks+=1
        rows_compared+=rows;codes.append(dict(seed=int(trial['seed']),kind=trial['kind'],method=trial['method'],original=oldtrial['code'],corrected=trial['code']))
    summary[group]=trials
contract=list(csv.DictReader((corrected/'observation_contract.csv').open()));assert len(contract)==200 and all(row['integration_state_unchanged']=='1' and row['replay_identical']=='1' for row in contract)
reranking=yaml.safe_load((corrected/'corrected_development_ranking.yaml').read_text())
result=dict(status='PASS',canonical_samples=rows_compared,independent_fk_checks=fkchecks,independent_fk_position_max=maxP,independent_fk_rotation_matrix_max=maxR,max_position_observation_correction=maxPoseCorrection,original_frozen_selection=selected,diagnostic_corrected_ranking=reranking,historical_damping_used_without_reselection=True,trial_codes=codes,groups=summary)
(corrected/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(f'PHASE2_OBSERVATION_CORRECTION_FROZEN_REPLAY_AND_FK_PASS samples={rows_compared} fk_checks={fkchecks}')

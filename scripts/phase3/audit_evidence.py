"""Offline NumPy/URDF audit independent of the C++ Pinocchio/Eigen implementation."""
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import yaml

root=Path(__file__).resolve().parents[2];results=root/'results/phase3'
design=yaml.safe_load((root/'config/phase3.yaml').read_text());selected=yaml.safe_load((results/'selection.yaml').read_text())
assert (root/'config/phase3.yaml').read_bytes()==(results/'frozen_design.yaml').read_bytes()
assert selected['design_sha256']==hashlib.sha256((root/'config/phase3.yaml').read_bytes()).hexdigest()
assert json.loads((results/'numerical/summary.json').read_text())['status']=='PASS'
robot=yaml.safe_load((root/'src/predictive_motion_kinematics/config/fr3.yaml').read_text())
model=ET.parse(root/'src/predictive_motion_kinematics/config'/robot['urdf']).getroot()
bychild={j.find('child').attrib['link']:j for j in model.findall('joint')}
chain=[];link=robot['tcp_parent_frame']
while link in bychild:
    joint=bychild[link];chain.insert(0,joint);link=joint.find('parent').attrib['link']
def rotation(axis,angle):
    axis=np.asarray(axis,dtype=float);axis/=np.linalg.norm(axis);x,y,z=axis
    cross=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return np.eye(3)+np.sin(angle)*cross+(1-np.cos(angle))*(cross@cross)
def quaternion_rotation(q):
    x,y,z,w=q
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
baseR=quaternion_rotation(robot['base_quaternion_xyzw']);baseP=np.array(robot['base_translation'])
toolR=quaternion_rotation(robot['tcp_quaternion_xyzw']);toolP=np.array(robot['tcp_translation'])
prepared=[]
for joint in chain:
    origin=joint.find('origin');xyz=np.array([float(v) for v in origin.attrib.get('xyz','0 0 0').split()]);rpy=[float(v) for v in origin.attrib.get('rpy','0 0 0').split()]
    R=rotation([0,0,1],rpy[2])@rotation([0,1,0],rpy[1])@rotation([1,0,0],rpy[0])
    axis=joint.find('axis');axis=np.array([float(v) for v in (axis.attrib.get('xyz','1 0 0') if axis is not None else '1 0 0').split()])
    prepared.append((joint.attrib['name'],joint.attrib['type'],xyz,R,axis))
def independent_fk_j(q):
    R=baseR.copy();p=baseP.copy();origins={};axes={};mapping=dict(zip(robot['joint_names'],q))
    for name,kind,xyz,Rorigin,axis in prepared:
        p=p+R@xyz;R=R@Rorigin
        if name in mapping:origins[name]=p.copy();axes[name]=R@axis
        if kind!='fixed':R=R@rotation(axis,mapping.get(name,robot['fixed_joint_positions'].get(name,0)))
    p=p+R@toolP;R=R@toolR
    J=np.zeros((6,len(q)))
    for i,name in enumerate(robot['joint_names']):J[:3,i]=R.T@np.cross(axes[name],p-origins[name]);J[3:,i]=R.T@axes[name]
    return p,R,J
def dataset(path):
    header=path.open().readline().strip().split(',');numeric=[i for i,k in enumerate(header) if k not in ('primary','objective')]
    array=np.loadtxt(path,delimiter=',',skiprows=1,usecols=numeric,ndmin=2)
    return {header[i]:array[:,j] for j,i in enumerate(numeric)}
def matrix(data,name,n):return np.column_stack([data[f'{name}_{i}'] for i in range(n)])
def close(actual,expected,tolerance=1e-10):assert np.max(np.abs(actual-expected))<=tolerance,(np.max(np.abs(actual-expected)),tolerance)
summary={'audit_status':'PASS','groups':{},'independent_kinematic_sample_stride':50};total=0;independent=0;maxleak=0;maxmetricerror=0;illconditioned=0
for group,expected in [('development',104),('evaluation',40)]:
    folder=results/group;bounds=list(csv.DictReader((folder/'bounds.csv').open()));n=len(bounds)
    lo=np.array([float(x['lower']) for x in bounds]);hi=np.array([float(x['upper']) for x in bounds]);vmax=np.array([float(x['velocity']) for x in bounds]);span=hi-lo
    rows=list(csv.DictReader((folder/'trials.csv').open()));assert len(rows)==expected;records=[]
    for trial in rows:
        name=f"{trial['case']}_{trial['reference']}_{trial['seed']}_{trial['objective']}_{float(trial['gain']):.6f}.csv";data=dataset(folder/name);count=len(data['time_after']);assert count==int(trial['steps'])
        for key,v in data.items():assert not np.isnan(v).any(),(name,key)
        if count==0:continue
        q=matrix(data,'q_before',n);executed=matrix(data,'executed_q',n);speed=matrix(data,'executed_dq',n);accepted=matrix(data,'accepted_dq',n);target=matrix(data,'accepted_q_target',n);requested=matrix(data,'requested_dq',n);secondary=matrix(data,'secondary_dq',n);primary=matrix(data,'primary_dq',n);z=matrix(data,'z',n)
        close(data['time_after']-data['time_before'],np.full(count,design['period']),1e-12)
        selection=yaml.safe_load((folder/f"search_{trial['seed']}_selection.yaml").read_text())
        selected_index=selection[trial['case']+'_index']
        start=next(row for row in csv.DictReader((folder/f"search_{trial['seed']}.csv").open()) if int(row['index'])==selected_index)
        close(target[0]-design['period']*accepted[0],np.array([float(start[f'q_{j}']) for j in range(n)]),1e-12)
        assert np.max(np.abs(accepted)-vmax)<1e-9;assert np.min(target-lo)>=-1e-12 and np.min(hi-target)>=-1e-12
        close(q[1:],executed[:-1],1e-12);close(target[1:]-target[:-1],design['period']*accepted[1:],1e-12);close(requested,primary+secondary,1e-12)
        margins=np.minimum((q-lo)/span,(hi-q)/span);close(margins,matrix(data,'normalized_margin',n),1e-12);close(margins.min(axis=1),data['min_normalized_margin'],1e-12)
        hjoint=np.sum(((q-(lo+span*.5))/span)**2,axis=1);gradient=2*(q-(lo+span*.5))/span**2;close(hjoint,data['H_joint'],1e-12);close(np.sum(gradient*secondary,axis=1),data['joint_directional_derivative'],1e-10)
        if trial['objective']=='joint':assert data['joint_directional_derivative'].max()<1e-10
        vv=np.any(np.abs(speed)>vmax+1e-9,axis=1);pv=np.any((executed<lo-1e-9)|(executed>hi+1e-9),axis=1);close(vv,data['measured_velocity_violation'],0);close(pv,data['measured_position_violation'],0)
        interventions=np.logical_or(data['velocity_intervention'],data['position_intervention'])
        assert int(vv.sum())==int(trial['measured_velocity_violations']) and int(pv.sum())==int(trial['measured_position_violations']) and int(interventions.sum())==int(trial['interventions'])
        if vv.any() or pv.any():assert trial['code']=='EXECUTED_LIMIT_VIOLATION'
        xyz=matrix(data,'actual_tcp_xyz',3);desiredxyz=matrix(data,'desired_tcp_xyz',3);close(np.linalg.norm(xyz-desiredxyz,axis=1),data['position_error'],1e-12)
        aq=matrix(data,'actual_tcp_xyzw',4);dq=matrix(data,'desired_tcp_xyzw',4);close(np.linalg.norm(aq,axis=1),np.ones(count),1e-12);close(np.linalg.norm(dq,axis=1),np.ones(count),1e-12)
        relative=aq[:,3,None]*dq[:,:3]-dq[:,3,None]*aq[:,:3]-np.cross(aq[:,:3],dq[:,:3]);angle=2*np.arctan2(np.linalg.norm(relative,axis=1),np.abs(np.sum(aq*dq,axis=1)));close(angle,data['rotation_error'],1e-11)
        pairs={'mean_position_error':data['position_error'].mean(),'mean_rotation_error':data['rotation_error'].mean(),'peak_position_error':data['position_error'].max(),'peak_rotation_error':data['rotation_error'].max(),'final_position_error':data['position_error'][-1],'final_rotation_error':data['rotation_error'][-1],'raw_dq_max':np.abs(requested).max(),'accepted_dq_max':np.abs(accepted).max(),'executed_dq_max':np.abs(speed).max(),'raw_JPz_leakage_max':data['raw_unscaled_JPz_leakage'].max(),'guard_task_distortion_max':data['guard_unscaled_task_distortion'].max(),'gradient_mean_us':data['gradient_us'].mean(),'control_mean_us':data['control_compute_us'].mean(),'control_max_us':data['control_compute_us'].max()}
        for key,value in pairs.items():close(float(trial[key]),value,1e-8)
        initialH=hjoint[0];finalH=np.sum(((executed[-1]-(lo+span*.5))/span)**2);close(initialH,float(trial['initial_H']),1e-12);close(finalH,float(trial['final_H']),1e-12)
        score=design['score_pose_weight']*(pairs['mean_position_error']+design['rotation_length_scale']*pairs['mean_rotation_error'])+design['score_joint_cost_weight']*(float(trial['final_H'])-float(trial['initial_H']))-design['score_sigma_weight']*np.log((float(trial['final_sigma'])+design['log_volume_regularization'])/(float(trial['initial_sigma'])+design['log_volume_regularization']))+design['score_speed_weight']*np.linalg.norm(accepted,axis=1).mean()+design['score_intervention_weight']*interventions.mean()
        if trial['code']!='COMPLETED':score+=design['score_failure_penalty']
        close(score,float(trial['score']),1e-8)
        for idx in range(0,count,50):
            _,_,J=independent_fk_j(q[idx]);scaled=J.copy();scaled[3:]*=design['rotation_length_scale'];u,s,vh=np.linalg.svd(scaled,full_matrices=False);keep=s>design['rank_relative_tolerance']*s[0];P=np.eye(n)-vh[keep].T@vh[keep]
            leak=np.linalg.norm(J@secondary[idx]);maxleak=max(maxleak,leak);close(leak,data['raw_unscaled_JPz_leakage'][idx],1e-9);close(np.linalg.norm(J@(accepted[idx]-requested[idx])),data['guard_unscaled_task_distortion'][idx],1e-8)
            close(np.linalg.norm(J@(accepted[idx]-primary[idx])),data['postguard_task_difference'][idx],1e-8)
            if s[-1]/max(s[0],1e-12)>1e-7:close(P@z[idx],secondary[idx],1e-7)
            else:illconditioned+=1
            for prefix,matrixJ in [('scaled',scaled),('unscaled',J)]:
                singular=np.linalg.svd(matrixJ,compute_uv=False);error=float(np.max(np.abs(singular-np.array([data[f'{prefix}_sigma_{i}'][idx] for i in range(6)]))));maxmetricerror=max(maxmetricerror,error);assert error<1e-11
                close(singular[-1],data[f'{prefix}_sigma_min'][idx],1e-11)
                close(np.exp(np.log(singular).sum()),data[f'{prefix}_manipulability'][idx],1e-11)
                close(np.log(np.hypot(singular,design['log_volume_regularization'])).sum(),data[f'{prefix}_regularized_log_volume'][idx],1e-9)
            pos,rot,_=independent_fk_j(executed[idx]);close(pos,xyz[idx],1e-11);close(rot,quaternion_rotation(aq[idx]),1e-11);independent+=1
        records.append(dict(trial,measured_max_velocity_ratio=float(np.max(np.abs(speed)/vmax)),runtime_p95_us=float(np.quantile(data['control_compute_us'],.95)),runtime_p99_us=float(np.quantile(data['control_compute_us'],.99))))
        total+=count
    summary['groups'][group]=records
summary.update(canonical_tracking_samples=total,independent_kinematic_checks=independent,illconditioned_projection_comparisons_flagged=illconditioned,independent_leakage_max=maxleak,independent_singular_value_error_max=maxmetricerror)
preserved=results/'initial_cached_site_run'
comparisons=[]
if preserved.exists():
    # Ignore corrected post-step pose/error and nondeterministic timing; control/plant states must match.
    for group in ('development','evaluation'):
        for path in (results/group).glob('*.csv'):
            if path.name in ('bounds.csv','trials.csv','tuning.csv') or path.name.startswith('search_'):continue
            original=dataset(preserved/group/path.name);current=dataset(path)
            for key in ('q_before','primary_dq','z','secondary_dq','requested_dq','accepted_dq','accepted_q_target','executed_q','executed_dq','reference_q'):
                assert np.array_equal(matrix(original,key,n),matrix(current,key,n)),(path.name,key)
            comparisons.append(str(path.relative_to(results)))
    assert (results/'selection.yaml').read_bytes()==(results/'corrected_development_selection.yaml').read_bytes()
summary['measurement_correction']=dict(initial_cache_pose_was_pre_last_integration=True,corrected_by_independent_mujoco_kinematics_snapshot=True,control_and_plant_arrays_byte_equal=len(comparisons),frozen_selection_unchanged=True)
(results/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(f'PHASE3_RAW_AND_INDEPENDENT_URDF_AUDIT_PASS samples={total} independent_kinematic_checks={independent}')

#!/usr/bin/env python3
"""Independent scalar box-QP servo replay; no fitting, plant stepping, or production predictor."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
import xml.etree.ElementTree as ET
import yaml

DT=.002;N=7
MODEL_SHA='984ee85d086aeba7da8260a20b21b301e23dfd2c698a6c61ace0ff956bbec1bb'
RAW_SHA='c435bea765c9a12e73bc12d12e2dfa7b6cbb6ddf877f1d519d9056810b21f03c'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def trace(path):
    rows=list(csv.DictReader(path.open()))
    data={p:np.array([[float(r[p+str(j)]) for j in range(N)] for r in rows]) for p in ['q_before_','v_before_','target_','q_post_','v_post_']}
    assert all(np.isfinite(x).all() for x in data.values())
    assert all(int(r['tick'])==i//2 and int(r['substep'])==i%2+1 for i,r in enumerate(rows))
    assert max(abs(float(r['time_s'])-(i+1)*DT) for i,r in enumerate(rows))<1e-8
    assert np.max(abs(data['q_before_'][1:]-data['q_post_'][:-1]))<1e-12
    assert np.max(abs(data['v_before_'][1:]-data['v_post_'][:-1]))<1e-12
    assert np.max(abs(data['target_'][::2]-data['target_'][1::2]))==0
    return rows,data


def parameters(model):
    public=model['public_parameters']
    return [np.array(model[k]) for k in ['mass_effective_kg_m2','bias_Nm']]+[np.array(public[k]) for k in ['kp_Nm_rad','damping_Nm_s_rad','friction_bound_Nm','impedance','reference_decay_s_inv']]


def box_step(q,v,c,params):
    mass,bias,kp,damp,eta,imp,decay=params
    smooth=kp*(c-q)-damp*v+bias
    # Derive force from scalar constrained quadratic, not production clip predictor.
    regularizer=(1-imp)/(imp*mass)
    curvature=1/mass+regularizer
    linear=smooth/mass+decay*v
    unconstrained=-linear/curvature
    force=np.maximum(-eta,np.minimum(eta,unconstrained))
    gradient=curvature*force+linear
    kkt=np.where(force==-eta,np.minimum(gradient,0),np.where(force==eta,np.maximum(gradient,0),gradient))
    vn=v+(smooth+force)*DT/(mass+DT*damp)
    return q+DT*vn,vn,unconstrained,float(np.max(abs(kkt)))


def jacobian(q,v,c,params):
    mass,bias,kp,damp,eta,imp,decay=params
    inside=abs(imp*(kp*(c-q)-damp*v+bias+mass*decay*v))<eta
    gain=DT/(mass+DT*damp)
    x=-gain*kp*(1-imp*inside)
    y=1+gain*(-damp*(1-imp*inside)-mass*decay*imp*inside)
    p=np.block([[np.eye(N)+DT*np.diag(x),DT*np.diag(y)],[np.diag(x),np.diag(y)]])
    b=np.vstack((np.diag(-DT*x),np.diag(-x)))
    return p,b


def derivative_checks(params):
    mass,bias,kp,damp,eta,imp,decay=params
    max_one=max_two=kkt=0.;cases=[]
    for level in [0.,2.,-2.]:
        q=np.zeros(N);v=np.zeros(N);c=(level*eta/imp-bias)/kp
        p1,b1=jacobian(q,v,c,params)
        q1,v1,_,kk=box_step(q,v,c,params);kkt=max(kkt,kk)
        p2,b2=jacobian(q1,v1,c,params)
        composed=np.column_stack((p2@p1,p2@b1+b2))
        first=np.column_stack((p1,b1));h=1e-8
        for j in range(3*N):
            plus=np.r_[q,v,c];minus=plus.copy();plus[j]+=h;minus[j]-=h
            def run(z,count):
                qz,vz=z[:N].copy(),z[N:2*N].copy()
                for _ in range(count):qz,vz,_,_=box_step(qz,vz,z[2*N:],params)
                return np.r_[qz,vz]
            max_one=max(max_one,float(np.max(abs((run(plus,1)-run(minus,1))/(2*h)-first[:,j]))))
            max_two=max(max_two,float(np.max(abs((run(plus,2)-run(minus,2))/(2*h)-composed[:,j]))))
        cases.append({'drive_relative_to_bound':level,'second_step_target_unchanged':True})
    assert max_one<1e-8 and max_two<1e-8 and kkt<1e-12
    return {'synthetic_algebra_scope':True,'cases':cases,'max_2ms_jacobian_fd_error':max_one,'max_4ms_composed_jacobian_fd_error':max_two,'max_box_kkt_error':kkt,'threshold_derivative_policy':'No unique derivative at either exact clip threshold; saturated-side convention is one branch choice only.'}


def public_xml_check(path,model):
    root=ET.parse(path).getroot();defaults={}
    def register(node,parent):
        attributes=dict(parent)
        for child in node.findall('joint'):attributes.update(child.attrib)
        defaults[node.get('class','')]=attributes
        for child in node.findall('default'):register(child,attributes)
    register(root.find('default'),{})
    joints={}
    def walk(body,cls=''):
        cls=body.get('childclass',cls)
        for child in body:
            if child.tag=='joint':
                attrs={**defaults.get(child.get('class',cls),{}),**child.attrib};joints[child.get('name')]=attrs
            elif child.tag=='body':walk(child,cls)
    walk(root.find('worldbody'))
    actuators={child.get('joint'):child.attrib for child in root.find('actuator')}
    actual={k:[] for k in ['kp_Nm_rad','damping_Nm_s_rad','friction_bound_Nm','impedance','reference_decay_s_inv']}
    for name in model['public_parameters']['joint_names']:
        j,act=joints[name],actuators[name]
        imp=[float(x) for x in j.get('solimpfriction','.9 .95 .001 .5 2').split()]
        ref=[float(x) for x in j.get('solreffriction','.02 1').split()]
        for key,value in [('kp_Nm_rad',float(act['kp'])),('damping_Nm_s_rad',float(act['kv'])+float(j.get('damping',0))),('friction_bound_Nm',float(j['frictionloss'])),('impedance',imp[0]),('reference_decay_s_inv',2/(imp[1]*max(ref[0],2*DT)))]:actual[key].append(value)
    discrepancy={k:float(np.max(abs(np.array(v)-model['public_parameters'][k]))) for k,v in actual.items()}
    assert max(discrepancy.values())==0 and root.find('option').get('integrator')=='implicitfast'
    return {'parameter_discrepancies':discrepancy,'integrator':root.find('option').get('integrator'),'compiler_angle':root.find('compiler').get('angle'),'scalar_surrogate_caveat':'Full MuJoCo DOF regularizer uses dof_invweight0 and coupled inverse inertia; equating its scalar approximation to 1/effective_m is a fitted surrogate assumption.'}


def preparation_coverage(raw,box):
    rows=list(csv.DictReader(raw.open()));counts={key:[0]*N for key in ['q','v','target_error']};previous=None;total=0
    for row in rows:
        if row['phase']=='path' and previous is not None:
            total+=1
            for j in range(N):
                q,v,c=float(previous[f'q_post_{j}']),float(previous[f'dq_post_{j}']),float(row[f'q_accepted_{j}']);error=c-q
                counts['q'][j]+=not box['q_min'][j]<=q<=box['q_max'][j]
                counts['v'][j]+=abs(v)>box['v_abs_max']
                counts['target_error'][j]+=not box['target_error_min'][j]<=error<=box['target_error_max'][j]
        previous=row
    return {'raw_sha256':sha(raw),'scope':'Retained v19-full preparation coverage comparison only; no new model performance evaluation or fit','path_substeps':total,'domain_bad_substeps_by_joint':counts}


def replay(rows,a,model,params,report):
    active=np.array([r['phase']!='warmup' for r in rows]);box=model['local_box']
    metrics=[];worst=[];maxdiff=0.;maxkkt=0.;forecast_bad=0;branch_counts=np.zeros((N,3),dtype=int)
    for hi,length in enumerate([1,2,20,400]):
        starts=np.array([i for i in range(0,len(rows)-length+1,2) if active[i]])
        q=a['q_before_'][starts].copy();v=a['v_before_'][starts].copy()
        for step in range(length):
            c=a['target_'][starts+step]
            error=c-q
            if length==400:
                forecast_bad+=int(np.sum(((q<box['q_min'])|(q>box['q_max'])|(abs(v)>box['v_abs_max'])|(error<box['target_error_min'])|(error>box['target_error_max'])).any(1)))
            q,v,u,kk=box_step(q,v,c,params);maxkkt=max(maxkkt,kk)
            if length==400:
                eta=params[4]
                branch_counts[:,0]+=np.sum(u<=-eta,axis=0);branch_counts[:,1]+=np.sum(abs(u)<eta,axis=0);branch_counts[:,2]+=np.sum(u>=eta,axis=0)
        qe=q-a['q_post_'][starts+length-1];ve=v-a['v_post_'][starts+length-1]
        m={'substeps':length,'windows':len(starts),'max_q_error_rad':float(np.max(abs(qe))),'max_v_error_rad_s':float(np.max(abs(ve))),'rmse_q_rad':float(np.sqrt(np.mean(qe*qe))),'rmse_v_rad_s':float(np.sqrt(np.mean(ve*ve)))}
        for key in ['max_q_error_rad','max_v_error_rad_s','rmse_q_rad','rmse_v_rad_s']:maxdiff=max(maxdiff,abs(m[key]-report['metrics'][hi][key]))
        assert len(starts)==report['metrics'][hi]['windows']
        m['passed']=m['max_q_error_rad']<=model['policy']['position_error_limits_rad'][hi] and m['max_v_error_rad_s']<=model['policy']['velocity_error_limits_rad_s'][hi]
        metrics.append(m)
        if length==400:
            for label,e in [('position',qe),('velocity',ve)]:
                i,j=np.unravel_index(np.argmax(abs(e)),e.shape)
                worst.append({'quantity':label,'joint':int(j),'start_tick':int(starts[i])//2,'signed_error':float(e[i,j])})
    q,v,c=(a[k][active] for k in ['q_before_','v_before_','target_']);e=c-q
    domainbad=int(np.sum(((q<box['q_min'])|(q>box['q_max'])|(abs(v)>box['v_abs_max'])|(e<box['target_error_min'])|(e>box['target_error_max'])).any(1)))
    ranges={k:{'min':x.min(0).tolist(),'max':x.max(0).tolist(),'span':np.ptp(x,axis=0).tolist()} for k,x in [('q',q),('v',v),('accepted_target',c),('target_minus_q',e)]}
    assert maxdiff<1e-11 and domainbad==0 and all(m['passed'] for m in metrics)
    return {'metrics':metrics,'max_metric_discrepancy':maxdiff,'max_box_kkt_residual':maxkkt,'measured_active_domain_bad_rows':domainbad,'forecast_domain_bad_window_substeps_800ms':forecast_bad,'forecast_branch_counts_lower_interior_upper_800ms':branch_counts.tolist(),'active_ranges':ranges,'worst_800ms_windows':worst,'phase_counts':{phase:sum(r['phase']==phase for r in rows) for phase in set(r['phase'] for r in rows)}}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();root=args.project
    base=root/'results/phase5/development';directory=base/'servo-model-soft-friction-v2-frozen';mp=directory/'model.json'
    model=json.loads(mp.read_text());assert sha(mp)==MODEL_SHA
    epoch=base/'servo-soft-friction-v2-validation';freeze=json.loads((epoch/'frozen.json').read_text());execution=json.loads((epoch/'execution.json').read_text())
    raw=Path(execution['argv'][-1])/'raw.csv';assert sha(raw)==RAW_SHA==execution['raw_files']['raw.csv']
    assert execution['return_code']==0 and execution['argv'][-2]=='91012'
    assert freeze['files'][str(mp)]==MODEL_SHA==execution['model_prefrozen_sha256']==execution['model_after_run_sha256']
    inputs=[mp,raw,epoch/'frozen.json',epoch/'execution.json',directory/'heldout-validation/validation_report.json',directory/'training_report.json']
    for source in ['servo_model_soft_friction_v2.py','servo_model_soft_friction_v2_test.py','run_servo_soft_validation_v2.py','validate_servo_soft_friction_v2.py','servo_model_v1.py']:
        sp=root/'scripts/phase5'/source;inputs.append(sp);assert sha(sp)==freeze['files'][str(sp)]
    for source in ['tools/phase5_adapter/servo_validation_v2.cpp','config/phase5_development/servo_validation_soft_friction_v2.yaml','experiments/generated/inspection/inspection_fr3.xml','experiments/generated/phase4/robot.yaml']:
        sp=root/source;inputs.append(sp);assert sha(sp)==freeze['files'][str(sp)]
    assert model['training_seed']==91011 and model['training_raw_sha256']=='ab9d14efa1a5886c0683db25345f24d5cacd55343e2768eb60536fa180a11dce'
    assert model['script_sha256']==sha(root/'scripts/phase5/servo_model_soft_friction_v2.py')
    params=parameters(model);assert np.all(params[0]>0) and all(np.isfinite(x).all() for x in params)
    assert all(d['response_jacobian_rank']==2 and not any(d['bound_active']) for d in model['fit_diagnostics'])
    rows,a=trace(raw);report=json.loads((directory/'heldout-validation/validation_report.json').read_text())
    result={'scope':__doc__,'verdict':'PASS_LOCAL_RECORDED_INPUT_PREDICTION','model_sha256_before':sha(mp),'created_utc':model['created_utc'],'validation_frozen_utc':freeze['frozen_before_run_utc'],'replay':replay(rows,a,model,params,report),'derivatives':derivative_checks(params),'oracle_source_sha256':sha(Path(__file__)),'public_sources':['https://github.com/google-deepmind/mujoco/blob/3.3.7/src/engine/engine_core_constraint.c','https://mujoco.readthedocs.io/en/3.3.7/computation/index.html'],'local_box':model['local_box'],'training_ranges':model['training_ranges'],'effective_inertia_not_true_multibody_inertia':True}
    result['public_xml_checks']=public_xml_check(root/'experiments/generated/inspection/inspection_fr3.xml',model)
    config=yaml.safe_load((root/'config/phase5_development/servo_validation_soft_friction_v2.yaml').read_text())
    result['frozen_waveform']={k:config[k] for k in ['validation_frequency_base_hz','validation_frequency_step_hz','validation_phase_step_rad','identification_amplitude_rad','identification_duration_s','validation_waveform_id']}
    assert [config[k] for k in ['validation_frequency_base_hz','validation_frequency_step_hz','validation_phase_step_rad','identification_amplitude_rad','identification_duration_s']]==[.73,.103,.27,.0006,8.]
    oldraw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-identification-v1-validation/raw.csv');inputs.append(oldraw)
    result['old_v1_validation_sha256']=sha(oldraw);assert result['old_v1_validation_sha256']=='3331840951457d0219cc0c461ea1339cead478211727c3ffc8579a7e2f847912'
    prep=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/reference-tracking-v19-full/predictive_inspection_91011/raw.csv');inputs.append(prep);result['previous_preparation_domain_comparison']=preparation_coverage(prep,model['local_box'])
    result['effective_inputs']={str(f):{'sha256':sha(f),'bytes':f.stat().st_size} for f in inputs}
    result['model_sha256_after']=sha(mp);assert result['model_sha256_after']==MODEL_SHA
    args.output.mkdir(parents=True,exist_ok=False);(args.output/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'verdict':result['verdict'],'replay':{k:v for k,v in result['replay'].items() if k not in ['active_ranges','forecast_branch_counts_lower_interior_upper_800ms']},'derivatives':result['derivatives']},indent=2))


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Read-only expanded command/geometry conflict and captured-stop audit; no plant execution."""
import argparse,csv,hashlib,json
from fractions import Fraction
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
import yaml
from scipy.optimize import linprog

N=7;RAW_SHA='b913b712590be96eeec031a0b62a88e42d462ed2ac13d87ddf6b8a5d648a29e2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def qdecimal(value):
    with localcontext() as c:
        c.prec=60
        return str(Decimal(value.numerator)/Decimal(value.denominator))


def numeric(path):
    return np.loadtxt(path,delimiter=',',ndmin=2)


def recover_box(directory,prefix='',row_tolerance=Fraction(0)):
    ar=list(csv.reader((directory/(prefix+'A.csv')).open()))
    lr=[row[0] for row in csv.reader((directory/(prefix+'lower.csv')).open())]
    ur=[row[0] for row in csv.reader((directory/(prefix+'upper.csv')).open())]
    intervals=[];sources=[]
    for j in range(N):
        lower=[];upper=[]
        for i,row in enumerate(ar[:21]):
            coeff=[Fraction(x) for x in row];nz=[k for k,x in enumerate(coeff) if x]
            assert len(nz)==1
            if nz[0]!=j:continue
            a=coeff[j];l,u=Fraction(lr[i])-row_tolerance,Fraction(ur[i])+row_tolerance
            if a>0:lower.append((l/a,i));upper.append((u/a,i))
            else:lower.append((u/a,i));upper.append((l/a,i))
        lo=max(lower);hi=min(upper);assert lo[0]<=hi[0]
        intervals.append((lo[0],hi[0]));sources.append({'joint':j,'lower_row':lo[1],'upper_row':hi[1],'lower_exact_decimal':qdecimal(lo[0]),'upper_exact_decimal':qdecimal(hi[0])})
    witnesses=[]
    labels=list(csv.DictReader((directory/(prefix+'rows.csv')).open()))
    for i,row in enumerate(ar[21:],21):
        a=[Fraction(x) for x in row];support=sum(x*(intervals[j][1] if x>=0 else intervals[j][0]) for j,x in enumerate(a));lower=Fraction(lr[i])-row_tolerance
        # Rational arithmetic proves this positive deficit independent of any solver.
        deficit=lower-support
        if deficit>0:
            corner=[intervals[j][1] if x>=0 else intervals[j][0] for j,x in enumerate(a)]
            witnesses.append({'row':i,'label':labels[i]['label'],'lower_m_s':float(lower),'exact_support_max_m_s':float(support),'exact_positive_gap_m_s':float(deficit),'rational_gap_positive':True,'gap_decimal_60digits':qdecimal(deficit),'maximizing_corner_rad_s':[float(x) for x in corner]})
    return intervals,sources,witnesses


def lp_check(a,l,u):
    finite_l=np.isfinite(l);finite_u=np.isfinite(u)
    result=linprog(np.zeros(N),A_ub=np.vstack((-a[finite_l],a[finite_u])),b_ub=np.r_[-l[finite_l],u[finite_u]],bounds=[(None,None)]*N,method='highs')
    return {'success':bool(result.success),'status':int(result.status),'message':result.message}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--project',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();root=args.project;base=root/'results/phase5/development'
    cases=['servo-expanded-qp-reconstruction-v1','servo-expanded-failure-stop-replay-v1'];rec=base/cases[0]/'reconstruction';stop=base/cases[1]/'replay-stop'
    frozen=[json.loads((base/c/'frozen.json').read_text()) for c in cases];execution=[json.loads((base/c/'execution.json').read_text()) for c in cases]
    raw=Path(execution[0]['argv'][3]);assert sha(raw)==RAW_SHA
    original=list(csv.DictReader(raw.open()));assert len(original)==1708
    inputs=[raw];checks={}
    for case,exe in zip(cases,execution):
        for name,h in exe['output_files'].items():
            p=base/case/name;assert sha(p)==h;inputs.append(p)
        inputs.extend([base/case/'frozen.json',base/case/'execution.json'])
    meta=yaml.safe_load((rec/'reconstruction.yaml').read_text());cfgpath=root/'config/phase5_development/servo_validation_soft_friction_v2_expanded.yaml';cfg=yaml.safe_load(cfgpath.read_text());inputs.append(cfgpath)
    dt=cfg['control_dt_s'];assert dt==.004 and cfg['physics_substep_s']==.002 and int(original[-1]['tick'])==853 and meta['next_tick']==854
    vec=lambda row,p:np.array([float(row[p+str(j)]) for j in range(N)])
    final=original[-1];q,v,c,w,acc=[vec(final,p) for p in ['q_post_','v_post_','target_','command_velocity_','command_acceleration_']]
    for label,value in [('measured_q',q),('measured_v',v),('accepted_target',c),('accepted_velocity',w),('accepted_acceleration',acc)]:assert np.max(abs(value-np.array(meta[label])))==0
    # The derivative-only interval is known from actual accepted histories.
    expected_lo=np.maximum(w-cfg['command_acceleration_rad_s2']*dt,w+dt*acc-cfg['command_jerk_rad_s3']*dt*dt)
    expected_hi=np.minimum(w+cfg['command_acceleration_rad_s2']*dt,w+dt*acc+cfg['command_jerk_rad_s3']*dt*dt)
    a=numeric(rec/'A.csv');l=numeric(rec/'lower.csv').ravel();u=numeric(rec/'upper.csv').ravel();h=numeric(rec/'H.csv');g=numeric(rec/'g.csv').ravel()
    sa=numeric(stop/'stop_A.csv');sl=numeric(stop/'stop_lower.csv').ravel();su=numeric(stop/'stop_upper.csv').ravel();sh=numeric(stop/'stop_H.csv');sg=numeric(stop/'stop_g.csv').ravel()
    intervals,sources,witnesses=recover_box(rec);si,ssources,switnesses=recover_box(stop,'stop_')
    _,_,tolerance_witnesses=recover_box(rec,row_tolerance=Fraction('1e-7'))
    assert len(tolerance_witnesses)==3 and min(w['exact_positive_gap_m_s'] for w in tolerance_witnesses)>1e-3
    boxlo=np.array([float(x[0]) for x in intervals]);boxhi=np.array([float(x[1]) for x in intervals]);assert np.max(abs(boxlo-expected_lo))<1e-15 and np.max(abs(boxhi-expected_hi))<1e-15
    assert intervals==si and len(witnesses)==3
    checks['history_interval_error']=float(max(np.max(abs(boxlo-expected_lo)),np.max(abs(boxhi-expected_hi))))
    derivative_error=0.
    assert np.array_equal(a[:N],np.eye(N)) and np.array_equal(h,np.eye(N))
    for j in range(N):
        i=7+2*j;axis=np.eye(N)[j]
        assert np.array_equal(a[i],axis/dt) and np.array_equal(a[i+1],axis/(dt*dt))
        derivative_error=max(derivative_error,abs(l[i]-(w[j]/dt-cfg['command_acceleration_rad_s2'])),abs(u[i]-(w[j]/dt+cfg['command_acceleration_rad_s2'])),abs(l[i+1]-(w[j]/(dt*dt)+acc[j]/dt-cfg['command_jerk_rad_s3'])),abs(u[i+1]-(w[j]/(dt*dt)+acc[j]/dt+cfg['command_jerk_rad_s3'])))
    checks['original_si_derivative_rows_history_error']=float(derivative_error);assert derivative_error<1e-10
    checks['matrix_shapes']={'reconstruction':list(a.shape),'actual_stop':list(sa.shape)}
    checks['command_rows_equal']=bool(np.array_equal(a[:21],sa[:21]) and np.array_equal(l[:21],sl[:21]) and np.array_equal(u[:21],su[:21]))
    assert checks['command_rows_equal']
    rlabels=[x['label'] for x in csv.DictReader((rec/'rows.csv').open())];slabels=[x['label'] for x in csv.DictReader((stop/'stop_rows.csv').open())]
    mapping=[]
    for i,label in enumerate(rlabels):
        j=slabels.index(label);assert np.array_equal(a[i],sa[j]) and l[i]==sl[j] and u[i]==su[j];mapping.append({'reconstruction_row':i,'stop_row':j,'label':label})
    checks['reconstruction_rows_exact_subset_of_actual_stop']=True
    checks['hessian_difference']=float(np.max(abs(h-sh)));assert checks['hessian_difference']==0 and np.max(abs(sg))==0
    checks['tracking_gradient_equals_negative_request']=float(np.max(abs(g+np.array(meta['request']))));assert checks['tracking_gradient_equals_negative_request']<1e-15
    boxcandidate=numeric(rec/'box_candidate.csv').ravel();checks['command_only_candidate_original_si_violation']=float(max(0,np.max(l[:21]-a[:21]@boxcandidate),np.max(a[:21]@boxcandidate-u[:21])))
    checks['reconstructed_LP']=lp_check(a,l,u);checks['actual_stop_LP']=lp_check(sa,sl,su);assert checks['reconstructed_LP']['status']==2 and checks['actual_stop_LP']['status']==2
    replay=list(csv.DictReader((stop/'replay.csv').open()));assert len(replay)==len(original)
    errors={key:0. for key in ['q_before_error','v_before_error','q_post_error','v_post_error','target_error','time_error']}
    for i,(actual,record) in enumerate(zip(replay,original)):
        assert int(actual['record'])==i and actual['tick']==record['tick'] and actual['substep']==record['substep'] and float(actual['time_s'])==float(record['time_s'])
        for key in errors:errors[key]=max(errors[key],abs(float(actual[key])))
    assert max(errors.values())==0
    cycles=list(csv.DictReader((stop/'stop_cycles.csv').open()));stoprows=list(csv.DictReader((stop/'stop_raw.csv').open()));summary=yaml.safe_load((stop/'summary.yaml').read_text())
    assert len(cycles)==1 and cycles[0]['status']=='PRIMAL_INFEASIBLE' and cycles[0]['accepted']=='0' and not stoprows and float(cycles[0]['age_s'])<.05
    assert summary['accepted_stop_commands']==0 and not summary['completed_stop'] and summary['final_virtual_time_s']==float(final['time_s'])
    chains=max(np.max(abs(vec(previous,'q_post_')-vec(current,'q_before_'))) for previous,current in zip(original,original[1:]));assert chains==0
    sourcechecks={}
    for suffix in ['tools/phase5_adapter/reconstruct_servo_failure_qp.cpp','tools/phase5_adapter/replay_servo_expanded_failure_stop.cpp','src/predictive_motion_control/src/reactive_qp.cpp','src/predictive_motion_control/src/predictive.cpp','tools/phase5_adapter/phase5_benchmark.cpp']:
        p=root/suffix;inputs.append(p);expected=[f['files'].get(str(p)) for f in frozen];sourcechecks[suffix]={'actual_sha256':sha(p),'frozen_sha256':expected}
        for expected_hash in expected:
            if expected_hash is not None:assert expected_hash==sha(p)
    for path in set(frozen[0]['files'])&set(frozen[1]['files']):
        if any(name in path for name in ['libpredictive_controller.a','libreactive_qp.a','libqp_wrapper.a']):
            p=Path(path);assert sha(p)==frozen[0]['files'][path]==frozen[1]['files'][path];inputs.append(p)
    shared=set(frozen[0]['files'])&set(frozen[1]['files']);changed=[p for p in shared if frozen[0]['files'][p]!=frozen[1]['files'][p]]
    store=Path(json.loads((base/cases[0]/'materialized-identity.json').read_text())['content_store'])
    cachetext=[]
    for f in frozen:
        cachehash=f['files'][str(root/'build-servo-qp-reconstruct-v1/CMakeCache.txt')];blob=store/cachehash;assert sha(blob)==cachehash;inputs.append(blob);cachetext.append(blob.read_text())
    def cache_entries(text):return {line.split(':',1)[0]:line.split('=',1)[1] for line in text.splitlines() if ':' in line and '=' in line and not line.startswith('//')}
    caches=[cache_entries(t) for t in cachetext];cachechanges=[key for key in set(caches[0])|set(caches[1]) if caches[0].get(key)!=caches[1].get(key)]
    analysis=json.loads((base/cases[0]/'feasibility_analysis.json').read_text());candidate=np.array(analysis['normalized_margin_LP']['candidate_velocity']);res=np.maximum(np.maximum(l-a@candidate,a@candidate-u),0);worst=int(np.argmax(res))
    inputs.append(base/cases[0]/'feasibility_analysis.json')
    inputs.extend(base/case/'materialized-identity.json' for case in cases)
    barrier=[{'row':i,'label':rlabels[i],'lower_m_s':float(l[i]),'gradient_times_physical_velocity_m_s':float(a[i]@v),'gradient_times_last_accepted_command_velocity_m_s':float(a[i]@w)} for i in range(21,len(a))]
    result={'scope':__doc__,'verdict':'VERIFIED_RETAINED_FAILURE_AND_COMMAND_GEOMETRY_CONFLICT; NOT_STOPPING_PASS','raw_sha256':sha(raw),'original_rows':len(original),'checks':checks,'box_intervals':sources,'reconstruction_support_proofs':witnesses,'original_si_1e7_acceptance_tolerance_support_proofs':tolerance_witnesses,'actual_stop_support_proofs':switnesses,'row_mapping':mapping,'replay_logged_difference_checks':errors,'replay_evidence_scope':'Independently aligned replay diagnostic differences to original1708records and inspected frozen comparison code; no new physical replay executed by auditor. Replay exports per-record error maxima rather than all actual physical vectors.','stop_cycle':cycles[0],'stop_raw_data_rows':len(stoprows),'stop_summary':summary,'final_record':{'time_s':float(final['time_s']),'physical_velocity_max':float(max(abs(v))),'accepted_velocity_max':float(max(abs(w))),'contacts':int(final['contacts']),'true_clearance_m':float(final['true_clearance_m'])},'barrier_physical_command_comparison':barrier,'margin_LP_nonexecutable':{'worst_row':worst,'label':rlabels[worst],'original_SI_violation':float(res[worst]),'row_units':'rad/s^3 for this command_jerk row'},'source_identity':sourcechecks,'shared_frozen_inputs':len(shared),'same_hash_shared_inputs':len(shared)-len(changed),'changed_shared_input_paths':changed,'cache_changed_keys':cachechanges,'cache_blob_hashes_verified':True,'effective_inputs':{str(f):{'sha256':sha(f),'bytes':f.stat().st_size} for f in inputs},'oracle_source_sha256':sha(Path(__file__))}
    args.output.mkdir(parents=True,exist_ok=False);(args.output/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['verdict','checks','reconstruction_support_proofs','replay_logged_difference_checks','cache_changed_keys','margin_LP_nonexecutable']},indent=2))


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Independent recorded affine servo audit; no fitting, plant runs, or coefficient changes."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

DT, N = .002, 7
EXPECTED = {
    'model': '904460b19cd1014b624e15a6e2dd8827f07a590db08c3d60f86ce896e8a19200',
    'training': 'ab9d14efa1a5886c0683db25345f24d5cacd55343e2768eb60536fa180a11dce',
    'validation': '3331840951457d0219cc0c461ea1339cead478211727c3ffc8579a7e2f847912'}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_raw(path):
    rows = list(csv.DictReader(path.open()))
    a = {prefix: np.array([[float(r[prefix+str(j)]) for j in range(N)] for r in rows])
         for prefix in ['q_before_', 'v_before_', 'target_', 'q_post_', 'v_post_']}
    assert all(np.isfinite(v).all() for v in a.values())
    assert all(int(r['tick']) == i//2 and int(r['substep']) == i%2+1 for i,r in enumerate(rows))
    chain = max(np.max(abs(a['q_before_'][1:]-a['q_post_'][:-1])),
                np.max(abs(a['v_before_'][1:]-a['v_post_'][:-1])))
    clock = max(abs(float(r['time_s'])-(i+1)*DT) for i,r in enumerate(rows))
    hold = np.max(abs(a['target_'][::2]-a['target_'][1::2]))
    assert max(chain,clock,hold) < 1e-8
    return rows, a, {'physical_chain':float(chain),'clock_s':float(clock),'same_target_4ms':float(hold),
                    'q_integrator':float(np.max(abs(a['q_post_']-a['q_before_']-DT*a['v_post_'])))}


def predict(initial, targets, p, b, d):
    # Only initial measurement and target sequence enter this function.
    state = initial.copy()
    for target in targets:
        state = p @ state + b @ target + d
    return state


def evaluate(path, report_path, model, p, b, affine):
    rows,a,checks = load_raw(path)
    y = np.column_stack((a['q_before_'],a['v_before_']))
    yn = np.column_stack((a['q_post_'],a['v_post_']))
    target = a['target_']
    residual = yn - (y @ p.T + target @ b.T + affine)
    active = np.array([r['phase'] != 'warmup' for r in rows])
    report = json.loads(report_path.read_text())
    results, worst_windows = [], []
    difference = 0.0
    for index,length in enumerate([1,2,20,400]):
        starts = np.array([i for i in range(len(rows)-length+1) if i%2==0 and active[i]])
        state = y[starts].copy()
        accumulated_error = np.zeros_like(state)
        for step in range(length):
            state = state @ p.T + target[starts+step] @ b.T + affine
            # Diagnostic residual convolution, not a forecasting input.
            accumulated_error = accumulated_error @ p.T - residual[starts+step]
        error = state - yn[starts+length-1]
        convolution_error = float(np.max(abs(error-accumulated_error)))
        qe,ve = error[:,:N],error[:,N:]
        item={'substeps':length,'windows':len(starts),'max_q_error_rad':float(np.max(abs(qe))),
              'max_v_error_rad_s':float(np.max(abs(ve))),
              'rmse_q_rad':float(np.sqrt(np.mean(qe*qe))),
              'rmse_v_rad_s':float(np.sqrt(np.mean(ve*ve))),
              'residual_convolution_identity_error':convolution_error}
        for key in ['max_q_error_rad','max_v_error_rad_s','rmse_q_rad','rmse_v_rad_s']:
            difference=max(difference,abs(item[key]-report['metrics'][index][key]))
        assert item['windows']==report['metrics'][index]['windows']
        item['passed']=item['max_q_error_rad']<=model['policy']['position_error_limits_rad'][index] and item['max_v_error_rad_s']<=model['policy']['velocity_error_limits_rad_s'][index]
        results.append(item)
        if length == 400:
            for label,values,offset in [('position',qe,0),('velocity',ve,N)]:
                i,j=np.unravel_index(np.argmax(abs(values)),values.shape)
                start=int(starts[i])
                scalar=predict(y[start],target[start:start+length],p,b,affine)
                assert np.max(abs(scalar-state[i])) < 1e-10
                worst_windows.append({'quantity':label,'start_tick':start//2,'joint':int(j),
                                      'start_time_s':float(rows[start]['time_s'])-DT,
                                      'end_time_s':float(rows[start+length-1]['time_s']),
                                      'signed_error':float(values[i,j]),
                                      'initial_measured_state':y[start].tolist(),
                                      'endpoint_prediction':scalar.tolist(),
                                      'endpoint_actual':yn[start+length-1].tolist(),
                                      'diagnostic_convolution_signed_error':float(accumulated_error[i,offset+j])})
    local=model['local_box']
    domainbad=int(np.sum(active & (((a['q_before_']<np.array(local['q_min'])) | (a['q_before_']>np.array(local['q_max']))).any(1) | (abs(a['v_before_'])>local['v_abs_max']).any(1))))
    assert difference<1e-10 and not results[-1]['passed'] and domainbad==0
    return {'raw_rows':len(rows),'phase_counts':{phase:sum(r['phase']==phase for r in rows) for phase in sorted(set(r['phase'] for r in rows))},
            'chain_checks':checks,'active_measured_domain_bad_rows':domainbad,'metrics':results,
            'max_report_metric_discrepancy':difference,'worst_800ms_windows':worst_windows},(rows,a,residual)


def training_diagnostics(rows,a,residual,model):
    mask=np.array([r['phase']=='excitation' for r in rows])
    q,v,c,vn=(a[k][mask] for k in ['q_before_','v_before_','target_','v_post_'])
    rv=residual[mask,N:]
    x=np.column_stack((c-q,v))
    mu,scale=x.mean(0),x.std(0)
    z=np.column_stack(((x-mu)/scale,np.ones(len(x))))
    s=np.linalg.svd(z,compute_uv=False)
    rawsingular=np.linalg.svd(np.column_stack((x,np.ones(len(x)))),compute_uv=False)
    rank=int(np.sum(s>s[0]*max(z.shape)*np.finfo(float).eps))
    corr=np.corrcoef(x,rowvar=False)
    pairs=sorted([(abs(float(corr[i,j])),i,j,float(corr[i,j])) for i in range(14) for j in range(i+1,14)],reverse=True)[:8]
    assert rank==15
    result={'scope':'91011 excitation only; fixed residual strata and SVD; no fitted model or validation-selected hyperparameters',
            'rows':len(x),'scaled_rank':rank,'scaled_condition':float(s[0]/s[-1]),
            'unscaled_design_condition':float(rawsingular[0]/rawsingular[-1]),
            'singular_values_scaled':s.tolist(),'feature_means':mu.tolist(),'feature_scales':scale.tolist(),
            'max_feature_mean_discrepancy':float(np.max(abs(mu-np.array(model['fit_diagnostics']['feature_mean'])))),
            'max_feature_scale_discrepancy':float(np.max(abs(scale-np.array(model['fit_diagnostics']['feature_scale'])))),
            'feature_ranges':{'min':x.min(0).tolist(),'max':x.max(0).tolist()},
            'existing_coefficients_standardized_normal_equation_max_abs':float(np.max(abs(z.T@rv))),
            'largest_feature_correlations':pairs,'per_joint':[]}
    # Descriptive omitted-feature correlations/design conditioning; not a fit.
    extras=np.column_stack((q-q.mean(0),np.sign(v),v*abs(v)))
    extra_names=([f'configuration_delta_joint{j}' for j in range(N)] +
                 [f'velocity_sign_joint{j}' for j in range(N)] +
                 [f'velocity_times_abs_velocity_joint{j}' for j in range(N)])
    result['omitted_feature_residual_correlations']=[]
    for j in range(N):
        correlations=[float(np.corrcoef(extras[:,i],rv[:,j])[0,1]) for i in range(extras.shape[1])]
        result['omitted_feature_residual_correlations'].append({'output_joint':j,
            'largest':sorted([{'feature':name,'correlation':value} for name,value in zip(extra_names,correlations)],
                             key=lambda item:abs(item['correlation']),reverse=True)[:5]})
    candidate=np.column_stack((x,q-q.mean(0)))
    cs=candidate.std(0)
    design=np.column_stack(((candidate-candidate.mean(0))/cs,np.ones(len(candidate))))
    ds=np.linalg.svd(design,compute_uv=False)
    result['configuration_augmented_feature_design_only']={
        'no_fit':True,'columns':design.shape[1],
        'rank':int(np.sum(ds>ds[0]*max(design.shape)*np.finfo(float).eps)),
        'scaled_condition':float(ds[0]/ds[-1])}
    bounds=[-float('inf'),-.001,-.0001,-.00001,.00001,.0001,.001,float('inf')]
    for j in range(N):
        bins=[]
        for low,high in zip(bounds,bounds[1:]):
            selected=(v[:,j]>=low)&(v[:,j]<high)
            if selected.any():
                bins.append({'velocity_bin_rad_s':[None if not np.isfinite(low) else low,None if not np.isfinite(high) else high],
                             'rows':int(selected.sum()),'mean_velocity':float(v[selected,j].mean()),
                             'mean_true_minus_predicted_vnext_residual':float(rv[selected,j].mean()),
                             'rmse_residual':float(np.sqrt(np.mean(rv[selected,j]**2))),
                             'max_abs_residual':float(np.max(abs(rv[selected,j])))})
        mean_velocity_center=v[:,j]-v[:,j].mean()
        serial=float(np.corrcoef(rv[:-1,j],rv[1:,j])[0,1])
        near=np.abs(v[:,j])<=1e-5
        predicted_next=vn[:,j]-rv[:,j]
        result['per_joint'].append({'joint':j,'residual_mean':float(rv[:,j].mean()),
                                   'residual_rmse':float(np.sqrt(np.mean(rv[:,j]**2))),
                                   'residual_max':float(np.max(abs(rv[:,j]))),
                                   'lag_one_residual_correlation':serial,
                                   'near_zero_current_velocity_rows':int(near.sum()),
                                   'near_zero_current_and_next_rows':int(np.sum(near&(abs(vn[:,j])<=1e-5))),
                                   'near_zero_actual_next_while_prediction_above_1e5_rows':int(np.sum((abs(vn[:,j])<=1e-5)&(abs(predicted_next)>1e-5))),
                                   'velocity_sign_bins':bins})
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=args.project
    base=root/'results/phase5/development'
    modelpath=base/'servo-model-v1/model.json'
    modelhash_before=sha(modelpath)
    assert modelhash_before==EXPECTED['model']
    model=json.loads(modelpath.read_text())
    e,v,d=(np.array(model[k]) for k in ['E','V','d'])
    p=np.block([[np.eye(N)-DT*e,DT*v],[-e,v]])
    b=np.vstack((DT*e,e));affine=np.r_[DT*d,d]
    matrixchecks={key:float(np.max(abs(value-np.array(model[key])))) for key,value in [('P_2ms',p),('Q_2ms',b),('affine_2ms',affine)]}
    inputs=[modelpath,root/'scripts/phase5/servo_model_v1.py',root/'scripts/phase5/run_servo_validation_v1.py',
            root/'scripts/phase5/servo_model_v1_test.py',root/'tools/phase5_adapter/servo_identification.cpp']
    result={'scope':__doc__,'matrix_reconstruction_error':matrixchecks,
            'hold_spectral_radius_recomputed':float(np.max(abs(np.linalg.eigvals(p)))),
            'numpy_version':np.__version__,'oracle_source_sha256':sha(Path(__file__)),'datasets':{}}
    train_data=None
    for label,seed in [('training',91011),('validation',91012)]:
        epoch=base/f'servo-identification-v1-{label}'
        exepath,freezepath=epoch/'execution.json',epoch/'frozen.json'
        execution,freeze=(json.loads(f.read_text()) for f in [exepath,freezepath])
        raw=Path(execution['argv'][-1])/'raw.csv'
        reportpath=base/'servo-model-v1'/('training_report.json' if label=='training' else 'heldout-validation/validation_report.json')
        inputs.extend([exepath,freezepath,raw,reportpath])
        assert execution['return_code']==0 and execution['argv'][-2]==str(seed)
        assert sha(raw)==execution['raw_files']['raw.csv']==EXPECTED[label]
        source=root/'tools/phase5_adapter/servo_identification.cpp'
        assert sha(source)==freeze['files'][str(source)]
        if label=='validation':
            assert freeze['files'][str(modelpath)]==modelhash_before==execution['model_prefrozen_sha256']==execution['model_after_run_sha256']
            for suffix in ['servo_model_v1.py','run_servo_validation_v1.py','servo_model_v1_test.py']:
                f=root/'scripts/phase5'/suffix
                assert sha(f)==freeze['files'][str(f)]
            assert sha(root/'scripts/phase5/servo_model_v1.py')==model['script_sha256']
            result['freeze_timestamp_utc']=freeze['frozen_before_run_utc']
            result['frozen_model_policy_matches_model']=freeze['model_policy']==model['policy']
        observations,data=evaluate(raw,reportpath,model,p,b,affine)
        result['datasets'][label]=observations
        if label=='training':train_data=data
    result['training_residual_diagnostics']=training_diagnostics(*train_data,model)
    result['model_created_utc']=model['created_utc']
    result['training_identity_matches_model']=model['training_raw_sha256']==EXPECTED['training']
    result['model_sha256_before']=modelhash_before
    result['model_sha256_after']=sha(modelpath)
    assert result['model_sha256_after']==modelhash_before
    result['effective_inputs']={str(f):{'sha256':sha(f),'bytes':f.stat().st_size} for f in inputs}
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'model_identity':modelhash_before,'hold_spectral_radius':result['hold_spectral_radius_recomputed'],
                      'datasets':{k:v['metrics'] for k,v in result['datasets'].items()},
                      'conditioning':result['training_residual_diagnostics']['scaled_condition']},indent=2))


if __name__=='__main__':main()

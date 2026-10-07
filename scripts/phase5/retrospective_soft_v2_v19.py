#!/usr/bin/env python3
"""Retrospective recorded-target MODEL forecast only; not holdout, fitting, domain expansion or plant."""
import argparse,csv,hashlib,json
from pathlib import Path
SOURCE_BYTES=Path(__file__).read_bytes();SOURCE_SHA=hashlib.sha256(SOURCE_BYTES).hexdigest()
import numpy as np

N=7;DT=.002
MODEL_SHA='984ee85d086aeba7da8260a20b21b301e23dfd2c698a6c61ace0ff956bbec1bb'
RAW_SHA='113a5a1c82e97d6a624656b78fc6383363a76bccf8cc149406071fc57216ee2a'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def box_transition(q,v,c,p):
    m,g,k,d,eta,imp,b=p
    smooth=k*(c-q)-d*v+g
    hessian=1/m+(1-imp)/(imp*m)
    linear=smooth/m+b*v
    unconstrained=-linear/hessian
    force=np.maximum(-eta,np.minimum(eta,unconstrained))
    vn=v+DT*(smooth+force)/(m+DT*d)
    return q+DT*vn,vn


def outside(q,v,c,box):
    error=c-q
    parts={'q':((q<box['q_min'])|(q>box['q_max'])),
           'v':abs(v)>box['v_abs_max'],
           'target_minus_q':((error<box['target_error_min'])|(error>box['target_error_max']))}
    return np.logical_or.reduce([x.any(axis=1) for x in parts.values()]),parts


def metrics(windows):
    if not windows:return {'windows':0}
    q=np.array([x['endpoint_q_error_rad'] for x in windows]);v=np.array([x['endpoint_v_error_rad_s'] for x in windows])
    return {'windows':len(windows),'max_q_error_rad':float(np.max(abs(q))),
            'max_v_error_rad_s':float(np.max(abs(v))),'rmse_q_rad':float(np.sqrt(np.mean(q*q))),
            'rmse_v_rad_s':float(np.sqrt(np.mean(v*v))),
            'actual_domain_bad_windows':sum(x['actual_domain_bad_substeps']>0 for x in windows),
            'forecast_domain_bad_windows':sum(x['forecast_domain_bad_substeps']>0 for x in windows),
            'actual_domain_bad_window_substeps':sum(x['actual_domain_bad_substeps'] for x in windows),
            'forecast_domain_bad_window_substeps':sum(x['forecast_domain_bad_substeps'] for x in windows)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['raw','model','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();assert sha(args.raw)==RAW_SHA and sha(args.model)==MODEL_SHA
    model=json.loads(args.model.read_text());rows=list(csv.DictReader(args.raw.open()))
    assert len(rows)==1802
    assert all(int(r['tick'])==i//2 and int(r['substep'])==i%2+1 for i,r in enumerate(rows))
    read=lambda prefix:np.array([[float(r[prefix+str(j)]) for j in range(N)] for r in rows])
    qpost,vpost,target=read('q_post_'),read('dq_post_'),read('q_accepted_')
    assert all(np.isfinite(x).all() for x in [qpost,vpost,target])
    assert np.max(abs(target[::2]-target[1::2]))==0
    # Every scored initial q/v is the preceding recorded physical endpoint.
    # Row0 has no recorded initial physical velocity; do not manufacture it.
    qbefore=np.r_[qpost[:1],qpost[:-1]];vbefore=np.r_[vpost[:1],vpost[:-1]]
    box=model['local_box'];public=model['public_parameters']
    p=[np.array(model[k]) for k in ['mass_effective_kg_m2','bias_Nm']]+[np.array(public[k]) for k in ['kp_Nm_rad','damping_Nm_s_rad','friction_bound_Nm','impedance','reference_decay_s_inv']]
    known=np.arange(1,len(rows));actualpre,parts=outside(qbefore[known],vbefore[known],target[known],box)
    actualpost,postparts=outside(qpost[known],vpost[known],target[known],box)
    actual_bad=np.zeros(len(rows),dtype=bool);actual_bad[known]=actualpre|actualpost
    domain_by_phase={}
    for phase in ['warmup','path','stopping']:
        idx=np.array([i for i in known if rows[i]['phase']==phase]);bad,preparts=outside(qbefore[idx],vbefore[idx],target[idx],box);after,aparts=outside(qpost[idx],vpost[idx],target[idx],box)
        domain_by_phase[phase]={'recorded_substeps_with_known_prestate':len(idx),
                               'bad_any_pre_or_post_substeps':int(np.sum(bad|after)),
                               'prestate_bad_by_joint':{key:np.sum(value,axis=0).tolist() for key,value in preparts.items()},
                               'poststate_bad_by_joint':{key:np.sum(value,axis=0).tolist() for key,value in aparts.items()}}
    result={'scope':__doc__,'classification':'RETROSPECTIVE_UNVALIDATED_STRESS_DIAGNOSTIC_NO_ACCURACY_PASS',
            'source_sha256':SOURCE_SHA,'model_sha256':sha(args.model),'raw_sha256':sha(args.raw),
            'numpy_version':np.__version__,'physical_rows':len(rows),
            'phase_substeps':{phase:sum(r['phase']==phase for r in rows) for phase in ['warmup','path','stopping']},
            'path_duration_s':sum(r['phase']=='path' for r in rows)*DT,
            'unscored_initial_boundary':{'tick':0,'reason':'raw has no recorded pre-first-row physical velocity; no setup/teacher-forced reconstruction used'},
            'actual_domain_by_phase':domain_by_phase,'domain_count_policy':'Known recorded pre-state and post-state are checked against unchanged q/v/target−q bounds. Forecast counts each window/substep once if either pre/post model state is outside; both raw pre/post and model pre/post counts remain visible. Overlapping window counts are not independent rows or trials.',
            'forecasts':[]}
    for length in [1,2,20,400]:
        starts=np.arange(2,len(rows)-length+1,2);qp=qbefore[starts].copy();vp=vbefore[starts].copy()
        forecast_bad=np.zeros(len(starts),dtype=int);pre_bad_count=np.zeros(len(starts),dtype=int);post_bad_count=np.zeros(len(starts),dtype=int)
        for k in range(length):
            c=target[starts+k];before,_=outside(qp,vp,c,box)
            qp,vp=box_transition(qp,vp,c,p);after,_=outside(qp,vp,c,box)
            forecast_bad+=before|after;pre_bad_count+=before;post_bad_count+=after
        qe=qp-qpost[starts+length-1];ve=vp-vpost[starts+length-1];windows=[]
        for wi,start in enumerate(starts):
            end=int(start+length-1);phases=list(dict.fromkeys(r['phase'] for r in rows[start:end+1]))
            windows.append({'start_tick':int(start)//2,'start_time_s':float(rows[start-1]['time_s']),
                            'end_tick':int(rows[end]['tick']),'end_substep':int(rows[end]['substep']),
                            'end_time_s':float(rows[end]['time_s']),'start_phase':rows[start]['phase'],
                            'end_phase':rows[end]['phase'],'phase_sequence':phases,
                            'endpoint_q_error_rad':qe[wi].tolist(),'endpoint_v_error_rad_s':ve[wi].tolist(),
                            'initial_domain_bad':bool(outside(qbefore[start:start+1],vbefore[start:start+1],target[start:start+1],box)[0][0]),
                            'actual_domain_bad_substeps':int(np.sum(actual_bad[start:end+1])),
                            'forecast_domain_bad_substeps':int(forecast_bad[wi]),
                            'forecast_domain_bad_pre_substeps':int(pre_bad_count[wi]),
                            'forecast_domain_bad_post_substeps':int(post_bad_count[wi]),
                            'fully_inside_declared_domain':not(np.any(actual_bad[start:end+1]) or forecast_bad[wi])})
        summaries={'all_complete_windows':metrics(windows),'by_start_phase':{},'by_phase_sequence':{}}
        for phase in ['warmup','path','stopping']:summaries['by_start_phase'][phase]=metrics([w for w in windows if w['start_phase']==phase])
        for sequence in sorted(set('->'.join(w['phase_sequence']) for w in windows)):
            summaries['by_phase_sequence'][sequence]=metrics([w for w in windows if '->'.join(w['phase_sequence'])==sequence])
        summaries['fully_in_domain_retrospective_subset']=metrics([w for w in windows if w['fully_inside_declared_domain']])
        result['forecasts'].append({'substeps':length,'duration_s':length*DT,'summaries':summaries,'windows':windows})
    assert sha(Path(__file__))==SOURCE_SHA and sha(args.model)==MODEL_SHA and sha(args.raw)==RAW_SHA
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Retrospective soft-v2 forecast on observed v19-full','',
           'Scope: fixed-model retrospective conditional forecast, not fresh holdout, model fit, physical plant execution, domain enlargement or controller acceptance. No production predictor was called. Future q/v never initialize the model inside a window; only the initial preceding measured endpoint and subsequent accepted targets are used.',
           '',f'Model SHA `{MODEL_SHA}`; raw SHA `{RAW_SHA}`; oracle source SHA `{SOURCE_SHA}`. Original domain and coefficients are unchanged. Warmup, path, stopping and crossing windows are all retained. Tick0 is unscorable because the first pre-step physical velocity is absent from this raw schema; every remaining complete4ms-boundary window is scored.',
           '', '| Horizon | All scored windows | Max q error [rad] | Max v error [rad/s] | Actual-domain-bad windows | Forecast-domain-bad windows |', '|---|---:|---:|---:|---:|---:|']
    for item in result['forecasts']:
        s=item['summaries']['all_complete_windows'];lines.append(f"| {item['duration_s']:.3f}s | {s['windows']} | {s['max_q_error_rad']:.6e} | {s['max_v_error_rad_s']:.6e} | {s['actual_domain_bad_windows']} | {s['forecast_domain_bad_windows']} |")
    lines+=['','The main path lasts0.556s, so no0.8s path-only window exists. Every0.8s path-start window necessarily includes stopping. The JSON retains each complete window, its phase sequence, signed joint endpoint errors and all domain counts; no stopping/out-of-domain window is discarded. Fully in-domain subset metrics are retrospective descriptions only, not a new accuracy gate.','',
            'Any forecast initialized or propagated outside the declared q/v/target-minus-q box is unvalidated numerical stress evidence. Passing a box is also not proof of uniform box accuracy. These observations do not authorize widening bounds, selecting coefficients on this already seen trace, or treating old physical output as prospective validation.','',
            'Domain counts distinguish raw rows from overlapping window/substep evaluations. Both pre/post states are checked. Source startup identity is fixed and source/model/raw bytes are checked unchanged before publication. Only the independent developer may collect prospective validation or integrate the C++ contract; this diagnostic does not close CTRL-001 or Phase5.']
    (args.output/'DIAGNOSTIC.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'phase_rows':result['phase_substeps'],'actual_domain':domain_by_phase,'horizons':[{k:item[k] for k in ['duration_s']}|{'all':item['summaries']['all_complete_windows'],'path_start':item['summaries']['by_start_phase']['path']} for item in result['forecasts']]},indent=2))


if __name__=='__main__':main()

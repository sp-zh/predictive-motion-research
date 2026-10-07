#!/usr/bin/env python3
"""Score every expanded trace window; preserve old domain failures and new prospective limits."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import yaml
from servo_model_soft_friction_v2 import evaluate,step
from servo_model_v1 import trace,sha,write_new,DT
p=argparse.ArgumentParser(description=__doc__)
for name in ['raw','execution','frozen','model','protocol','output']:
    p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args()
model=json.loads(a.model.read_text());execution=json.loads(a.execution.read_text());frozen=json.loads(a.frozen.read_text());protocol=yaml.safe_load(a.protocol.read_text())
if execution['argv'][-2]!='91012':raise ValueError('prospective 91012 fixture required')
for file in [a.model,a.protocol,Path(__file__)]:
    if frozen['files'].get(str(file.resolve()))!=sha(file):raise ValueError('prefrozen input changed '+str(file))
if execution['raw_files']['raw.csv']!=sha(a.raw):raise ValueError('trace identity changed')
if sha(Path(__file__).with_name('servo_model_soft_friction_v2.py'))!=model['script_sha256']:raise ValueError('prediction source changed')
a.output.mkdir(exist_ok=False)
report={'model_sha256':sha(a.model),'raw_sha256':sha(a.raw),'frozen_sha256':sha(a.frozen),'protocol_sha256':sha(a.protocol),
        'scope':'Prospective expanded conditional recorded-input test only; original frozen model/domain and errors unchanged; no controller/robust/hardware/online certificate',
        'no_refit':True,'no_windows_deleted_for_old_domain':True,'seed':91012,'run_id':'servo-soft-friction-v2-expanded-validation'}
if execution['return_code']!=0:
    report.update({'gate':'FAIL_GUARD_OR_INCOMPLETE_TRACE','fixture_return_code':execution['return_code'],'partial_trace_retained':True,
                   'stderr':(a.execution.parent/'stderr.log').read_text(),'old_domain_not_expanded':True})
    write_new(a.output/'validation_report.json',report);print(json.dumps(report,indent=2));raise SystemExit(1)
rows,data=trace(a.raw)
old=evaluate(model,rows,data)
q,v,c=[data[k] for k in ['q_before_','v_before_','target_']]
active=np.array([r['phase']!='warmup' for r in rows]);new=protocol['prospective_model_domain']
center=np.array(new['q_center_rad']);radius=new['q_radius_rad'];ec=np.array(new['target_error_center_rad']);er=new['target_error_radius_rad']
def masks(q,v,c,domain):
    if domain=='old':
        box=model['local_box'];lo,hi=np.array(box['q_min']),np.array(box['q_max']);vmax=box['v_abs_max'];elo,ehi=np.array(box['target_error_min']),np.array(box['target_error_max'])
    else:lo,hi=center-radius,center+radius;vmax=new['v_abs_max_rad_s'];elo,ehi=ec-er,ec+er
    return {'q':(q<lo)|(q>hi),'v':abs(v)>vmax,'target_minus_q':((c-q)<elo)|((c-q)>ehi)}
def counts(m,active=None):
    return {key:values[active].sum(axis=0).tolist() if active is not None else values.sum(axis=0).tolist() for key,values in m.items()}
measured_old,measured_new=masks(q,v,c,'old'),masks(q,v,c,'new')
new_bad_rows=int(sum(active & np.logical_or.reduce([values.any(axis=1) for values in measured_new.values()])))
starts=np.array([i for i in range(0,len(rows)-400+1,2) if active[i]])
qp,vp=q[starts].copy(),v[starts].copy();predicted_old={k:np.zeros(7,dtype=int) for k in ['q','v','target_minus_q']};predicted_new={k:np.zeros(7,dtype=int) for k in ['q','v','target_minus_q']}
for k in range(400):
    target=c[starts+k]
    qp,vp=step(qp,vp,target,model)
    for which,destination in [('old',predicted_old),('new',predicted_new)]:
        for key,value in masks(qp,vp,target,which).items():destination[key]+=value.sum(axis=0)
all_metrics_pass=all(m['passed'] for m in old['metrics'])
expanded_pass=all_metrics_pass and new_bad_rows==0 and all(not np.any(x) for x in predicted_new.values())
report.update({'gate':'PASS_EXPANDED_RECORDED_TRACE' if expanded_pass else 'FAIL_EXPANDED_RECORDED_TRACE',
               'old_model_domain_gate':old['gate'],'old_model_domain_unchanged':True,'metrics':old['metrics'],
               'old_domain_measured_bad_per_joint':counts(measured_old,active),'new_domain_measured_bad_per_joint':counts(measured_new,active),
               'old_domain_measured_bad_rows':old['active_domain_bad_rows'],'new_domain_measured_bad_rows':new_bad_rows,
               'predicted_800ms_old_domain_bad_per_joint':{k:v.tolist() for k,v in predicted_old.items()},
               'predicted_800ms_new_domain_bad_per_joint':{k:v.tolist() for k,v in predicted_new.items()},
               'active_trace_ranges':{'q_min':q[active].min(0).tolist(),'q_max':q[active].max(0).tolist(),'v_abs_max':abs(v[active]).max(0).tolist(),
                                      'target_min':c[active].min(0).tolist(),'target_max':c[active].max(0).tolist(),
                                      'target_minus_q_min':(c-q)[active].min(0).tolist(),'target_minus_q_max':(c-q)[active].max(0).tolist()},
               'new_prospective_domain':new,'new_box_not_validated_everywhere':True,'overlapping_windows_not_independent_trials':True})
write_new(a.output/'validation_report.json',report);print(json.dumps(report,indent=2))
raise SystemExit(0 if expanded_pass else 1)

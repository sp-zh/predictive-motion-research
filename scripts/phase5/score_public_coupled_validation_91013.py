#!/usr/bin/env python3
"""Prospectively frozen scorer, conditional public_v2 model only; no fitting."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import argparse,csv,hashlib,json,time
from collections import Counter
from pathlib import Path
import numpy as np,yaml
from public_coupled_servo_v2 import PublicServo

parser=argparse.ArgumentParser(description=__doc__)
for name in ['packet','raw','execution','output']:parser.add_argument('--'+name,type=Path,required=True)
a=parser.parse_args();sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();freeze=json.loads((a.packet/'frozen.json').read_text());protocol=json.loads((a.packet/'protocol.json').read_text());execution=json.loads(a.execution.read_text());assert freeze['seed']==91013 and execution['argv'][-2]=='91013' and execution['prepared_frozen_sha256']==sha(a.packet/'frozen.json');assert all(sha(f)==h for f,h in freeze['files'].items());assert sha(a.raw)==execution['raw_files']['raw.csv'];a.output.mkdir(exist_ok=False)
summary=yaml.safe_load(a.raw.with_name('summary.yaml').read_text()) if a.raw.with_name('summary.yaml').exists() else {};base={'scope':'Freshseed91013known-curated-input development conditional validation only; no untouchedfinalholdout/newwaveform/task/controller/250Hz/Phase5 acceptance','protocol_sha256':sha(a.packet/'protocol.json'),'frozen_sha256':sha(a.packet/'frozen.json'),'raw_sha256':sha(a.raw),'summary':summary,'seed':91013,'no_calibration':True}
if execution['return_code']!=0 or not summary.get('completed_stop') or summary.get('primary_failure') or summary.get('stop_failure'):
 base.update(gate='FAIL_COLLECTOR_GUARD_OR_STOP',partial_trace_retained=True);(a.output/'validation_report.json').write_text(json.dumps(base,indent=2)+'\n');print(json.dumps(base,indent=2));raise SystemExit(1)
rows=list(csv.DictReader(a.raw.open()));assert all(int(r['tick'])==i//2 and int(r['substep'])==i%2+1 for i,r in enumerate(rows))
def data(prefix):return np.array([[float(r[prefix+str(j)]) for j in range(7)] for r in rows])
q,v,c,qpost,vpost=[data(k) for k in ['q_before_','v_before_','target_','q_post_','v_post_']];assert np.array_equal(c[::2],c[1::2]);active=np.array([r['phase']!='warmup' for r in rows]);contacts=np.array([int(r['contacts']) for r in rows]);constants=json.loads(Path(protocol['public_model_constants']).read_text());model=PublicServo(Path('/home/codextransfer/predictive_motion/experiments/generated/inspection/inspection_fr3.xml'),constants);metrics=[];failures=[];maxkkt=0.;maxiters=0;branches=Counter();clamps=Counter();last=time.monotonic()
for h in protocol['horizons']:
 count=h['substeps'];starts=list(range(0,len(rows)-count+1,2));group={s:{'windows':0,'complete':0,'failed':0,'maxq':0.,'maxv':0.,'sumq':0.,'sumv':0.,'worstq':None,'worstv':None} for s in ['active','warmup']}
 for number,i in enumerate(starts):
  kind='active' if active[i] else 'warmup';s=group[kind];s['windows']+=1;qp,vp=q[i].copy(),v[i].copy()
  try:
   for k in range(count):
    qp,vp,info=model.step(qp,vp,c[i+k]);maxkkt=max(maxkkt,info['original_KKT']);maxiters=max(maxiters,info['iterations']);branches.update(info['branches']);clamps['controls']+=info['control_clips'];clamps['forces']+=info['force_clips']
   # Actual contact labels classify unsupported regime after forecast; not model input.
   if np.any(contacts[i:i+count]):raise ValueError('recorded contact outside model regime')
   eq,ev=abs(qp-qpost[i+count-1]),abs(vp-vpost[i+count-1]);s['complete']+=1;s['sumq']+=float(np.sum(eq**2));s['sumv']+=float(np.sum(ev**2))
   if eq.max()>s['maxq']:s['maxq']=float(eq.max());s['worstq']={'start_tick':int(rows[i]['tick']),'joint_index':int(eq.argmax()),'phase':rows[i]['phase']}
   if ev.max()>s['maxv']:s['maxv']=float(ev.max());s['worstv']={'start_tick':int(rows[i]['tick']),'joint_index':int(ev.argmax()),'phase':rows[i]['phase']}
  except Exception as e:s['failed']+=1;failures.append({'duration_s':count*.002,'start_tick':int(rows[i]['tick']),'phase':rows[i]['phase'],'type':type(e).__name__,'reason':str(e)})
  if time.monotonic()-last>20:print(json.dumps({'progress_duration_s':count*.002,'processed':number+1,'total':len(starts),'failures':len(failures)}),flush=True);last=time.monotonic()
 for kind,s in group.items():
  denominator=s['complete']*7;selected=[i for i in starts if ('active' if active[i] else 'warmup')==kind];roster=dict(Counter(rows[i]['phase'] for i in selected));intersections={phase:sum(any(rows[j]['phase']==phase for j in range(i,i+count)) for i in selected) for phase in ['reference_motion','reference_recorded_stop','hold','new_shared_stop']}
  metrics.append({'scope':kind,'duration_s':count*.002,'windows':s['windows'],'completed_windows':s['complete'],'failed_windows':s['failed'],'max_q_error_rad':s['maxq'],'max_v_error_rad_s':s['maxv'],'rmse_q_rad':float(np.sqrt(s['sumq']/denominator)) if denominator else None,'rmse_v_rad_s':float(np.sqrt(s['sumv']/denominator)) if denominator else None,'q_worst':s['worstq'],'v_worst':s['worstv'],'q_limit_rad':h['q_limit_rad'],'v_limit_rad_s':h['v_limit_rad_s'],'start_phase_counts':roster,'windows_intersecting_phase':intersections,'hold_only_windows':sum(all(rows[j]['phase']=='hold' for j in range(i,i+count)) for i in selected),'passed':s['failed']==0 and s['maxq']<=h['q_limit_rad'] and s['maxv']<=h['v_limit_rad_s']})
 print(json.dumps({'finished_duration_s':count*.002,'metrics':metrics[-2:]}),flush=True);(a.output/'metrics.partial.json').write_text(json.dumps(metrics,indent=2)+'\n');(a.output/'failures.partial.json').write_text(json.dumps(failures,indent=2)+'\n')
cycles=list(csv.DictReader(a.raw.with_name('cycles.csv').open()));attempts=list(csv.DictReader(a.raw.with_name('all_qp_solves.csv').open()));points={(int(r['tick']),r['kind']):r for r in attempts};maxSI=0.;bad=[]
for row in csv.DictReader(a.raw.with_name('all_qp_rows.csv').open()):
 candidate=points[(int(row['tick']),row['kind'])]
 if candidate['wrapper_status']!='SOLVED' or int(candidate['raw_status'])!=1 or int(candidate['candidate_size'])!=7:bad.append({'tick':int(row['tick']),'kind':row['kind'],'reason':'native/API/candidate rejection'});continue
 value=sum(float(row['A'+str(j)])*float(candidate['x'+str(j)]) for j in range(7));maxSI=max(maxSI,0.,float(row['lower'])-value,value-float(row['upper']))
age=max(float(r['command_age_s']) for r in cycles);collector_ok=not bad and maxSI<=1e-7 and age<=.05
assert all(sha(f)==h for f,h in freeze['files'].items())
base.update({'gate':'PASS_FRESH_CURATED_CONDITIONAL_TRACE_ONLY' if collector_ok and all(m['passed'] for m in metrics if m['scope']=='active') else 'FAIL_FRESH_CURATED_CONDITIONAL_TRACE','metrics':metrics,'failures':failures,'phase_rows':dict(Counter(r['phase'] for r in rows)),'max_force_QP_KKT':maxkkt,'max_force_QP_iterations':maxiters,'repeated_prediction_branches':dict(branches),'prediction_clamps':dict(clamps),'actual_original_row_max_SI_violation':maxSI,'native_API_rejections':bad,'max_command_age_s':age,'full4ms_deadline_misses':sum(int(r['deadline_miss']) for r in cycles),'all_full_windows_including_hold_stop_retained':True,'overlapping_windows_not_independent_trials':True,'model_parameter_source_unchanged':True,'stop_scope':protocol['stop_scope'],'uniform_accuracy_box_claim':False,'main_MPC_integrated':False})
(a.output/'validation_report.json').write_text(json.dumps(base,indent=2)+'\n');print(json.dumps({'gate':base['gate'],'metrics':metrics,'failures':len(failures),'maxSI':maxSI},indent=2));raise SystemExit(0 if base['gate'].startswith('PASS') else 1)

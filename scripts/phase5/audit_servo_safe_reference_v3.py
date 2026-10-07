#!/usr/bin/env python3
import csv,json,hashlib,sys
from pathlib import Path
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/servo-safe-reference-v3-validation';raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-safe-reference-v3-validation');sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
sys.path.insert(0,str(p/'scripts/phase5'));from signed_command_velocity_cone import acceleration_interval
rows=list(csv.DictReader((raw/'raw.csv').open()));sub=[r for r in rows if int(r['substep'])==2];cycles=list(csv.DictReader((raw/'cycles.csv').open()));solves=list(csv.DictReader((raw/'all_qp_solves.csv').open()));points={(int(r['tick']),r['kind']):r for r in solves};maximum_si=0.;worst=None
for row in csv.DictReader((raw/'all_qp_rows.csv').open()):
 key=(int(row['tick']),row['kind']);candidate=points[key];assert candidate['wrapper_status']=='SOLVED' and int(candidate['raw_status'])==1 and int(candidate['candidate_size'])==7
 x=np.array([float(candidate['x'+str(j)]) for j in range(7)]);a=np.array([float(row['A'+str(j)]) for j in range(7)]);value=float(a@x);lo=float(row['lower']);hi=float(row['upper']);violation=max(0.,lo-value,value-hi)
 if violation>maximum_si:maximum_si=violation;worst={'tick':key[0],'kind':key[1],'row':int(row['row']),'violation':violation}
continuation_bad=[]
for r in sub:
 if int(r['tick'])<500:continue
 for j in range(7):
  w=float(r['command_velocity_'+str(j)]);alpha=float(r['command_acceleration_'+str(j)])
  if acceleration_interval(w,alpha,.0625,1.,20.,.004) is None:continuation_bad.append({'tick':int(r['tick']),'joint':j})
report=json.loads((base/'model-audit/validation_report.json').read_text());window_rosters=[]
for count in (1,2,20,400):
 windows=[i for i in range(0,len(rows)-count+1,2) if rows[i]['phase']!='warmup'];starts=Counter(rows[i]['phase'] for i in windows);hold_only=sum(all(rows[k]['phase']=='hold' for k in range(i,i+count)) for i in windows)
 window_rosters.append({'duration_s':count*.002,'windows':len(windows),'start_phase_counts':dict(starts),'hold_only_windows':hold_only,'windows_containing_motion_or_recorded_braking':sum(any(rows[k]['phase'] in ('reference_motion','reference_recorded_stop') for k in range(i,i+count)) for i in windows)})
audit={'scope':'Actual fresh curated-reference run and recorded-input prediction diagnostics only; no untouched holdout/online250Hz/expanded model certificate','raw_sha256':sha(raw/'raw.csv'),'phase_cycle_counts':dict(Counter(r['phase'] for r in sub)),'window_rosters':window_rosters,'last_complete_tick':int(sub[-1]['tick']),'last_time_s':float(sub[-1]['time_s']),'native_API_SOLVED_only_all_attempts':all(r['wrapper_status']=='SOLVED' and int(r['raw_status'])==1 for r in solves),'solve_attempts':len(solves),'stop_attempts':sum(r['kind']=='stop' for r in solves),'max_independent_original_row_SI_violation':maximum_si,'worst_row':worst,'SI_tolerance':1e-7,'max_command_age_s':max(float(r['command_age_s']) for r in cycles),'full_cycle_deadline_misses':sum(int(r['deadline_miss']) for r in cycles),'max_full_cycle_wall_s':max(float(r['full_cycle_wall_s']) for r in cycles),'actual_accepted_history_continuation_failures':continuation_bad,'final_command_speed':max(abs(float(sub[-1]['command_velocity_'+str(j)])) for j in range(7)),'final_physical_speed':max(abs(float(sub[-1]['v_post_'+str(j)])) for j in range(7)),'predictor_gate':report['gate'],'model_domain_gate':report['old_model_domain_gate'],'matrix_provenance':'A/l/u directly logged for every tracking/stop attempt; exact H/g from frozen tracking/stopping source and frozen w_reference inputs, not separately exported per solve; first-rejection full H/g snapshot mechanism not triggered in successful fixture','retained_setup_failures':['First make requested new target before CMake regeneration: no rule,exit2','CMake regeneration without ROS setup: ament_package ModuleNotFoundError,exit1; fixed by existing ROS setup.bash, no installation/config relaxation']}
assert maximum_si<=1e-7 and not continuation_bad and audit['max_command_age_s']<=.05
(base/'actual_guard_phase_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
fig,axes=plt.subplots(1,2,figsize=(11,4.5),constrained_layout=True);t=np.array([float(r['time_s']) for r in sub]);w=np.array([float(r['command_velocity_3']) for r in sub]);v=np.array([float(r['v_post_3']) for r in sub]);axes[0].plot(t,w,label='Actual accepted w, joint 3');axes[0].plot(t,v,label='Measured physical v, joint 3');axes[0].axvspan(3.712,10.,alpha=.12,color='gray',label='Hold (not excitation)');axes[0].set_xlabel('New simulation time (s)');axes[0].set_ylabel('rad/s');axes[0].legend(fontsize=8)
metrics=report['metrics'];qrat=[r['max_q_error_rad']/r['q_limit_rad'] for r in metrics];vrat=[r['max_v_error_rad_s']/r['v_limit_rad_s'] for r in metrics];x=np.arange(4);axes[1].bar(x-.18,qrat,.36,label='Maximum q error / limit');axes[1].bar(x+.18,vrat,.36,label='Maximum v error / limit');axes[1].axhline(1,color='r',ls=':',label='Frozen acceptance limit');axes[1].set_xticks(x,['2 ms','4 ms','40 ms','800 ms']);axes[1].set_ylabel('Error / original frozen limit');axes[1].legend(fontsize=8);axes[1].set_title('Predictor expansion fails at 2 / 4 ms',fontsize=11)
fig.suptitle('v3 curated reference: guard and actual stop complete; frozen predictor still fails',fontsize=12);image=base/'phase5_servo_safe_reference_v3.png';fig.savefig(image,dpi=170);plt.close(fig)
(base/'phase5_servo_safe_reference_v3.json').write_text(json.dumps({'image_sha256':sha(image),'raw_sha256':sha(raw/'raw.csv'),'report_sha256':sha(base/'model-audit/validation_report.json'),'source':'scripts/phase5/audit_servo_safe_reference_v3.py','units':'seconds,radians/s,dimensionless error ratio','scope':audit['scope']},indent=2)+'\n');print(json.dumps(audit,indent=2))

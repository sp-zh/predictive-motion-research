#!/usr/bin/env python3
import csv,hashlib,json
from collections import Counter
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import yaml
p=Path('/home/codextransfer/predictive_motion'); base=p/'results/phase5/development/servo-safe-reference-unit-20261007';base.mkdir(exist_ok=False)
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
reports=[];fig,axes=plt.subplots(2,2,figsize=(12,7),constrained_layout=True)
for i,ver in enumerate(('v1','v2')):
 run='servo-safe-reference-'+ver+'-validation';d=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw')/run
 rows=list(csv.DictReader((d/'raw.csv').open()));sub=[r for r in rows if int(r['substep'])==2]
 summary=yaml.safe_load((d/'summary.yaml').read_text());cycles=list(csv.DictReader((d/'cycles.csv').open()))
 stages=Counter(r['phase'] for r in sub)
 # v1 labels were generic: retain original raw; derive roster explicitly in report only.
 roster=Counter(('warmup' if int(r['tick'])<500 else 'reference_motion' if int(r['tick'])<695 else 'reference_recorded_stop' if int(r['tick'])<928 else 'hold') for r in sub) if ver=='v1' else stages
 t=np.array([float(r['time_s']) for r in sub]);w=np.array([[float(r['command_velocity_'+str(j)]) for j in range(7)] for r in sub]);v=np.array([[float(r['v_post_'+str(j)]) for j in range(7)] for r in sub])
 axes[i,0].plot(t,w[:,3],label='Accepted command w, joint 3');axes[i,0].plot(t,v[:,3],label='Measured physical v, joint 3');axes[i,0].axhline(-.0625,color='r',ls=':',label='Command lower limit');axes[i,0].set_ylabel('rad/s');axes[i,0].legend(fontsize=8);axes[i,0].set_title(ver+': '+summary['primary_failure'])
 axes[i,1].plot(t,[float(r['true_clearance_m'])*1000 for r in sub]);axes[i,1].axhline(10,color='r',ls=':',label='10 mm guard');axes[i,1].set_ylabel('Recorded true clearance (mm)');axes[i,1].legend(fontsize=8);axes[i,1].set_title('Shared stop '+('completed' if summary['completed_stop'] else 'infeasible'))
 report={'run':run,'raw_sha256':sha(d/'raw.csv'),'summary':summary,'raw_phase_cycles':dict(stages),'annotated_phase_cycles':dict(roster),'last_complete_tick':int(sub[-1]['tick']),'last_time_s':float(sub[-1]['time_s']),'last_command_w':w[-1].tolist(),'last_command_alpha':[float(sub[-1]['command_acceleration_'+str(j)]) for j in range(7)],'first_non_SOLVED_cycle':next((r for r in cycles if r['status'] not in ('SOLVED','HOLD')),None),'max_command_speed':float(np.max(abs(w))),'max_physical_speed':float(np.max(abs(v))),'full_cycle_deadline_misses':sum(int(r['deadline_miss']) for r in cycles),'scope':'Curated seen reference inputs; fresh physical run; all raw rows retained. Guard rejection prevents predictor validation success; no new model domain.'}
 if ver=='v1':report['annotation']='Generic excitation raw label preserved. Derived warmup/motion/recorded braking counts refer to source input schedule, not successful fresh stop.'
 reports.append(report)
for ax in axes[-1]:ax.set_xlabel('New-run simulation time (s)')
fig.suptitle('Retained safe-reference development failures — frozen servo model, original guards',fontsize=13)
image=base/'phase5_servo_reference_failures.png';fig.savefig(image,dpi=170);plt.close(fig)
meta={'scope':'Development diagnostics only; no accepted controller result or CAD modification','source_raw_hashes':[r['raw_sha256'] for r in reports],'image_sha256':sha(image),'units':{'time':'seconds','joint_velocity':'radians/second','distance':'millimetres'},'source':'scripts/phase5/analyze_servo_reference_unit.py'}
(base/'reference_failure_report.json').write_text(json.dumps(reports,indent=2)+'\n');(base/'phase5_servo_reference_failures.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(reports,indent=2))

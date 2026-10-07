#!/usr/bin/env python3
"""Strip a seen safe trajectory to accepted target increments; no physical-state inputs."""
import csv,json,hashlib
from pathlib import Path
import numpy as np,yaml
p=Path(__file__).resolve().parents[2];source=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/moving-stop-v1/raw.csv');base=p/'results/phase5/development/servo-safe-reference-v1';base.mkdir(exist_ok=False)
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
rows=[r for r in csv.DictReader(source.open()) if int(r['substep'])==2]
c=np.array([[float(r['q_accepted_'+str(j)]) for j in range(7)] for r in rows]);w=np.array([[float(r['dq_accepted_'+str(j)]) for j in range(7)] for r in rows]);alpha=np.array([[float(r['command_acc_'+str(j)]) for j in range(7)] for r in rows]);jerk=np.array([[float(r['command_jerk_'+str(j)]) for j in range(7)] for r in rows])
assert all(int(r['tick'])==i for i,r in enumerate(rows)) and len(rows)==928
assert np.max(abs(w))<=.0625+1e-7 and np.max(abs(alpha))<=1+1e-7 and np.max(abs(jerk))<=20+1e-7 and np.max(abs(w[-1]))==0
out=base/'accepted_target_increments.csv'
with out.open('x',newline='') as f:
 writer=csv.writer(f,lineterminator='\n');writer.writerow(['tick']+['c_delta_'+str(j) for j in range(7)]+['w_reference_'+str(j) for j in range(7)])
 for i in range(len(rows)):writer.writerow([i]+[format(x,'.17g') for x in c[i]-c[0]]+[format(x,'.17g') for x in w[i]])
meta={'scope':'Curated previously seen moving-stop accepted inputs only; original physical states never exported to controller; not untouched old holdout',
      'source_raw_sha256':sha(source),'reference_sha256':sha(out),'cycles':928,'control_dt_s':.004,'relative_offset':'new initial accepted target + original accepted target - original initial accepted target',
      'initial_500_cycles':'original warmup target constant; new run also warms 2s','tail':'hold last accepted target through tick2499; then shared bounded stop',
      'source_selected_before_new_run':True,'precheck':{'max_delta_rad_per_joint':np.max(abs(c-c[0]),axis=0).tolist(),'max_w_rad_s':float(np.max(abs(w))),'max_alpha_rad_s2':float(np.max(abs(alpha))),'max_jerk_rad_s3':float(np.max(abs(jerk))),'target_integrator_error':float(np.max(abs(c[1:]-c[:-1]-.004*w[1:])))},
      'geometry_and_stop':'source had observed bounded stop; new initialization geometry/command/physical guards and fresh stop must independently pass'}
with (base/'reference_identity.json').open('x') as f:f.write(json.dumps(meta,indent=2)+'\n')
cfg=yaml.safe_load((p/'config/phase5_development/servo_validation_soft_friction_v2_expanded.yaml').read_text())
cfg.update({'validation_waveform_id':'safe-accepted-reference-v1-91012','accepted_reference_csv':str(out),'validation_policy':'Fresh91012 execution of curated previously observed accepted-target increments with explicit new-initial-target offset; frozen coefficients/thresholds; no original physical states as predictor input or new holdout evidence.'})
with (p/'config/phase5_development/servo_validation_safe_reference_v1.yaml').open('x') as f:f.write(yaml.safe_dump(cfg,sort_keys=False))
print(json.dumps(meta,indent=2))

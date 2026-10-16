from pathlib import Path
import sys,os,json,ast,struct,hashlib
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root61_parser_and_formal_review_v1 as m61
strict=m61.strict
T=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.ClassDef)and x.name=='R'],type_ignores=[]),'<saved-reader>','exec'))
O=Path('/private/tmp/root62_stop_cause_review_v1_20261016');O.mkdir(exist_ok=True);os.environ['P5_DERIVED53_ROOT']=str(O)
P=Path('/private/tmp/phase5_controlled_stop_exact_cycle_terminal61_v1_20261016');A=next(P.glob('actual-dell/*/run-attempt1/artifacts'));out=[]
for case in ['cycle-0/trial-0','cycle-43/trial-0','cycle-43/trial-1','cycle-74/trial-0','cycle-95/trial-0']:
 d=A/case
 r=R(d/'planning_guard.bin','EXPLICIT_CURRENT_DERIVED_ALPHA_PROGRESS_JERK_AND_NUMERICAL_TAIL_V5');solver,strict_radius,progressguard,pstrict,pb,pr=r.take('<6d');base=r.u();columns=[r.u()for _ in range(r.u())];scales=r.vec();label=r.text();center=r.vec();limiting=r.take('<q')[0];rows=[r.u()for _ in range(r.u())];proof=r.mat();fraction=r.d();r.text();r.end();assert len(center)==160 and proof.shape==(2800,5)
 r=R(d/'candidate.bin','SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');reason=r.text();permission,attempts,entries=r.take('<3Q');status,raw,api,iterations,violationrow=r.take('<5Q');solution=r.vec();assert len(solution)==160
 # Full preview not needed here: the native solver vector is directly checked against retained planning center.
 deltas=solution.reshape(20,8)[:18,:7]-center.reshape(20,8)[:18,:7];assert np.max(np.abs(deltas))<=strict_radius+1e-12
 sourcepins={n:{'bytes':(d/n).stat().st_size,'sha256':hashlib.sha256((d/n).read_bytes()).hexdigest()}for n in ['planning_guard.bin','candidate.bin']}
 first=solution[:7];cent=center[:7];out.append(dict(case=case,solver_guard=solver,strict_guard=strict_radius,trial_margin=fraction,first_alpha=first.tolist(),first_nominal_alpha=cent.tolist(),first_alpha_change=(first-cent).tolist(),first_progress_b=solution[7],first_nominal_progress_b=center[7],max_alpha_change=float(np.max(np.abs(deltas))),first_alpha_at_guard=[bool(abs(abs(a)-solver)<=1e-10)for a in first-cent],proof_shape=list(proof.shape),input_pins=sourcepins))
rows=json.loads(Path('/Users/uot/Documents/ChatGPT/ros/reviews/evidence/phase5_actual61_exact_cycle_and_stop_refusal_v1_20261016/Root/actual/STOP_ROWS.json').read_text());limits=dict(v=1e-4,a=1e-3,w=1e-6,alpha=1e-4,r=1e-6,b=1e-4);failures={k:sum(abs(x[k])>v for x in rows)for k,v in limits.items()}
report=dict(schema='ROOT62_READONLY_SAVED61_STOP_CAUSE_OBSERVATIONS_V1',records=len(rows),individual_threshold_failures=failures,first=rows[0],last=rows[-1],peak_velocity=max(x['v']for x in rows),peak_command_velocity=max(x['w']for x in rows),last_to_threshold={k:abs(rows[-1][k])/v for k,v in limits.items()},selected_current_guard_and_alpha=out,confirmed='The simultaneous stop predicate correctly fails; physical v/a and accepted w/alpha fail every saved stop observation. Progress r/b dropping below threshold does not stop the arm. Current43 accepted trial has a much smaller nominal-centered alpha subset after actual B rejection. Original stop-mode cost is present, but cannot by itself guarantee finite stop within64commands.',pending='A causal ablation of a fresh genuinely braking nominal within unchanged plant/QP/SI/nonlinear/B/C/jerk/stop limits is needed. Saved-data guard observations alone do not prove a single complete cause or authorize replacing a native controller. No new Model/controller/native/probe executed.')
bounded_write(O/'SAVED61_STOP_CAUSE_OBSERVATIONS.json',json.dumps(report,indent=2)+'\n');print(json.dumps(report))

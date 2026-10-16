from pathlib import Path
import sys,os,json,ast,hashlib,struct
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root61_parser_and_formal_review_v1 as m61
strict=m61.strict
T=ast.parse(Path('/private/tmp/root58_selected_audit_v1.py').read_text());exec(compile(ast.Module(body=[x for x in T.body if isinstance(x,ast.ClassDef)and x.name=='R'],type_ignores=[]),'<saved-reader>','exec'))
O=Path('/private/tmp/root62_stop_cause_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);P=Path('/private/tmp/phase5_controlled_stop_exact_cycle_terminal61_v1_20261016');A=next(P.glob('actual-dell/*/run-attempt1/artifacts'));G=json.loads((O/'SAVED61_STOP_CAUSE_OBSERVATIONS.json').read_text());out=[]
for e in G['selected_current_guard_and_alpha']:
 if not e['case'].startswith(('cycle-43','cycle-74','cycle-95')):continue
 p=A/e['case']/'observation_before.bin';r=R(p,'ACTUAL_NATIVE_SESSION_SNAPSHOT');oid,tid=r.text(),r.text();tick,sequence,completed=r.take('<3Q');stage,error=r.text(),r.text();r.take('<3Q');time,age=r.take('<2d');contact=r.u();q,v,C,w=[r.arr(7)for _ in range(4)];s,rate=r.take('<2d');prev_a=r.arr(7);prev_b=r.d();r.u();r.arr(7);r.arr(7);r.u();r.text();r.vec();r.vec();r.end()
 c=np.array(e['first_nominal_alpha']);alpha=np.array(e['first_alpha']);radius=e['solver_guard'];low=c-radius;high=c+radius
 # For each joint, can the retained alpha-only nominal-centered subset even change w toward zero in this first 4ms?
 forced_acceleration=[i for i in range(7)if (w[i]>0 and low[i]>0)or(w[i]<0 and high[i]<0)]
 zero_target=-w/.004;can_reach_one_step=[bool(low[i]<=zero_target[i]<=high[i])for i in range(7)]
 out.append(dict(case=e['case'],current_w=w.tolist(),physical_v=v.tolist(),previous_alpha=prev_a.tolist(),selected_alpha=alpha.tolist(),nominal_center=c.tolist(),nominal_centered_first_alpha_interval=[low.tolist(),high.tolist()],joints_forced_to_increase_abs_w_by_guard=forced_acceleration,joints_zero_w_one_step_inside_subset=can_reach_one_step,predicted_new_w_from_original_integrator=(w+.004*alpha).tolist(),scope='Algebraic restriction of disclosed additional planning subset only. One-step zero may also violate original jerk/acceleration/domain constraints; this diagnostic does not recommend or authorize one-step stopping. No nonlinear/physical response predicted here.'))
report=dict(schema='ROOT62_SAVED_FIRST_CONTROL_STOP_DIRECTION_RESTRICTION_V1',reader_qualification='Initial saved-data reader import omitted Python struct; NameError occurred before reading source fields or producing output. Corrected reader import only, no native/capture/experiment repeated.',cases=out,confirmed='Selected43/trial1 accepted command remains forced to accelerate some command-velocity components by the narrow nominal-centered alpha subset. The solver stop penalty cannot reverse those components within that retained subset. This establishes a concrete planning restriction, not the sole cause of all physical stop failure.',next_needed='Use genuine current braking nominal and fresh bounded validation to isolate/repair receding inherited nominal effect while preserving original trust/SI/nonlinear/B/C/jerk/physical/stop gates. Do not relax original safety thresholds or extend consumed61.')
bounded_write(O/'SAVED61_FIRST_CONTROL_DIRECTION_RESTRICTION.json',json.dumps(report,indent=2)+'\n');print(json.dumps(report))

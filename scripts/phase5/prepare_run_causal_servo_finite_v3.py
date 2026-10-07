#!/usr/bin/env python3
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');s=(p/'scripts/phase5/run_causal_servo_api_v2.py').read_text().replace('causal-soft-servo-cpp-v2','causal-soft-servo-cpp-v3').replace('build-causal-soft-servo-v2','build-causal-soft-servo-v3').replace('phase5_causal_servo_v2','phase5_causal_servo_v3').replace('prepare_causal_servo_api_v2.py','prepare_causal_servo_finite_v3.py').replace('PASS_ISOLATED_CAUSAL_API_BRANCH_V2','PASS_ISOLATED_CAUSAL_FINITE_V3')
s=s.replace("files=list(source.iterdir())",'''overflow=p/'build-causal-soft-servo-v3/causal_soft_servo_overflow_probe';edge=p/'build-causal-soft-servo-v3/root_edge_probe'
horizon_files=[]
for name,kind in [('horizon_control',0),('horizon_initial',1)]:
 m={'mass_effective_kg_m2':[.002],'bias_Nm':[0.],'public_parameters':{'kp_Nm_rad':[1e152 if kind==0 else 1e-300],'damping_Nm_s_rad':[0.],'friction_bound_Nm':[0. if kind==0 else .3],'impedance':[.9],'reference_decay_s_inv':[100. if kind==0 else 1e152]},'local_box':{'q_min':[-.01],'q_max':[.01],'v_abs_max':.05,'target_error_min':[-.001],'target_error_max':[.001]}}
 f=base/(name+'.yaml');f.write_text(yaml.safe_dump({'cases':[{'name':name,'model':m,'initial':[0.,0.,0.,0.,.2,0.],'controls':[[0.,0.],[0.,0.]],'mesh_s':[.004,.004]}],'rejection_cases':[]},sort_keys=False));horizon_files.append(f)
files=[overflow,edge]+horizon_files+list(source.iterdir())''')
s=s.replace("'api',[str(api)]", "'overflow',[str(overflow)]),('edge',[str(edge)]),('api',[str(api)]")
s=s.replace("reports=[];nominal_reports=[]",'''overflow_lines=(base/'overflow.stdout').read_text().splitlines();edge_result=json.loads((base/'edge.stdout').read_text())
if not edge_result['model_validated'] or not edge_result['threw']:failures.append({'reason':'root finite-parameter counterexample not rejected'})
if len(overflow_lines)!=9:failures.append({'reason':'overflow fixture roster mismatch'})
for line in overflow_lines[1:]:
 if not line.startswith('composed,') and ',1,1,nonfinite ' not in line:failures.append({'reason':'arithmetic failure not rejected','line':line})
horizon_results=[]
for f in horizon_files:
 r=subprocess.run([str(binary),str(f),str(base/(f.stem+'.partial.json'))],capture_output=True,text=True);(base/(f.stem+'.stdout')).write_text(r.stdout);(base/(f.stem+'.stderr')).write_text(r.stderr)
 accepted=r.returncode==3 and 'nonfinite horizon' in r.stderr
 horizon_results.append({'case':f.stem,'return_code':r.returncode,'rejected':accepted,'reason':r.stderr.strip(),'partial_output_retained':True})
 if not accepted:failures.append({'reason':'nonfinite horizon was not rejected','case':f.stem})
reports=[];nominal_reports=[]''')
s=s.replace("'scope':'Only robust public-entry validation and fixed-root branch/nominal numerical parity; same physical model/FR3 box; synthetic threshold box only is separate algebraic fixture; no ordinary derivative FD, refit or plant/main-MPC integration'", "'scope':'Reject nonfinite derived arithmetic at cycle/cell/horizon serialization and every intermediate matrix propagation; root overflow counterexample plus original API/branch/nominal regressions. Original FR3 parameters/domain unchanged; no refit, plant or main-MPC integration'")
s=s.replace("'API_invalid_entry_checks':78", "'root_counterexample':edge_result,'overflow_regression_rows':overflow_lines[1:],'horizon_overflow_rejections':horizon_results,'API_invalid_entry_checks':78")
dest=p/'scripts/phase5/run_causal_servo_finite_v3.py';assert not dest.exists();dest.write_text(s);print('v3 runner prepared; probes not executed')

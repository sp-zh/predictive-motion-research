#!/usr/bin/env python3
import datetime,hashlib,json,subprocess
from pathlib import Path
import numpy as np,yaml
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/causal-soft-servo-cpp-v3';base.mkdir(exist_ok=False);sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();branch=Path('/home/codextransfer/clean-audits/root-causal-servo-branch-packet-20261007/branch_packet.json');assert sha(branch)=='8f09f79a23a6be6f3785dc76612c9a1f43b90b038e1fb248d616116dcb1276f7';packet=json.loads(branch.read_text())
(base/'root_branch_packet.json').write_bytes(branch.read_bytes());(base/'root_branch_READY.json').write_bytes(branch.with_name('READY.json').read_bytes())
fixture=base/'branch_input.yaml';fixture.write_text(yaml.safe_dump({'cases':[{'name':c['name'],'model':c['model'],'initial':c['initial'],'controls':[c['control']],'mesh_s':[c['dt_s']]} for c in packet['cases']],'rejection_cases':[]},sort_keys=False))
nominal=p/'results/phase5/development/causal-soft-servo-cpp-v1/input.yaml';ref=p/'results/phase5/development/causal-soft-servo-cpp-reference-v1/oracle.json';binary=p/'build-causal-soft-servo-v3/causal_soft_servo_probe';api=p/'build-causal-soft-servo-v3/causal_soft_servo_api_probe';source=p/'tools/phase5_causal_servo_v3';overflow=p/'build-causal-soft-servo-v3/causal_soft_servo_overflow_probe';edge=p/'build-causal-soft-servo-v3/root_edge_probe'
horizon_files=[]
for name,kind in [('horizon_control',0),('horizon_initial',1)]:
 m={'mass_effective_kg_m2':[.002],'bias_Nm':[0.],'public_parameters':{'kp_Nm_rad':[1e152 if kind==0 else 1e-300],'damping_Nm_s_rad':[0.],'friction_bound_Nm':[0. if kind==0 else .3],'impedance':[.9],'reference_decay_s_inv':[100. if kind==0 else 1e152]},'local_box':{'q_min':[-.01],'q_max':[.01],'v_abs_max':.05,'target_error_min':[-.001],'target_error_max':[.001]}}
 f=base/(name+'.yaml');f.write_text(yaml.safe_dump({'cases':[{'name':name,'model':m,'initial':[0.,0.,0.,0.,.2,0.],'controls':[[0.,0.],[0.,0.]],'mesh_s':[.004,.004]}],'rejection_cases':[]},sort_keys=False));horizon_files.append(f)
files=[overflow,edge]+horizon_files+list(source.iterdir())+[Path(__file__),p/'scripts/phase5/prepare_causal_servo_finite_v3.py',p/'build-causal-soft-servo-v3/CMakeCache.txt',binary,api,fixture,base/'root_branch_packet.json',base/'root_branch_READY.json',nominal,ref]
freeze={'before_probes_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{str(f):sha(f) for f in files},'tolerance':5e-12,'scope':'Reject nonfinite derived arithmetic at cycle/cell/horizon serialization and every intermediate matrix propagation; root overflow counterexample plus original API/branch/nominal regressions. Original FR3 parameters/domain unchanged; no refit, plant or main-MPC integration'};(base/'frozen.json').write_text(json.dumps(freeze,indent=2)+'\n')
failures=[]
for name,cmd in [('overflow',[str(overflow)]),('edge',[str(edge)]),('api',[str(api)]),('branch',[str(binary),str(fixture),str(base/'actual_branches.json')]),('nominal',[str(binary),str(nominal),str(base/'actual_nominal.json')])]:
 r=subprocess.run(cmd,capture_output=True,text=True);(base/(name+'.stdout')).write_text(r.stdout);(base/(name+'.stderr')).write_text(r.stderr)
 if r.returncode:failures.append({'probe':name,'return_code':r.returncode,'stderr':r.stderr})
overflow_lines=(base/'overflow.stdout').read_text().splitlines();edge_result=json.loads((base/'edge.stdout').read_text())
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
reports=[];nominal_reports=[]
if not failures:
 actual=json.loads((base/'actual_branches.json').read_text());assert len(actual['cases'])==8
 for a,e in zip(actual['cases'],packet['cases']):
  errors={k:float(np.max(abs(np.array(av)-np.array(ev)))) for k,av,ev in [('state',a['states'][1],e['next_state']),('A',a['cell_A'][0],e['A']),('B',a['cell_B'][0],e['B']),('defect',a['cell_defect'][0],e['defect'])]};same=a['history'][0]['branches_2ms']==e['branches_2ms'];reports.append({'name':e['name'],'errors':errors,'branches_2ms':a['history'][0]['branches_2ms'],'branches_equal':same,'clip_equalities':a['clip_equalities'],'exact_clip_threshold':e['exact_clip_threshold'],'derivative_scope':e['derivative_scope']})
  if not same or max(errors.values())>5e-12:failures.append({'case':e['name'],'reason':'branch or numerical mismatch'})
 actual=json.loads((base/'actual_nominal.json').read_text());expected=json.loads(ref.read_text())
 for a,e in zip(actual['cases'],expected['cases']):
  errors={k:float(np.max(abs(np.array(a[k])-np.array(e[k])))) for k in ['states','cell_A','cell_B','cell_defect','condensed_offsets','control_sensitivities','initial_sensitivities']};same=all(x['branches_2ms']==y['branches_2ms'] for x,y in zip(a['history'],e['history']));nominal_reports.append({'name':e['name'],'errors':errors,'branches_equal':same})
  if not same or max(errors.values())>5e-12:failures.append({'case':e['name'],'reason':'nominal regression'})
 if not all(x['rejected'] for x in actual['rejections']) or len(actual['rejections'])!=10:failures.append({'reason':'old domain/mesh rejection regression'})
 api_lines=(base/'api.stdout').read_text().splitlines();assert len(api_lines)==79
 if any(not x.endswith(',1') for x in api_lines[1:]):failures.append({'reason':'invalid public entry accepted'})
assert all(sha(f)==h for f,h in freeze['files'].items())
report={'gate':'PASS_ISOLATED_CAUSAL_FINITE_V3' if not failures else 'FAIL_RETAINED','root_branch_packet_sha256':sha(base/'root_branch_packet.json'),'root_oracle_source_sha256':'c63f524d2002323ca635574addcf8ef04a498154ea171ac5a58deda088853710','root_counterexample':edge_result,'overflow_regression_rows':overflow_lines[1:],'horizon_overflow_rejections':horizon_results,'API_invalid_entry_checks':78,'API_invalid_scenarios':27,'branch_cases':reports,'nominal_cases':nominal_reports,'original_domain_mesh_rejections':10,'failures':failures,'source_binary_inputs_unchanged':True,'scope':freeze['scope']};(base/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(failures))

#!/usr/bin/env python3
import datetime,hashlib,json,subprocess
from pathlib import Path
import numpy as np,yaml
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/causal-soft-servo-cpp-v2';base.mkdir(exist_ok=False);sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();branch=Path('/home/codextransfer/clean-audits/root-causal-servo-branch-packet-20261007/branch_packet.json');assert sha(branch)=='8f09f79a23a6be6f3785dc76612c9a1f43b90b038e1fb248d616116dcb1276f7';packet=json.loads(branch.read_text())
(base/'root_branch_packet.json').write_bytes(branch.read_bytes());(base/'root_branch_READY.json').write_bytes(branch.with_name('READY.json').read_bytes())
fixture=base/'branch_input.yaml';fixture.write_text(yaml.safe_dump({'cases':[{'name':c['name'],'model':c['model'],'initial':c['initial'],'controls':[c['control']],'mesh_s':[c['dt_s']]} for c in packet['cases']],'rejection_cases':[]},sort_keys=False))
nominal=p/'results/phase5/development/causal-soft-servo-cpp-v1/input.yaml';ref=p/'results/phase5/development/causal-soft-servo-cpp-reference-v1/oracle.json';binary=p/'build-causal-soft-servo-v2/causal_soft_servo_probe';api=p/'build-causal-soft-servo-v2/causal_soft_servo_api_probe';source=p/'tools/phase5_causal_servo_v2';files=list(source.iterdir())+[Path(__file__),p/'scripts/phase5/prepare_causal_servo_api_v2.py',p/'build-causal-soft-servo-v2/CMakeCache.txt',binary,api,fixture,base/'root_branch_packet.json',base/'root_branch_READY.json',nominal,ref]
freeze={'before_probes_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{str(f):sha(f) for f in files},'tolerance':5e-12,'scope':'Only robust public-entry validation and fixed-root branch/nominal numerical parity; same physical model/FR3 box; synthetic threshold box only is separate algebraic fixture; no ordinary derivative FD, refit or plant/main-MPC integration'};(base/'frozen.json').write_text(json.dumps(freeze,indent=2)+'\n')
failures=[]
for name,cmd in [('api',[str(api)]),('branch',[str(binary),str(fixture),str(base/'actual_branches.json')]),('nominal',[str(binary),str(nominal),str(base/'actual_nominal.json')])]:
 r=subprocess.run(cmd,capture_output=True,text=True);(base/(name+'.stdout')).write_text(r.stdout);(base/(name+'.stderr')).write_text(r.stderr)
 if r.returncode:failures.append({'probe':name,'return_code':r.returncode,'stderr':r.stderr})
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
report={'gate':'PASS_ISOLATED_CAUSAL_API_BRANCH_V2' if not failures else 'FAIL_RETAINED','root_branch_packet_sha256':sha(base/'root_branch_packet.json'),'root_oracle_source_sha256':'c63f524d2002323ca635574addcf8ef04a498154ea171ac5a58deda088853710','API_invalid_entry_checks':78,'API_invalid_scenarios':27,'branch_cases':reports,'nominal_cases':nominal_reports,'original_domain_mesh_rejections':10,'failures':failures,'source_binary_inputs_unchanged':True,'scope':freeze['scope']};(base/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(failures))

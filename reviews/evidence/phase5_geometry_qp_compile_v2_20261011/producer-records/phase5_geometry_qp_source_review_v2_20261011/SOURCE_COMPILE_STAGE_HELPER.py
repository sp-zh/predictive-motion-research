from pathlib import Path
import json,hashlib,shlex,subprocess
D=Path('/private/tmp/phase5_geometry_qp_session_active_v2_20261011');old='/home/codextransfer/predictive_motion/results/phase5/session-task-start-stabilization-v2-20261010-attempt7';remote='/home/codextransfer/predictive_motion/results/phase5/session-geometry-qp-three-cycle-v4-20261011-attempt30'
a=json.loads(Path('/private/tmp/phase5_task_start_a_active_v1_20261010/dev_compile_plan.json').read_text());prefix=a['compile_argv'][0][:a['compile_argv'][0].index('-MMD')];prefix=[s.replace(old,remote) for s in prefix]
names=['model_boundary.cpp','normalization.cpp','affine_assembly.cpp','integrated_horizon_qp.cpp','runtime_observer.cpp','task_local_provider.cpp','lossless_evidence.cpp','active_first_cycle.cpp','candidate_validation.cpp','cycle_support_tests.cpp','current_numeric_tests.cpp','current_numeric_oracle.cpp','observer_tests.cpp','owner_binding_tests.cpp']
argv=[prefix+['-MMD','-MF',remote+f'/build-attempt1/unit-{i}.d','-c',remote+'/src/'+n,'-o',remote+f'/build-attempt1/unit-{i}.o'] for i,n in enumerate(names,1)]
files={'src/'+p.name:p.read_text() for p in sorted((D/'src').iterdir()) if p.is_file()}
ids=[{'requested_path':remote+'/'+n,'bytes':len(s.encode()),'sha256':hashlib.sha256(s.encode()).hexdigest()} for n,s in files.items()]
plan={'schema':'ACTIVE_SESSION_PILOT_BC_COMPILE_V1','output_directory':remote+'/build-attempt1','env':a['env'],'input_files':ids,'readonly_directory_rosters':[],'compile_argv':argv}
runner=Path('/private/tmp/phase5_task_start_a_active_v1_20261010/dev_compile.py').read_text().replace('ACTIVE_SESSION_A_COMPILE_V1','ACTIVE_SESSION_PILOT_BC_COMPILE_V1').replace("assert len(plan['compile_argv'])==2","assert len(plan['compile_argv'])==14")
files.update({'dev_compile.py':runner,'dev_compile_plan.json':json.dumps(plan,indent=2)+'\n'})
s='''import pathlib,json,sys
p=pathlib.Path(%r);p.mkdir(exist_ok=False);(p/'src').mkdir()
for n,b in json.load(sys.stdin).items():
 with (p/n).open('x') as f:f.write(b)
print('fresh14TU compile only staged; no native B/C run')
'''%remote
x=subprocess.run(['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(s)],input=json.dumps(files).encode(),capture_output=True,timeout=25);assert x.returncode==0,x.stderr
for n,b in files.items():
 if not n.startswith('src/'):(D/n).write_text(b)
(D/'REMOTE.json').write_text(json.dumps({'remote':remote})+'\n');print(x.stdout.decode())

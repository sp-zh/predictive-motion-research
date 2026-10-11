from pathlib import Path
import json,hashlib,shlex,subprocess
D=Path('/private/tmp/phase5_nonzero_progress_tail_margin_active_v4_20261011');remote=json.loads((D/'REMOTE.json').read_text())['remote'];ssh=['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer'];elf=remote+'/link-attempt1/active_first_cycle'
s='''from pathlib import Path
import json,hashlib
p=Path(%r);assert json.loads((p/'link-attempt1/BUILD_RESULT.json').read_text())['complete'];q=Path(%r);print(json.dumps({'path':str(q),'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()}))
'''%(remote,elf);x=subprocess.run(ssh+['python3 -I -S -B -c '+shlex.quote(s)],capture_output=True,timeout=20);assert x.returncode==0,x.stderr;producer=json.loads(x.stdout)
base=Path('/private/tmp/phase5_task_start_a_active_v1_20261010');input=json.loads((base/'active_input_v1.json').read_text());input['schema']='NONZERO_PROGRESS_NUMERICAL_TAIL_GEOMETRY_TASK_METRIC_DIAGNOSTIC_V2';input['session_id']='ACTUAL_PRIVATE_GEOMETRY_QP_3CYCLE_SEED91011_ATTEMPT36';old_guess=input.pop('numeric_guess');input['dependencies']=[n for n in input['dependencies'] if n['path']!=old_guess['path']]
input['scope']='One warm1000 then sameSimulationSession3privatecurrentgeometryQPcycles: actualobserve/oneboundauthenticSessionSharedOwner+stillactiveForecastValueConnectedToken+Snapshotbits/providernominal400full9035gradqueries/2true2cover1600rows/repropagate/fulloriginalQP14756SI/freshcurrentnumeric/nativeOSQP/fullSI/strict/valueB400+initialJacobian/oneownerC2 each; cumulativeforecasts6/tasksteps6/commits3; full144/18progress variables+solveralpha.000999/strict.001+progressjerk4.999/strict4.9995+planningterminalr1e-13 biasedsubset(noexactE0equivalence)+privateactualtask10mm/.05every2mssubstep; numeric48Mlogical/sourcebatch1.024B unchanged/outputglobal768MiB/journalglobal48MiB/cyclebinary128MiB/eachjournal12MiB; CPU120/AS2GiB/wall150/FSIZE256MiB/streams1MiB; offline actualwall4msmiss recorded; firstnonzero3currentcycles development; no fulltask/stop/main/scorer/phaseacceptance'
text=json.dumps(input,indent=2)+'\n';identity={'requested_path':remote+'/profile-version1/active_input.json','bytes':len(text.encode()),'sha256':hashlib.sha256(text.encode()).hexdigest()}
plan=json.loads((base/'active_run_plan.json').read_text());oldargv=plan['compile_argv'][0];skip={oldargv[0],oldargv[1],old_guess['path']};plan['input_files']=[row for row in plan['input_files'] if row['requested_path'] not in skip]+[identity,{'requested_path':producer['path'],'bytes':producer['bytes'],'sha256':producer['sha256']}]
for q in (D/'src').iterdir():
 if q.is_file():plan['input_files'].append({'requested_path':remote+'/src/'+q.name,'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
plan['output_directory']=remote+'/run-attempt1';plan['schema']='NONZERO_PROGRESS_NUMERICAL_TAIL_GEOMETRY_THREE_CYCLE_RUNTIME_V1';plan['compile_argv']=[[elf,identity['requested_path'],identity['sha256'],producer['sha256'],remote+'/run-attempt1/artifacts']]
runner=(base/'active_run_driver.py').read_text().replace('ACTIVE_SESSION_A_RUNTIME_V1','NONZERO_PROGRESS_NUMERICAL_TAIL_GEOMETRY_THREE_CYCLE_RUNTIME_V1').replace("'runtime_invocations':0","'controlled_executable_dispatch_attempts':len(records)");files={'profile-version1/active_input.json':text,'profile-version1/PRODUCER.json':json.dumps(producer,indent=2)+'\n','active_run_plan.json':json.dumps(plan,indent=2)+'\n','active_run_driver.py':runner}
s='''import pathlib,sys,json
p=pathlib.Path(%r);(p/'profile-version1').mkdir(exist_ok=False)
for n,b in json.load(sys.stdin).items():
 with (p/n).open('x') as f:f.write(b)
print('runtime profile staged only, no native invocation')
'''%remote;x=subprocess.run(ssh+['python3 -I -S -B -c '+shlex.quote(s)],input=json.dumps(files).encode(),capture_output=True,timeout=25);assert x.returncode==0,x.stderr
for n,b in files.items():
 p=D/n;p.parent.mkdir(exist_ok=True);p.write_text(b)
print(x.stdout.decode());print(json.dumps({'producer':producer,'runtime_plan_identities':len(plan['input_files']),'input_sha256':identity['sha256']}))

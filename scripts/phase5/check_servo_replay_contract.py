#!/usr/bin/env python3
"""Negative control: a corrupted past state must reject replay before stop attempts."""
import csv,hashlib,json,os,subprocess
from pathlib import Path
p=Path(__file__).resolve().parents[2];base=p/'results/phase5/development/servo-expanded-failure-stop-replay-v1';case=base/'contract-negative-control';case.mkdir(exist_ok=False)
source=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-soft-friction-v2-expanded-validation/raw.csv')
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
original_sha=sha(source)
with source.open() as f:
 reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
rows[0]['q_post_0']=format(float(rows[0]['q_post_0'])+1e-6,'.17g')
corrupted=case/'corrupted_state.csv'
with corrupted.open('x',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
binary=p/'build-servo-qp-reconstruct-v1/replay_servo_expanded_failure_stop'
freeze={'scope':__doc__,'original_raw_sha256':original_sha,'synthetic_raw_sha256':sha(corrupted),'binary_sha256':sha(binary),'script_sha256':sha(__file__),'changed_field':'first q_post_0 + 1e-6 rad; accepted targets and initial state unchanged'}
with (case/'frozen.json').open('x') as f:f.write(json.dumps(freeze,indent=2)+'\n')
env=dict(os.environ);env['LD_LIBRARY_PATH']=str(p/'.vendor/mujoco-3.3.7/lib')+':'+env.get('LD_LIBRARY_PATH','')
argv=[str(binary),str(p),str(p/'config/phase5_development/servo_validation_soft_friction_v2_expanded.yaml'),str(corrupted),str(case/'rejected-replay')]
r=subprocess.run(argv,env=env,cwd=p,capture_output=True,text=True)
with (case/'stdout.log').open('x') as f:f.write(r.stdout)
with (case/'stderr.log').open('x') as f:f.write(r.stderr)
passed=r.returncode==1 and 'prefix physical/command/time mismatch' in r.stderr and not (case/'rejected-replay/stop_cycles.csv').exists() and sha(source)==original_sha
with (case/'result.json').open('x') as f:f.write(json.dumps({'scope':__doc__,'passed':passed,'return_code':r.returncode,'stop_attempt_started':False,'original_raw_unchanged':sha(source)==original_sha,'argv':argv},indent=2)+'\n')
print(json.dumps({'passed':passed,'return_code':r.returncode,'stderr':r.stderr}));raise SystemExit(0 if passed else 1)

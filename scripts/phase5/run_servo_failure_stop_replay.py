#!/usr/bin/env python3
"""Freeze full accepted-target past replay and shared guarded failure-stop attempt."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
p=Path(__file__).resolve().parents[2];e=p/'results/phase5/development/servo-expanded-failure-stop-replay-v1'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-soft-friction-v2-expanded-validation/raw.csv')
old=json.loads((p/'results/phase5/development/servo-soft-friction-v2-expanded-validation/frozen.json').read_text())
files={name:sha(name) for name in old['files']}
binary=p/'build-servo-qp-reconstruct-v1/replay_servo_expanded_failure_stop'
for f in [raw,binary,p/'tools/phase5_adapter/replay_servo_expanded_failure_stop.cpp',p/'tools/phase5_servo_diagnostics/CMakeLists.txt',p/'build-servo-qp-reconstruct-v1/CMakeCache.txt',Path(__file__)]:files[str(f)]=sha(f)
e.mkdir(exist_ok=False)
freeze={'files':files,'scope':'full accepted-target past replay including warmup; exact q/v/target/time match required; shared stop may return NO_FEASIBLE_STOP; original run unchanged','frozen_before_run_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
with (e/'frozen.json').open('x') as f:f.write(json.dumps(freeze,indent=2)+'\n')
sys.path.insert(0,str(p/'scripts/phase5'));from materialize_identity import materialize
materialize(e/'frozen.json')
argv=[str(binary),str(p),str(p/'config/phase5_development/servo_validation_soft_friction_v2_expanded.yaml'),str(raw),str(e/'replay-stop')]
env=dict(os.environ);env['LD_LIBRARY_PATH']=str(p/'.vendor/mujoco-3.3.7/lib')+':'+env.get('LD_LIBRARY_PATH','')
start=time.monotonic()
with (e/'stdout.log').open('x') as out,(e/'stderr.log').open('x') as err:r=subprocess.call(argv,cwd=p,env=env,stdout=out,stderr=err)
with (e/'execution.json').open('x') as f:f.write(json.dumps({'argv':argv,'return_code':r,'wall_s':time.monotonic()-start,'output_files':{str(f.relative_to(e)):sha(f) for f in (e/'replay-stop').rglob('*') if f.is_file()}},indent=2)+'\n')
print((e/'stdout.log').read_text());print((e/'stderr.log').read_text());raise SystemExit(r)

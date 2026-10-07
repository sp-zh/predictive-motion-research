#!/usr/bin/env python3
"""Freeze every existing fixture input plus candidate before independent seed 91012."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time

p = Path(__file__).resolve().parents[2]
sha = lambda f: hashlib.sha256(Path(f).read_bytes()).hexdigest()
model = p / 'results/phase5/development/servo-model-soft-friction-v2-frozen/model.json'
candidate = json.loads(model.read_text())
if candidate['training_seed'] != 91011 or candidate['status'] != 'FROZEN_CANDIDATE_NOT_ACCEPTED':
    raise ValueError('unexpected candidate')
if sha(p / 'scripts/phase5/servo_model_soft_friction_v2.py') != candidate['script_sha256']:
    raise ValueError('candidate fitting source changed')
epoch = 'servo-soft-friction-v2-expanded-validation'
e = p / 'results/phase5/development' / epoch
raw = Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw') / epoch
if e.exists() or raw.exists():
    raise ValueError('refuse evidence overwrite')
old = json.loads((p / 'results/phase5/development/servo-identification-v1-training/frozen.json').read_text())
files = {name: sha(name) for name in old['files']}
for path in [model, Path(__file__), p / 'scripts/phase5/servo_model_soft_friction_v2.py', p / 'scripts/phase5/servo_model_soft_friction_v2_test.py']:
    files[str(path)] = sha(path)
training_report = json.loads((model.parent/'training_report.json').read_text())
tests = json.loads((model.parent/'synthetic_tests.json').read_text())
if training_report['gate'] != 'PASS_LOCAL_EMPIRICAL' or tests['return_code'] != 0:
    raise ValueError('training checks must pass before new validation')
for path in [p/'scripts/phase5/servo_model_v1.py', p/'tools/phase5_adapter/servo_validation_v2.cpp', p/'build-phase5-adapter/servo_validation_v2', p/'config/phase5_development/servo_validation_soft_friction_v2_expanded.yaml', model.parent/'training_report.json', model.parent/'synthetic_tests.json', p/'scripts/phase5/validate_servo_soft_friction_expanded.py']:
    files[str(path)] = sha(path)
e.mkdir()
freeze = {'files': files, 'scope': 'frozen positive soft-friction candidate v2; independent 91012 fixture; no refit; same frozen coefficients; prospective expanded waveform/domain; preserve old-domain failures; no refit',
          'frozen_before_run_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'seed': 91012,
          'model_policy': candidate['policy']}
with (e / 'frozen.json').open('x') as out:
    out.write(json.dumps(freeze, indent=2) + '\n')
sys.path.insert(0, str(p / 'scripts/phase5'))
from materialize_identity import materialize
materialize(e / 'frozen.json')
argv = [str(p / 'build-phase5-adapter/servo_validation_v2'), str(p), str(p / 'config/phase5_development/servo_validation_soft_friction_v2_expanded.yaml'),
        'predictive', 'servo_validation', '91012', str(raw)]
env = dict(os.environ)
env['LD_LIBRARY_PATH'] = str(p / '.vendor/mujoco-3.3.7/lib') + ':' + env.get('LD_LIBRARY_PATH', '')
start = time.monotonic()
with (e / 'stdout.log').open('x') as out, (e / 'stderr.log').open('x') as err:
    code = subprocess.call(argv, env=env, cwd=p, stdout=out, stderr=err)
meta = {'argv': argv, 'return_code': code, 'wall_s': time.monotonic() - start,
        'model_prefrozen_sha256': files[str(model)], 'model_after_run_sha256': sha(model),
        'raw_files': {f.name: sha(f) for f in raw.rglob('*') if f.is_file()}}
with (e / 'execution.json').open('x') as out:
    out.write(json.dumps(meta, indent=2) + '\n')
print(json.dumps(meta, indent=2))
if meta['model_prefrozen_sha256'] != meta['model_after_run_sha256']:
    raise ValueError('model changed during independent validation')
if (raw / 'summary.yaml').exists():
    print((raw / 'summary.yaml').read_text())
if code:
    print((e / 'stderr.log').read_text())
raise SystemExit(code)

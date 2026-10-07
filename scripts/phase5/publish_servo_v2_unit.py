#!/usr/bin/env python3
"""Preserve v2 local-model unit, failed alternatives and verified frozen input closure."""
import datetime,hashlib,json,tarfile,subprocess
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion')
base=p/'results/phase5/development/servo-model-soft-friction-v2-frozen'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
figure=base/'figures/phase5_servo_soft_friction_v2.png'
with (base/'figures/visual_inspection.json').open('x') as f:f.write(json.dumps({'inspected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'image_sha256':sha(figure),'status':'PASS_PRESENTATION_LAYOUT','findings':'All four panels, legends, mrad/mrad-per-second units and conditional local scope readable without clipping. No CAD geometry units changed.'},indent=2)+'\n')
with (base/'setup_failure_record.json').open('x') as f:f.write(json.dumps({'scope':'retained setup failures before any v2 robot run','attempts':[{'command':'cmake --build build-phase5-adapter --target servo_validation_v2 -j2','exit_code':2,'error':'gmake: No rule to make target servo_validation_v2. Stop.','repair':'explicit configure existing build cache before building added target'},{'command':'python3 scripts/phase5/run_servo_soft_validation_v2.py','exit_code':1,'error':'FileNotFoundError: build-phase5-adapter/servo_validation_v2 during preflight hash','experiment_started':False,'repair':'build validation-only target before trial'}]},indent=2)+'\n')
probe=p/'results/phase5/development/servo-structural-probe-v1'
soft_source=Path('/tmp/phase5_soft_servo_training_probe_01a114d9.py')
with (probe/'soft_training_probe.py').open('x') as f:f.write(soft_source.read_text())
r=subprocess.run(['python3',str(probe/'soft_training_probe.py')],capture_output=True,text=True)
assert r.returncode==0
with (probe/'soft_training_probe.json').open('x') as f:f.write(r.stdout)
config=p/'results/phase5/development/servo-model-config-bias-v2'
r=subprocess.run(['python3',str(p/'scripts/phase5/servo_model_config_bias_v2_test.py')],capture_output=True,text=True)
with (config/'synthetic_tests.log').open('x') as f:f.write(r.stdout+r.stderr)
with (config/'synthetic_tests.json').open('x') as f:f.write(json.dumps({'return_code':r.returncode,'tests':4,'test_sha256':sha(p/'scripts/phase5/servo_model_config_bias_v2_test.py')},indent=2)+'\n')
assert r.returncode==0
freeze=json.loads((p/'results/phase5/development/servo-soft-friction-v2-validation/frozen.json').read_text())
cache=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/identity-cache')
closure=[]
for name,h in freeze['files'].items():
 blob=cache/h
 assert blob.is_file() and sha(blob)==h
 closure.append({'original_path':name,'sha256':h,'bytes':blob.stat().st_size})
with (base/'verified_input_closure.json').open('x') as f:f.write(json.dumps({'inputs':len(closure),'missing':[],'verified_storage':str(cache),'files':closure},indent=2)+'\n')
sources=['PHASE5_WRITER_STATE_20261007.json','scripts/phase5/servo_model_config_bias_v2.py','scripts/phase5/servo_model_config_bias_v2_test.py','scripts/phase5/servo_model_soft_friction_v2.py','scripts/phase5/servo_model_soft_friction_v2_test.py','scripts/phase5/run_servo_soft_validation_v2.py','scripts/phase5/validate_servo_soft_friction_v2.py','scripts/phase5/plot_servo_soft_friction_v2.py','scripts/phase5/publish_servo_v2_unit.py','tools/phase5_adapter/servo_validation_v2.cpp','tools/phase5_adapter/CMakeLists.txt','config/phase5_development/servo_validation_soft_friction_v2.yaml','reviews/phase_5_servo_soft_friction_v2_executor_review.md']
items={'project/'+name:p/name for name in sources}
for directory in [base,config,probe,p/'results/phase5/development/servo-model-soft-friction-v2',p/'results/phase5/development/servo-soft-friction-v2-validation']:
 for file in directory.rglob('*'):
  if file.is_file():items['project/'+str(file.relative_to(p))]=file
for phase,directory in [('training',Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-identification-v1-training')),('new-validation',Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-soft-friction-v2-validation'))]:
 for file in directory.rglob('*'):
  if file.is_file():items['raw/'+phase+'/'+str(file.relative_to(directory))]=file
manifest={name:{'sha256':sha(file),'bytes':file.stat().st_size} for name,file in items.items()}
with (base/'CHECKPOINT_FILE_MANIFEST.json').open('x') as f:f.write(json.dumps(manifest,indent=2)+'\n')
small={name:manifest['project/'+name] for name in sources}
for file in [base/'model.json',base/'training_report.json',base/'heldout-validation/validation_report.json',base/'figures/phase5_servo_soft_friction_v2.png',base/'figures/phase5_servo_soft_friction_v2.json',base/'figures/visual_inspection.json',config/'model.json',config/'training_report.json',probe/'training_probe.py',probe/'training_probe.json',probe/'soft_training_probe.py',probe/'soft_training_probe.json']:
 small[str(file.relative_to(p))]={'sha256':sha(file),'bytes':file.stat().st_size}
with (base/'BACKUP_SOURCE_MANIFEST.json').open('x') as f:f.write(json.dumps(small,indent=2)+'\n')
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:
 file=base/name;items['project/'+str(file.relative_to(p))]=file
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/servo-model-v2-20261007');dest.mkdir(exist_ok=False)
part=dest/'servo-model-v2-local.tar.gz.part'
with tarfile.open(part,'w:gz') as tar:
 for name,file in sorted(items.items()):tar.add(file,arcname=name,recursive=False)
archive=dest/'servo-model-v2-local.tar.gz';part.rename(archive)
with tarfile.open(archive) as tar:
 members=tar.getmembers();assert len(members)==len(items)
 for member in members:
  assert member.isfile() and member.name in items
  assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==sha(items[member.name])
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(items),'archive_members_verified':True,'input_cache_verified_on_dell':len(closure),'mac_copy_verified':False,'scope':'local soft-friction model; failed alternatives retained; Phase5 unaccepted','source_manifest':str(base/'BACKUP_SOURCE_MANIFEST.json'),'source_manifest_sha256':sha(base/'BACKUP_SOURCE_MANIFEST.json')}
with (dest/'READY.json.part').open('x') as f:f.write(json.dumps(ready,indent=2)+'\n')
(dest/'READY.json.part').rename(dest/'READY.json')
print(json.dumps(ready,indent=2))

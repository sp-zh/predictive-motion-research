#!/usr/bin/env python3
"""Immutable expanded-waveform guard failure, preserving original frozen model."""
import datetime,hashlib,json,tarfile
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/servo-soft-friction-v2-expanded-validation'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
image=base/'figures/phase5_servo_expanded_guard_failure.png'
with (base/'figures/visual_inspection.json').open('x') as f:f.write(json.dumps({'image_sha256':sha(image),'inspected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_PRESENTATION_LAYOUT','findings':'Three recorded panels, accepted versus physical quantities, native rejection, absent stop and clearance caveat legible without clipping; no CAD geometry changed.'},indent=2)+'\n')
freeze=json.loads((base/'frozen.json').read_text());cache=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/identity-cache');closure=[]
for name,h in freeze['files'].items():
 f=cache/h;assert f.exists() and sha(f)==h;closure.append({'original_path':name,'sha256':h,'bytes':f.stat().st_size})
with (base/'verified_input_closure.json').open('x') as f:f.write(json.dumps({'inputs':len(closure),'missing':[],'verified_storage':str(cache),'files':closure},indent=2)+'\n')
source=['scripts/phase5/run_servo_expanded_validation_v2.py','scripts/phase5/validate_servo_soft_friction_expanded.py','scripts/phase5/plot_servo_expanded_failure.py','scripts/phase5/publish_servo_expanded_failure.py','config/phase5_development/servo_validation_soft_friction_v2_expanded.yaml','reviews/phase_5_servo_expanded_validation_failure_20261007.md']
items={'project/'+name:p/name for name in source}
for f in base.rglob('*'):
 if f.is_file():items['project/'+str(f.relative_to(p))]=f
raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-soft-friction-v2-expanded-validation')
for f in raw.rglob('*'):
 if f.is_file():items['raw/'+str(f.relative_to(raw))]=f
model=p/'results/phase5/development/servo-model-soft-friction-v2-frozen/model.json';items['project/'+str(model.relative_to(p))]=model
manifest={name:{'sha256':sha(f),'bytes':f.stat().st_size} for name,f in items.items()}
with (base/'CHECKPOINT_FILE_MANIFEST.json').open('x') as f:f.write(json.dumps(manifest,indent=2)+'\n')
small={name:manifest['project/'+name] for name in source}
for f in [base/'model-audit/validation_report.json',base/'partial_trace_diagnostics.json',base/'figures/phase5_servo_expanded_guard_failure.png',base/'figures/phase5_servo_expanded_guard_failure.json',base/'figures/visual_inspection.json']:
 small[str(f.relative_to(p))]={'sha256':sha(f),'bytes':f.stat().st_size}
with (base/'BACKUP_SOURCE_MANIFEST.json').open('x') as f:f.write(json.dumps(small,indent=2)+'\n')
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:
 f=base/name;items['project/'+str(f.relative_to(p))]=f
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/servo-expanded-failure-20261007');dest.mkdir(exist_ok=False)
part=dest/'servo-expanded-failure.tar.gz.part'
with tarfile.open(part,'w:gz') as t:
 for name,f in sorted(items.items()):t.add(f,arcname=name,recursive=False)
archive=dest/'servo-expanded-failure.tar.gz';part.rename(archive)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(items)
 for m in t.getmembers():
  assert m.isfile() and m.name in items and hashlib.sha256(t.extractfile(m).read()).hexdigest()==sha(items[m.name])
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(items),'archive_members_verified':True,'input_cache_verified_on_dell':len(closure),'mac_copy_verified':False,'scope':'retained incomplete expanded validation/command guard failure; no enlarged model domain/stop/Phase5 acceptance','source_manifest':str(base/'BACKUP_SOURCE_MANIFEST.json'),'source_manifest_sha256':sha(base/'BACKUP_SOURCE_MANIFEST.json')}
with (dest/'READY.json.part').open('x') as f:f.write(json.dumps(ready,indent=2)+'\n')
(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2))

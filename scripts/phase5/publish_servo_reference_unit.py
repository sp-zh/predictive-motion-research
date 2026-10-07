#!/usr/bin/env python3
import datetime,hashlib,json,tarfile
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/servo-safe-reference-unit-20261007';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
review=p/'reviews/phase_5_servo_safe_reference_failures_20261007.md'
review.write_text('''# Phase5 curated-reference executor failures

Both prospectively frozen development runs used seed91012 and unchanged model SHA984ee85d086aeba7da8260a20b21b301e23dfd2c698a6c61ace0ff956bbec1bb. Both are FAIL_GUARD_OR_INCOMPLETE_TRACE. Phase5 remains unaccepted; main MPC untouched. These are curated previously seen accepted inputs, not untouched held-out trials. Original runner/summary generic held-out wording is inaccurate and retained as provenance only.

Reference source moving-stop-v1 raw SHA cdd840c3ab68a02ad4e22c8e7fe7fb8991257aab2133e57ff88fc343768f3481 exports only accepted target offsets and command velocity (928 cycles), no old physical state columns. Source input roster:500 warmup,195 motion,233 recorded braking. Actual fresh guard execution and fresh shared stop are separately recorded. Both retain original SI1e-7 acceptance, SOLVED-only, physical/command limits, nonlinear measured/accepted target guards and50ms command/stop checks; neither proves online250Hz. v2 had234 full-cycle deadline misses.

v1 position-error chase ran through tick792 (3.172s), then primary and shared stop INFEASIBLE_BOUNDS, no stop command. Joint3 w=-.061980006326262695 rad/s, alpha=-.51999999999999091 rad/s². With dt=.004,J=20,next alpha∈[-.60,-.44],next w∈[-.0643800063263,-.0637400063263], inconsistent with -.0625 hard lower speed bound by .00124000632626 rad/s. Raw generic excitation labels remain unchanged; report annotates500 warmup/195 reference motion/98 reference braking, not a fresh completed stop.

v2 requests original accepted w directly, actual target integrates guarded accepted w, without position catch-up. Native primary CONSTRAINT_VIOLATION at tick701 triggers fresh shared stop, which completes at tick927 (3.712s). Actual roster500 warmup/195 motion/6 recorded braking/227 fresh shared stop; hold never reached. Max accepted speed .0180999726125 rad/s, physical speed .0299222377166 rad/s, minimum clearance .0155670314094m. Saved first rejected full QP matrices; cycles logs report the accepted stop SOLVED, so first non-SOLVED cycle cannot locate primary rejection. Precise rejected numerical row cause remains for independent audit; no infeasibility claim for this rejection.

No refit, metadata domain enlargement, threshold tuning or deletion of transition windows. Both scorers reject the guard/incomplete trace before predictor success scoring. Failure source/binaries/configs/freeze/raw and pre-run cache identities preserved. Diagram records physical/accepted joint3 velocity and actual clearance from all complete substep2 rows; units radians/s,seconds,mm, not controller-performance certification. No model geometry change; actual recorded-state render from prior backed stop diagnostic remains relevant and unchanged. Local source inspection confirms finite-jerk velocity continuation is a separate pending isolated analysis, not implemented in these runs and not position/geometry future stopping proof.
''')
image=base/'phase5_servo_reference_failures.png'
(base/'visual_inspection.json').write_text(json.dumps({'image_sha256':sha(image),'status':'PASS_PRESENTATION_LAYOUT','inspected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'findings':'Both full traces, labels, hard limits and failure/stop outcomes visible with no clipping; no CAD change.'},indent=2)+'\n')
sources=['tools/phase5_servo_reference/CMakeLists.txt','tools/phase5_servo_reference/servo_safe_reference_fixture.cpp','tools/phase5_servo_reference/servo_safe_reference_velocity_fixture.cpp','scripts/phase5/prepare_servo_safe_reference.py','scripts/phase5/run_servo_safe_reference.py','scripts/phase5/run_servo_safe_reference_v2.py','scripts/phase5/validate_servo_safe_reference.py','scripts/phase5/validate_servo_safe_reference_v2.py','scripts/phase5/analyze_servo_reference_unit.py','scripts/phase5/publish_servo_reference_unit.py','config/phase5_development/servo_validation_safe_reference_v1.yaml','config/phase5_development/servo_validation_safe_reference_v2.yaml',str(review.relative_to(p))]
items={'project/'+s:p/s for s in sources};closures=[];cache=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/identity-cache')
for ver in ('v1','v2'):
 d=p/('results/phase5/development/servo-safe-reference-'+ver+'-validation');freeze=json.loads((d/'frozen.json').read_text())
 for name,h in freeze['files'].items():
  f=cache/h;assert f.is_file() and sha(f)==h;closures.append({'run':ver,'original_path':name,'sha256':h,'bytes':f.stat().st_size})
  if '/tools/phase5_servo_reference/' in name or '/build-servo-safe-reference-v1/' in name or 'servo_validation_safe_reference_' in name or '/scripts/phase5/run_servo_safe_reference' in name or '/scripts/phase5/validate_servo_safe_reference' in name:items['frozen-input-cache/'+h]=f
 for f in d.rglob('*'):
  if f.is_file():items['project/'+str(f.relative_to(p))]=f
 raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw')/('servo-safe-reference-'+ver+'-validation')
 for f in raw.rglob('*'):
  if f.is_file():items['raw/'+ver+'/'+str(f.relative_to(raw))]=f
for d in (base,p/'results/phase5/development/servo-safe-reference-v1'):
 for f in d.rglob('*'):
  if f.is_file():items['project/'+str(f.relative_to(p))]=f
(base/'verified_input_closure.json').write_text(json.dumps({'inputs_per_run':192,'total_references':len(closures),'unique_hashes':len(set(x['sha256'] for x in closures)),'all_verified_on_dell':True,'cache':str(cache),'mac_cache_verification':False,'files':closures},indent=2)+'\n')
items['project/'+str((base/'verified_input_closure.json').relative_to(p))]=base/'verified_input_closure.json'
manifest={k:{'sha256':sha(v),'bytes':v.stat().st_size} for k,v in items.items()};(base/'CHECKPOINT_FILE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
small={s:manifest['project/'+s] for s in sources}
for name in ['reference_failure_report.json','phase5_servo_reference_failures.png','phase5_servo_reference_failures.json','visual_inspection.json']:
 f=base/name;small[str(f.relative_to(p))]={'sha256':sha(f),'bytes':f.stat().st_size}
(base/'BACKUP_SOURCE_MANIFEST.json').write_text(json.dumps(small,indent=2)+'\n')
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:items['project/'+str((base/name).relative_to(p))]=base/name
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/servo-safe-reference-failures-20261007');dest.mkdir(exist_ok=False);part=dest/'servo-safe-reference-failures.tar.gz.part'
with tarfile.open(part,'w:gz') as tar:
 for name,f in sorted(items.items()):tar.add(f,arcname=name,recursive=False)
archive=dest/'servo-safe-reference-failures.tar.gz';part.rename(archive)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(items)
 for m in tar.getmembers():assert m.isfile() and m.name in items and hashlib.sha256(tar.extractfile(m).read()).hexdigest()==sha(items[m.name])
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(items),'archive_members_verified':True,'input_cache_references_verified_on_dell':len(closures),'mac_copy_verified':False,'source_manifest':str(base/'BACKUP_SOURCE_MANIFEST.json'),'source_manifest_sha256':sha(base/'BACKUP_SOURCE_MANIFEST.json'),'scope':'Retained two curated-reference failures; v2 fresh shared stop completed; no model expansion, online success or Phase5 acceptance'}
(dest/'READY.json.part').write_text(json.dumps(ready,indent=2)+'\n');(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2))

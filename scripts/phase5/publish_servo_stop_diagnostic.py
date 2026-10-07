#!/usr/bin/env python3
"""Immutable reconstruction + matched replay + actual infeasible stop checkpoint."""
import datetime,hashlib,json,tarfile
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/servo-expanded-failure-stop-replay-v1';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
cases=[p/'results/phase5/development/servo-expanded-qp-reconstruction-v1',base]
cache=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/identity-cache')
for case in cases:
 freeze=json.loads((case/'frozen.json').read_text());files=[]
 for name,h in freeze['files'].items():
  blob=cache/h;assert blob.is_file() and sha(blob)==h;files.append({'original_path':name,'sha256':h,'bytes':blob.stat().st_size})
 with (case/'verified_input_closure.json').open('x') as f:f.write(json.dumps({'inputs':len(files),'missing':[],'verified_storage':str(cache),'files':files},indent=2)+'\n')
with (base/'figures/visual_inspection.json').open('x') as f:f.write(json.dumps({'inspected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_PRESENTATION_LAYOUT_AND_UNITS','images':{name:sha(base/'figures'/name) for name in ['phase5_servo_no_feasible_stop.png','phase5_servo_guard_failure_state.png']},'findings':'Next-candidate command label corrected; support ranges, original guards, nonzero final speeds and lack of stop legible. Actual MuJoCo pose render uses metres/radians and unchanged CAD/source assets, no control/dynamics stepping.'},indent=2)+'\n')
sources=['tools/phase5_adapter/reconstruct_servo_failure_qp.cpp','tools/phase5_adapter/replay_servo_expanded_failure_stop.cpp','tools/phase5_servo_diagnostics/CMakeLists.txt','tools/phase5_servo_diagnostics/render_servo_recorded_pose.cpp','scripts/phase5/run_servo_qp_reconstruction.py','scripts/phase5/run_servo_failure_stop_replay.py','scripts/phase5/analyze_reconstructed_servo_qp.py','scripts/phase5/analyze_servo_stop_qp.py','scripts/phase5/check_servo_replay_contract.py','scripts/phase5/plot_servo_stop_feasibility.py','scripts/phase5/annotate_servo_failure_render.py','scripts/phase5/publish_servo_stop_diagnostic.py','reviews/phase_5_servo_failure_stop_diagnostic_20261007.md']
items={'project/'+name:p/name for name in sources}
for case in cases:
 for f in case.rglob('*'):
  if f.is_file():items['project/'+str(f.relative_to(p))]=f
raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-soft-friction-v2-expanded-validation/raw.csv');items['raw/original-expanded-failure.csv']=raw
manifest={name:{'sha256':sha(f),'bytes':f.stat().st_size} for name,f in items.items()}
with (base/'CHECKPOINT_FILE_MANIFEST.json').open('x') as f:f.write(json.dumps(manifest,indent=2)+'\n')
small={name:manifest['project/'+name] for name in sources}
for f in [base/'replay-stop/summary.yaml',base/'stop_feasibility_analysis.json',base/'contract-negative-control/result.json',base/'figures/phase5_servo_no_feasible_stop.png',base/'figures/phase5_servo_no_feasible_stop.json',base/'figures/phase5_servo_guard_failure_state.png',base/'figures/phase5_servo_guard_failure_state.json',base/'figures/visual_inspection.json',cases[0]/'feasibility_analysis.json']:
 small[str(f.relative_to(p))]={'sha256':sha(f),'bytes':f.stat().st_size}
with (base/'BACKUP_SOURCE_MANIFEST.json').open('x') as f:f.write(json.dumps(small,indent=2)+'\n')
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:
 f=base/name;items['project/'+str(f.relative_to(p))]=f
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/servo-stop-diagnostic-20261007');dest.mkdir(exist_ok=False);part=dest/'servo-stop-diagnostic.tar.gz.part'
with tarfile.open(part,'w:gz') as t:
 for name,f in sorted(items.items()):t.add(f,arcname=name,recursive=False)
archive=dest/'servo-stop-diagnostic.tar.gz';part.rename(archive)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(items)
 for m in t.getmembers():assert m.isfile() and hashlib.sha256(t.extractfile(m).read()).hexdigest()==sha(items[m.name])
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(items),'archive_members_verified':True,'input_cache_verified_on_dell':{'reconstruction':193,'replay_stop':193},'mac_copy_verified':False,'scope':'explicit reconstruction and actual matched-prefix stop failure; no completed stop/expanded model/Phase5 acceptance','source_manifest':str(base/'BACKUP_SOURCE_MANIFEST.json'),'source_manifest_sha256':sha(base/'BACKUP_SOURCE_MANIFEST.json')}
with (dest/'READY.json.part').open('x') as f:f.write(json.dumps(ready,indent=2)+'\n')
(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2))

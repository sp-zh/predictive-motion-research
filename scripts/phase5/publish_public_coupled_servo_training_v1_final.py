#!/usr/bin/env python3
"""Retain failed publication, finish the same work unit with regular byte members."""
import datetime,hashlib,json,tarfile
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/public-coupled-servo-v1-training';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();freeze=json.loads((base/'frozen.json').read_text());assert all(sha(f)==h for f,h in freeze['files'].items());initial=json.loads((base/'CHECKPOINT_FILE_MANIFEST.json').read_text());cache=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/identity-cache')
failure=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-coupled-servo-v1-training-20261007/FAILURE.json');failed=json.loads(failure.read_text());assert sha(failure.with_name('public-coupled-servo-v1-training.tar.gz'))==failed['archive_sha256']
closure=json.loads((base/'post_run_transitive_asset_closure.json').read_text());assert closure['all_current_bytes_equal_original_TRAIN']
review=p/'reviews/phase_5_public_coupled_servo_training_v1_scope_20261007.md';review.write_text('''# Public coupled v1 scope and publication supplement

Original v1model/solver/runner/static-reader source and40-input freeze remain unchanged. Recorded training results are limited to this fixed public compiled baseline and original91011 conditional windows. No calibration or new candidate was created during packaging repair.

Root review found v1B code includes a factor solref damping ratio; the standard positive-solref friction B formula excludes that factor. All seven currently frozen damping ratios are exactly1, so current coefficient B=105.2631579 and recorded TRAIN results are unchanged. This is a generic-parameter formula defect, not a generic-model PASS. After this workunit backup, a separate version must correct/restrict supported parameters before new prospective validation. Do not repair the old frozen source or relabel it exact engine.

Original40pre-scan files omitted transitive XML/mesh assets. post_run_transitive_asset_closure.json records40current XML/asset files from38asset references. Each file matches the original176-input TRAIN freeze SHA and immutable Dell-cache bytes. This is explicitly post-run closure verification; no backdated prefreeze claim. Reuse old cache identities rather than republishing all mesh bytes. NumPy/BLAS supplemental identity is also post-run only, with its previously stated provenance limitation.

Initial main archive retained at checkpoints/public-coupled-servo-v1-training-20261007: SHAe0b6d0110561e90682df85db65af6bc3df82fc8b43cf5199255693a02838f79b,26924907bytes. Its verification failed on four runtime library symlink members; it has FAILURE.json and no READY, must not be extracted as a verified payload. This was a publication failure, not a predictor/experimental failure. Exact initial manifest/source/failed archive retained. Final archive dereferences each library to regular bytes, checks every member against the SHA/size manifest and safe relative names, then publishes separate READY. No initial archive is overwritten.

The final successful checkpoint remains the same training-only workunit; original scalar/expanded/native-stop/API failures remain retained. Root independently reviews mathematics/causality/closure, updates showcase and owns private Git backup. Phase5 remains unaccepted; no new physical validation or main-MPC integration is authorized by training accuracy alone.
''')
items={}
post=json.loads((base/'numerical_runtime_after_run.json').read_text())['files']
for name in initial:
 if name.startswith('project/'):items[name]=p/name[len('project/'):]
 elif name.startswith('frozen-input-cache/'):items[name]=cache/name.split('/')[-1]
 elif name.startswith('post-run-runtime/'):
  h=name.split('/')[-1];items[name]=next(Path(f).resolve() for f,m in post.items() if m['sha256']==h)
 else:raise ValueError(name)
items['retained-initial/CHECKPOINT_FILE_MANIFEST.json']=base/'CHECKPOINT_FILE_MANIFEST.json';items['retained-initial/BACKUP_SOURCE_MANIFEST.json']=base/'BACKUP_SOURCE_MANIFEST.json';items['retained-initial/FAILURE.json']=failure
sources=['scripts/phase5/verify_public_servo_post_assets_v1.py','scripts/phase5/publish_public_coupled_servo_training_v1_final.py',str(review.relative_to(p))]
for name in sources:items['project/'+name]=p/name
for name in ['post_run_transitive_asset_closure.json','materialized-identity.json']:
 f=base/name;items['project/'+str(f.relative_to(p))]=f
manifest={name:{'sha256':sha(f),'bytes':f.stat().st_size} for name,f in items.items()};final_manifest=base/'CHECKPOINT_FILE_MANIFEST_FINAL.json';final_manifest.write_text(json.dumps(manifest,indent=2)+'\n');small=json.loads((base/'BACKUP_SOURCE_MANIFEST.json').read_text())
for name in sources:small[name]={'sha256':sha(p/name),'bytes':(p/name).stat().st_size}
f=base/'post_run_transitive_asset_closure.json';small[str(f.relative_to(p))]={'sha256':sha(f),'bytes':f.stat().st_size};small_manifest=base/'BACKUP_SOURCE_MANIFEST_FINAL.json';small_manifest.write_text(json.dumps(small,indent=2)+'\n')
for f in [final_manifest,small_manifest]:items['project/'+str(f.relative_to(p))]=f
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-coupled-servo-v1-training-final-20261007');dest.mkdir(exist_ok=False);part=dest/'public-coupled-servo-v1-training-final.tar.gz.part'
with tarfile.open(part,'w:gz',dereference=True) as t:
 for name,f in sorted(items.items()):t.add(f,arcname=name,recursive=False)
archive=dest/'public-coupled-servo-v1-training-final.tar.gz';part.rename(archive)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(items)
 for m in t.getmembers():assert m.isfile() and m.name in items and not m.name.startswith('/') and '..' not in Path(m.name).parts and hashlib.sha256(t.extractfile(m).read()).hexdigest()==sha(items[m.name])
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(items),'archive_members_verified':True,'pre_recorded_input_cache_verified':40,'post_run_transitive_assets_same_original_TRAIN':40,'pre_run_complete_environment_claim':False,'mac_copy_verified':False,'source_manifest':str(small_manifest),'source_manifest_sha256':sha(small_manifest),'retained_failed_publication':failed,'scope':'Fixed ratio1 public baseline conditional TRAIN91011 PASS only; generic B defect retained/restricted; no exact-engine/holdout/controller/Phase5 acceptance'};(dest/'READY.json.part').write_text(json.dumps(ready,indent=2)+'\n');(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2))

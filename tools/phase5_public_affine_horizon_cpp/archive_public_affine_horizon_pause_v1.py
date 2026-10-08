"""Checkpoint preservation only after human stop; no kernel/model/checker calls."""
import hashlib,json,tarfile,shutil
from pathlib import Path
ROOT=Path('/home/codextransfer/predictive_motion')
BASE=ROOT/'results/phase5/development/public-affine-horizon-cpp-v1'
SRC=ROOT/'tools/phase5_public_affine_horizon_cpp'
OUT=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-affine-horizon-cpp-v1-20261008')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
freeze=BASE/'frozen_before_predictions.json';assert sha(freeze)=='d3d4253c0173aae4ad3072eea37268713bd3710b68cfa05720e79f906bf97429'
frozen=json.loads(freeze.read_text());assert frozen['nonempty_calls']==0
for e in frozen['dependencies']:assert sha(Path(e['path']))==e['sha256'] and sha(BASE/e['cache'])==e['sha256']
OUT.mkdir(parents=True,exist_ok=False)
pause={'human_instruction':'完成当前最小工作后就保存，上传git，不要继续了','scope':'SAVE_CURRENT_MINIMAL_BUILD_EMPTY_PREFLIGHT_FREEZE_AND_PRIVATE_GIT_BACKUP_THEN_STOP','phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED','nonempty_calls':0,'no_future_run_release':True,'freeze_sha256':sha(freeze),'binary_sha256':frozen['binary_sha256'],'accepted_phase4_and_all_failures_preserved':True,'private_git_backup':'PENDING_ROOT_IMPORT_PUSH_REMOTE_VERIFICATION'}
with (BASE/'PAUSE_SAVE_RECORD.json').open('x') as g:json.dump(pause,g,indent=2,ensure_ascii=False);g.write('\n')
shutil.copyfile(Path(__file__),BASE/Path(__file__).name)
small=[p for p in SRC.iterdir() if p.is_file()]
small_manifest={'files':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(small)},'scope':'CURRENT_SOURCE_INCLUDING_REVIEWED_COMPATIBILITY_FIX_AND_BUILD_FREEZE_HELPERS_NO_NONEMPTY_OUTPUT'}
with (BASE/'SMALL_SOURCE_MANIFEST.json').open('x') as g:json.dump(small_manifest,g,indent=2);g.write('\n')
payload=[]
for p in sorted(BASE.rglob('*')):
 if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':payload.append((p,'project/results/phase5/development/public-affine-horizon-cpp-v1/'+str(p.relative_to(BASE))))
for p in sorted(small):payload.append((p,'project/tools/phase5_public_affine_horizon_cpp/'+p.name))
manifest={'files':{name:{'sha256':sha(p),'bytes':p.stat().st_size} for p,name in payload},'freeze_sha256':sha(freeze),'dependency_count':len(frozen['dependencies']),'nonempty_calls':0,'all_live_cache_verified_before_archive':True}
with (BASE/'CHECKPOINT_FILE_MANIFEST.json').open('x') as g:json.dump(manifest,g,indent=2);g.write('\n')
payload.append((BASE/'CHECKPOINT_FILE_MANIFEST.json','project/results/phase5/development/public-affine-horizon-cpp-v1/CHECKPOINT_FILE_MANIFEST.json'))
archive=OUT/'public-affine-horizon-cpp-v1.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
 for p,name in payload:tar.add(p,arcname=name,recursive=False)
with tarfile.open(archive,'r:gz') as tar:
 members={m.name:m for m in tar.getmembers()};assert len(members)==len(payload)
 for name,v in manifest['files'].items():
  m=members[name];assert m.isfile();assert m.size==v['bytes'];assert hashlib.sha256(tar.extractfile(m).read()).hexdigest()==v['sha256']
ready={'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'archive':str(archive),'regular_files':len(payload),'verified_payloads':len(manifest['files']),'small_source_files':len(small),'small_source_manifest_sha256':sha(BASE/'SMALL_SOURCE_MANIFEST.json'),'checkpoint_manifest_sha256':sha(BASE/'CHECKPOINT_FILE_MANIFEST.json'),'freeze_sha256':sha(freeze),'binary_sha256':frozen['binary_sha256'],'dependency_count':len(frozen['dependencies']),'Dell_all_archive_payloads_and_live_cache_verified':True,'Mac_verified':False,'nonempty_calls':0,'phase5':'NOT_ACCEPTED','project_action':'SAVE_AND_STOP_NO_FURTHER_DISPATCH','private_git_backup':'PENDING_ROOT_PUSH_REMOTE_VERIFICATION'}
with (OUT/'READY.json').open('x') as g:json.dump(ready,g,indent=2);g.write('\n')
print(json.dumps(ready),flush=True)

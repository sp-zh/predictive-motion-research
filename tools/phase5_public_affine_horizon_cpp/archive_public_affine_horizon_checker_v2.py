"""Preservation only: .part, member verification, final rename, READY last."""
import hashlib,json,os,shutil,tarfile
from pathlib import Path
ROOT=Path('/home/codextransfer/predictive_motion')
BASE=ROOT/'results/phase5/development/public-affine-horizon-checker-v2'
INSTALL=ROOT/'results/phase5/development/public-affine-horizon-checker-v2-installation'
SRC=ROOT/'tools/phase5_public_affine_horizon_cpp'
OUT=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-affine-horizon-checker-v2-20261008')
FREEZE_SHA='ec1b76a234e63c3dd6e3cb576d60ba1ef99c9130985690a4ba9313882071994f'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest()
def write(p,d):
 with p.open('x') as f:json.dump(d,f,indent=2,allow_nan=False);f.write('\n')
freeze=BASE/'frozen_before_predictions_v2.json';assert sha(freeze)==FREEZE_SHA
d=json.loads(freeze.read_text());assert d['file_count']==2921 and d['nonempty_calls']==0 and d['run_release'].startswith('NOT_GRANTED')
for e in d['files']:assert sha(Path(e['path']))==e['sha256'] and sha(Path(e['immutable_copy']))==e['sha256']
assert (INSTALL/'freeze_attempt1.exit').read_text().strip()=='0'
OUT.mkdir(parents=True,exist_ok=False)
record={'scope':'FREEZE_ONLY_FIRST_ATTEMPT_NO_KERNEL_CHECKER_MODEL_PLANT_CALLS','exit':0,
 'argv':['python3',str(SRC/'freeze_public_affine_horizon_checker_v2.py'),'--output',str(BASE),
 '--source-checkpoint','281d1f304ef99b9675d7e3ab6bdf0ae95ea7c59d','--self-sha','589872b80bc0a58b4d01c6b5a3ba5f7de90f0f3837ae450f058617eac7fedb2f',
 '--checker-review',str(ROOT/'reviews/evidence/public_affine_horizon_checker_v2_source_review_20261008.json'),
 '--checker-review-sha','eea5dba03e74f4c9d7aac6af60c2f3e194a5a0a7b54209115a6b9f5ba66bc954',
 '--state-sha','0e6a8c5c78e036701987c1aac4cef6c3afb099648ca448acd798b9b87f1e28e3',
 '--agents-sha','8b591ec2fdac809992a27e0c2c42cb860810e9c72e759e294e6862b1f458ce3b',
 '--additional-pinned',str(ROOT/'reviews/evidence/public_affine_horizon_checker_v2_freeze_source_review_20261008.json'),'afcc6d8f056c4e2e5e8dbd89110a9030e867b1d0c47efc4834452d1f11c609e0',
 '--additional-pinned',str(ROOT/'reviews/evidence/public_affine_horizon_algebra_execution_plan_v2_20261008.json'),'6023d3362fbdf5b0d7523e05c3e602bcce4ca5e9d640d94f22fdbd9df042ee0c',
 '--additional-pinned',str(ROOT/'reviews/evidence/public_affine_horizon_checker_v2_source_change_20261008.json'),'48b076bd097cea32ae5514390b130ae49d38b21f82df728e08906a6e9f70d9dd'],
 'freeze_sha256':FREEZE_SHA,'retained_old_freeze_sha256':d['old_freeze_sha256'],
 'binary_sha256':d['binary_sha256'],'checker_v2_sha256':d['new_checker_sha256'],
 'nonempty_calls':0,'run_release':'NOT_GRANTED','phase5':'NOT_ACCEPTED'}
write(INSTALL/'FREEZE_EXECUTION_RECORD.json',record)
shutil.copyfile(Path(__file__),INSTALL/Path(__file__).name)
payload=[]
for directory,label in ((BASE,'project/results/phase5/development/public-affine-horizon-checker-v2/'),
                        (INSTALL,'project/results/phase5/development/public-affine-horizon-checker-v2-installation/')):
 for p in sorted(directory.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':payload.append((p,label+str(p.relative_to(directory))))
sources=[SRC/'verify_public_affine_horizon_v2.py',SRC/'freeze_public_affine_horizon_checker_v2.py']
for p in sources:payload.append((p,'project/tools/phase5_public_affine_horizon_cpp/'+p.name))
small={'files':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in sources}}
write(INSTALL/'SMALL_SOURCE_MANIFEST.json',small)
payload.append((INSTALL/'SMALL_SOURCE_MANIFEST.json','project/results/phase5/development/public-affine-horizon-checker-v2-installation/SMALL_SOURCE_MANIFEST.json'))
manifest={'files':{name:{'sha256':sha(p),'bytes':p.stat().st_size} for p,name in payload},
 'freeze_sha256':FREEZE_SHA,'frozen_file_count':len(d['files']),'legacy2912_preserved':True,'nonempty_calls':0}
manifest_path=INSTALL/'CHECKPOINT_FILE_MANIFEST.json';write(manifest_path,manifest)
payload.append((manifest_path,'project/results/phase5/development/public-affine-horizon-checker-v2-installation/CHECKPOINT_FILE_MANIFEST.json'))
part=OUT/'public-affine-horizon-checker-v2.tar.gz.part';final=OUT/'public-affine-horizon-checker-v2.tar.gz'
with tarfile.open(part,'w:gz',compresslevel=6) as t:
 for p,name in payload:t.add(p,arcname=name,recursive=False)
with tarfile.open(part,'r:gz') as t:
 members={m.name:m for m in t.getmembers()};assert len(members)==len(payload) and all(m.isfile() for m in members.values())
 for name,e in manifest['files'].items():
  m=members[name];assert m.size==e['bytes'] and hashlib.sha256(t.extractfile(m).read()).hexdigest()==e['sha256']
 assert hashlib.sha256(t.extractfile('project/results/phase5/development/public-affine-horizon-checker-v2-installation/CHECKPOINT_FILE_MANIFEST.json').read()).hexdigest()==sha(manifest_path)
for e in d['files']:assert sha(Path(e['path']))==e['sha256'] and sha(Path(e['immutable_copy']))==e['sha256']
part_digest=sha(part);part_size=part.stat().st_size
os.rename(part,final);assert sha(final)==part_digest
ready={'archive':str(final),'archive_sha256':part_digest,'archive_bytes':part_size,'regular_files':len(payload),
 'verified_payloads':len(manifest['files']),'checkpoint_manifest_sha256':sha(manifest_path),
 'small_source_manifest_sha256':sha(INSTALL/'SMALL_SOURCE_MANIFEST.json'),'small_source_files':len(sources),
 'freeze_sha256':FREEZE_SHA,'frozen_file_count':len(d['files']),'legacy2912_preserved':True,
 'binary_sha256':d['binary_sha256'],'checker_v2_sha256':d['new_checker_sha256'],
 'Dell_all_members_live_immutable_verified':True,'Mac_verified':False,'nonempty_calls':0,
 'run_release':'NOT_GRANTED','private_git_backup':'PENDING_ROOT_CHECKPOINT','phase5':'NOT_ACCEPTED'}
write(OUT/'READY.json',ready)
print(json.dumps(ready),flush=True)

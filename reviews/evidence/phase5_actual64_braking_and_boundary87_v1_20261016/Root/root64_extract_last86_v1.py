from pathlib import Path
import os,sys,json,hashlib,tarfile
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write_bytes
O=Path('/private/tmp/root64_actual_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);E=O/'cycle86';E.mkdir();M=Path('/private/tmp/phase5_roundoff_command64_source_v1_20261016/full_archive64_v1/readback');items={e['path']:e for e in json.loads((M/'SOURCE_MANIFEST.json').read_text())['files']};base='native64/run-attempt1/artifacts/cycle-86/trial-0/';names=['MANIFEST.yaml','inline_qp.bin','planning_guard.bin','candidate_value.bin','candidate_validation.bin','observation_before.bin','original_nominal.bin','validation_initial.bin','observation_after.bin'];want={base+n for n in names};assert sum(items[n]['bytes']for n in want)<32*1024**2;seen=set()
with tarfile.open('transfer/cold-backups/native64-complete-20261016-v1/complete64.tar.gz','r|gz')as tf:
 for e in tf:
  if e.name not in want:continue
  a=items[e.name];assert e.isfile()and e.size==a['bytes'];b=tf.extractfile(e).read(e.size+1);assert len(b)==e.size and hashlib.sha256(b).hexdigest()==a['sha256'];bounded_write_bytes(E/Path(e.name).name,b);seen.add(e.name)
  if seen==want:break
assert seen==want
print({'extracted_files':len(seen),'bytes':sum(items[n]['bytes']for n in want),'all_SHA_bound_to_full_archive':True})

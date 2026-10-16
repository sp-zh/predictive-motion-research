from pathlib import Path
import tarfile,json,hashlib,sys,os
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write_bytes
O=Path('/private/tmp/root63_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O)
M=Path('/private/tmp/phase5_current_braking_nominal63_source_v1_20261016/full_archive63_v2/readback')
items={x['path']:x for x in json.loads((M/'SOURCE_MANIFEST.json').read_text())['files']}
base='native63/run-attempt1/artifacts/cycle-53/trial-0/'
(O/'actual53').mkdir(exist_ok=False)
want={base+n for n in ['stop_objective_mode.bin','inline_qp.bin','MANIFEST.yaml']};assert sum(items[n]['bytes']for n in want)<32*1024**2
seen=set()
with tarfile.open('transfer/cold-backups/native63-complete-20261016-v2/complete63.tar.gz','r|gz')as tf:
 for e in tf:
  if e.name not in want:continue
  a=items[e.name];assert e.isfile()and e.size==a['bytes'];b=tf.extractfile(e).read(e.size+1);assert len(b)==e.size and hashlib.sha256(b).hexdigest()==a['sha256'];bounded_write_bytes(O/'actual53'/Path(e.name).name,b);seen.add(e.name)
  if seen==want:break
assert seen==want
print(json.dumps({'extracted':len(seen),'bytes':sum(items[n]['bytes']for n in want),'all_payload_SHA_match_full_archive':True}))

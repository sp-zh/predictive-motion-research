from pathlib import Path
import os,sys,json,tarfile,hashlib
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write,bounded_write_bytes
O=Path('/private/tmp/root65_actual_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O)
B=Path('/Users/uot/Documents/ChatGPT/ros/transfer/cold-backups/native65-complete-direct-mac-20261016-v1');rows=json.loads((B/'SOURCE_MANIFEST.json').read_text())['files'];M={e['path']:e for e in rows}
S=json.loads(Path('/private/tmp/phase5_physical_braking65_source_v1_20261016/postnative65-metadata-readback-v1/DERIVED_TERMINAL65_SUMMARY.json').read_text())
A='native65/run-attempt1/artifacts/';full=[A+x+'/'for x in ['cycle-32/trial-0','cycle-49/trial-0','cycle-50/trial-0']]
wanted={n for n in M if n.startswith(A)and('/'not in n[len(A):]or any(n.startswith(x)for x in full))}
for cycle in range(32,51):
 for name in ['stop_objective_mode.bin','observation_before.bin','MANIFEST.yaml']:wanted.add(A+f'cycle-{cycle}/trial-0/'+name)
 prev=next(x for x in S['actual_after_snapshots']if x['tick']==cycle)['path'];parent=prev.rsplit('/',1)[0]
 for name in ['candidate.bin','MANIFEST.yaml']:wanted.add(A+parent+'/'+name)
for n in ['run-attempt1/BEFORE_INPUT_IDENTITIES.json','run-attempt1/AFTER_INPUT_IDENTITIES.json','ENTRY_CONSUMED65.json','DERIVED_TERMINAL65_SUMMARY.json']:
 key='native65/'+n
 if key in M:wanted.add(key)
assert wanted<=set(M);size=sum(M[n]['bytes']for n in wanted);assert len(wanted)<=250 and size<=128<<20
bounded_write(O/'SELECTED_EXTRACTION_PLAN.json',json.dumps({'files':len(wanted),'bytes':size,'max_file_count':250,'max_stored_bytes':128<<20,'all_complete_native_data_retained_in_full_archive':True,'selection':sorted(wanted)},indent=2)+'\n')
D=O/'selected';D.mkdir();done=[]
with tarfile.open(B/'complete.tar.gz',mode='r|gz')as tf:
 for e in tf:
  if e.name not in wanted:continue
  assert e.isfile()and e.size==M[e.name]['bytes'];data=tf.extractfile(e).read(e.size+1);assert len(data)==e.size and hashlib.sha256(data).hexdigest()==M[e.name]['sha256']
  p=D/e.name;p.parent.mkdir(parents=True,exist_ok=True);bounded_write_bytes(p,data);done.append({'path':e.name,'bytes':len(data),'sha256':M[e.name]['sha256']})
assert len(done)==len(wanted)
bounded_write(O/'SELECTED_EXTRACTION_READBACK.json',json.dumps({'files':done,'count':len(done),'bytes':sum(x['bytes']for x in done),'all_source_manifest_SHA_and_size_match':True},indent=2)+'\n');print(json.dumps({'files':len(done),'bytes':sum(x['bytes']for x in done)}))

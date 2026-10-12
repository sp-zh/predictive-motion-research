from pathlib import Path
import sys,json,hashlib,os,tarfile,gzip,resource,signal
sys.path.insert(0,'/private/tmp');from root_shared_derived_budget_stop45 import Budget
resource.setrlimit(resource.RLIMIT_CPU,(600,600));signal.alarm(1200)
B=Budget();CAP=16*1024**3
r=Path('/Users/uot/Documents/ChatGPT/ros');u=r/'results/phase5-reference/controlled-stop-failed47-v1-20261011';store=u/'root-archive1';payload=store/'payload';assert not store.exists();payload.mkdir(parents=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(524288),b''):h.update(b)
 return h.hexdigest()
def selected_sealed(a,dest):
 ready=a/'READY.json';d=json.loads(ready.read_text());entries=d.get('payload',d.get('files'));assert isinstance(entries,list)
 exp={e['path']:e for e in entries};assert len(exp)==len(entries)
 for n,e in exp.items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts
  q=a/n;assert q.is_file() and not q.is_symlink() and q.stat().st_size==e['bytes'] and sha(q)==e['sha256'],str(q)
  dst=dest/n;dst.parent.mkdir(parents=True,exist_ok=True);os.link(q,dst)
 dest.mkdir(parents=True,exist_ok=True);os.link(ready,dest/'READY.json')
 return {'source':str(a),'READY_sha256':sha(ready),'payloads':len(exp),'payload_bytes':sum(e['bytes'] for e in exp.values()),'selection':'All explicitly manifested payloads plus original READY; same-Mac aliases, not second physical copies.'}
refs=[('producer48',u/'root-import1'),('independent48',Path('/private/tmp/root_independent_controlled_stop48_review_20261011'))]
selections=[selected_sealed(a,payload/n) for n,a in refs]
for q in u.iterdir():
 if q.is_file():B.copy(q,payload/'Root-failures-and-verification'/q.name)

for n in ['root_archive_stop48.py','root_prepare_stop48_public.py','root_link_import_stop48.py','root_shared_derived_budget_stop45.py']:
 p=Path('/private/tmp')/n
 if p.exists():B.copy(p,payload/'Root-tools'/n)
for n in ['tools/phase5_controlled_stop_session_v4','reviews/evidence/phase5_controlled_stop_endpoint_failure_v1_20261011','figures/phase5_controlled_stop_endpoint_failure_v1_20261011']:
 a=r/n
 for q in a.rglob('*'):
  assert not q.is_symlink()
  if q.is_file():B.copy(q,payload/'public-snapshot'/n/q.relative_to(a))
for n in ['docs/phase5_development_status.md','docs/showcase.md','AGENTS.md','PROJECT_PAUSED.json']:B.copy(r/n,payload/'public-snapshot'/n)
previous=json.loads((r/'reviews/evidence/phase5_controlled_stop_face_failure_v1_20261011/STORAGE_CHECKPOINT.json').read_text())
transport=json.loads((u/'root-import1/READY.json').read_text())['external_transport']
B.write_text(payload/'ARCHIVE_SELECTION.json',json.dumps({'schema':'ROOT_STOP48_UNDERLYING_ONCE_SELECTION_V1','selections':selections,'external_compressed_transport':transport,'compressed_transport_D_copy_claimed':False,'ancillary_cache_excluded':None,'prior47_archive_reference':previous,'prior_public_commit':'00f6f0b3b1e44ac1a77e2c9713e23f7f0c8b5902','coverage':'Full underlying producer48 native/source/auxiliary/derived evidence and retained failures, full independent math review and all retained preparation references within producer48. Excludes duplicate external transport object; no raw experiment evidence omitted. Prior archives preserved without repacking. Public-snapshot storage receipt pending; final storage receipt closes after Dell readback.','native_reruns':0,'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED'},indent=2)+'\n')
B.snapshot(payload/'GLOBAL_DERIVED_BUDGET_AT_ARCHIVE_CAPTURE.json')
files={}
for q in sorted(payload.rglob('*')):
 assert not q.is_symlink()
 if q.is_file():files[str(q.relative_to(payload))]={'bytes':q.stat().st_size,'sha256':sha(q)}
mf=payload/'ARCHIVE_MANIFEST.json';B.write_text(mf,json.dumps({'schema':'ROOT_STOP48_FULL_MANIFEST_V1','files':files,'hard_cap_bytes':CAP,'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED'},indent=2)+'\n')
assert sum(e['bytes'] for e in files.values())+mf.stat().st_size<=CAP
class CapWriter:
 def __init__(self,f):self.f=f;self.n=0
 def write(self,b):
  assert len(b)<=CAP-self.n,'16GiB stream cap before write';n=self.f.write(b);self.n+=n;return n
 def flush(self):return self.f.flush()
 def tell(self):return self.n
archive=store/'controlled-stop48-full-failure-review-v1.tar.gz'
with archive.open('xb') as raw:
 compressed=CapWriter(raw)
 with gzip.GzipFile(fileobj=compressed,mode='wb',compresslevel=3,mtime=0) as gz:
  uncompressed=CapWriter(gz)
  with tarfile.open(fileobj=uncompressed,mode='w|',dereference=True) as tf:
   for q in sorted(payload.rglob('*')):
    if q.is_file():tf.add(q,arcname=str(q.relative_to(payload)),recursive=False)
  uncompressed_bytes=uncompressed.n
 compressed_bytes=compressed.n
assert compressed_bytes==archive.stat().st_size<=CAP
with tarfile.open(archive,'r|gz') as tf:
 seen=set();member_bytes=0
 for m in tf:
  assert m.isfile() and m.name not in seen;seen.add(m.name);member_bytes+=m.size;assert member_bytes<=CAP
  stream=tf.extractfile(m);h=hashlib.sha256();size=0
  for b in iter(lambda:stream.read(524288),b''):h.update(b);size+=len(b)
  stream.close();e={'bytes':mf.stat().st_size,'sha256':sha(mf)} if m.name=='ARCHIVE_MANIFEST.json' else files[m.name]
  assert size==e['bytes'] and h.hexdigest()==e['sha256'],m.name
 assert seen==set(files)|{'ARCHIVE_MANIFEST.json'}
result={'schema':'ROOT_STOP48_ARCHIVE_READY_V1','unit':u.name,'archive':str(archive),'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'manifest_sha256':sha(mf),'regular_members':len(files)+1,'payloads':len(files),'payload_bytes':sum(e['bytes'] for e in files.values()),'archive_compressed_and_uncompressed_streams_cap_bytes':CAP,'actual_uncompressed_tar_stream_bytes':uncompressed_bytes,'all_member_sum_cap_bytes':CAP,'Mac_all_payloads_verified':True,'Dell_copy_verified':False,'coverage':'Full actual48 underlying native evidence once, full reviews/failures and public snapshot. Producer preparation/failures retained. Future49 pure/source/native work outside this frozen archive. External duplicate compressed transport remains Mac-only; No local caches imported. Prior40-47 archives referenced unchanged.','resource_scope':'CPU600s wall1200s,512KiB SHA/readback. Darwin AS unavailable, no hard RSS claim. Public/reference copies globally precharged3GiB; sealed source/raw payload aliases not duplicate physical storage. Archive streams independently capped16GiB.','phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED'}
B.write_text(store/'ARCHIVE_READY.json',json.dumps(result,indent=2)+'\n')
for q in sorted(payload.rglob('*'),key=lambda q:len(q.parts),reverse=True):q.chmod(0o444 if q.is_file() else 0o555)
payload.chmod(0o555);archive.chmod(0o444);(store/'ARCHIVE_READY.json').chmod(0o444)
print(json.dumps(result))

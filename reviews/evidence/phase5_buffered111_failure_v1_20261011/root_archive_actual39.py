from pathlib import Path
import hashlib,json,shutil,tarfile,resource
resource.setrlimit(resource.RLIMIT_CPU,(360,360))
# Darwin RLIMIT_AS512MiB precheck refused; no unsupported OS memory claim.
# All data and archive hashes/readbacks use524288B chunks; CPU360s remains explicit.
root=Path('/Users/uot/Documents/ChatGPT/ros');unit=root/'results/phase5-reference/nonzero-128cycle-buffered-failed-v1-20261011';review=Path('/private/tmp/root_independent_buffered111_actual_review_20261011')
assert (review/'READY.json').is_file(),'independent sealed review required'
store=unit/'root-archive1';payload=store/'payload';assert not store.exists();payload.mkdir(parents=True)
def sha(q):
 h=hashlib.sha256()
 with q.open('rb') as f:
  for b in iter(lambda:f.read(524288),b''):h.update(b)
 return h.hexdigest()
def copytree(a,b):
 # Read-only imported bytes hardlink within one Mac volume; independent contents hashed below.
 shutil.copytree(a,b,copy_function=lambda x,y: __import__('os').link(x,y))
copytree(unit/'root-import1',payload/'producer')
copytree(review,payload/'independent')
for name in ['ROOT_PACKET_VERIFICATION.json','ROOT_INITIAL_VISUAL_INSPECTION.json']:
 shutil.copyfile(unit/name,payload/name)
copytree(Path('/private/tmp/root_independent_current_hint_fraction_review_20261011'),payload/'independent-fraction-source-review')
copytree(unit/'failed-root-layout1',payload/'retained-root-layout1')
for name in ['tools/phase5_nonzero_progress_session_v3','reviews/evidence/phase5_buffered111_failure_v1_20261011','figures/phase5_buffered111_failure_v1_20261011']:
 shutil.copytree(root/name,payload/'source-snapshot'/name)
for name in ['docs/phase5_development_status.md','docs/showcase.md','AGENTS.md','PROJECT_PAUSED.json']:
 d=payload/'source-snapshot'/name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,d)
shutil.copyfile(__file__,payload/Path(__file__).name)
files={}
for q in sorted(payload.rglob('*')):
 assert not q.is_symlink(),q
 if q.is_file():files[str(q.relative_to(payload))]={'bytes':q.stat().st_size,'sha256':sha(q)}
scope='Consumed39:111 currentgeometryQP/B44400/C222/history111/444ms, failed112thhint and originalfixture+unalteredlaststate exactlyverified; full111savedcost/SI+first32matcheddata+inclusivefine times. All1114msmiss, original1.024B cumulative slotsnotreset, newlogical1.2B tracked, nonzero r/no physicalstop. All3675producer+200independent+8fractionsource payloads/retainedadapter+layoutfailures andexactpublicsource39 retained. No128completion/fulltask/stopping/realtime/researchranking/hardware/Phase5acceptance. SDK/ELF/dependencies pinnedDell only.'
mf=payload/'ARCHIVE_MANIFEST.json';mf.write_text(json.dumps({'schema':'ROOT_ACTUAL39_FULL_MANIFEST_V1','files':files,'scope':scope,'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED'},indent=2)+'\n')
archive=store/'buffered111-and-failed112-full-review-v1.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=3) as tf:
 for q in sorted(payload.rglob('*')):
  if q.is_file():tf.add(q,arcname=str(q.relative_to(payload)),recursive=False)
with tarfile.open(archive,'r|gz') as tf:
 seen=set()
 for m in tf:
  assert m.isfile() and m.name not in seen,m.name;seen.add(m.name)
  h=hashlib.sha256();size=0
  stream=tf.extractfile(m)
  for b in iter(lambda:stream.read(524288),b''):h.update(b);size+=len(b)
  stream.close()
  e={'bytes':mf.stat().st_size,'sha256':sha(mf)} if m.name=='ARCHIVE_MANIFEST.json' else files[m.name]
  assert size==e['bytes'] and h.hexdigest()==e['sha256'],m.name
 assert seen==set(files)|{'ARCHIVE_MANIFEST.json'}
r={'schema':'ROOT_UNIT_ARCHIVE_READY_V1','unit':unit.name,'archive':str(archive),'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'manifest_sha256':sha(mf),'regular_members':len(files)+1,'payloads':len(files),'payload_bytes':sum(e['bytes'] for e in files.values()),'Mac_all_payloads_verified':True,'Dell_copy_verified':False,'scope':scope,'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED','archive_memory_scope':'512KiB streamed hash/memberreadback, fixed512KiB data chunks CPU360s; Darwin RLIMIT_AS unavailable; completepayloads hardlink only alreadysealedproducer/independentreview on sameMacvolume; publicsource copied separately'}
ready=store/'ARCHIVE_READY.json';ready.write_text(json.dumps(r,indent=2)+'\n')
for q in sorted(payload.rglob('*'),key=lambda q:len(q.parts),reverse=True):q.chmod(0o444 if q.is_file() else 0o555)
payload.chmod(0o555);archive.chmod(0o444);ready.chmod(0o444)
print(json.dumps(r))

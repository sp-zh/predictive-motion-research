from pathlib import Path
import hashlib,json,shutil,tarfile,resource,signal,os
resource.setrlimit(resource.RLIMIT_CPU,(600,600));signal.alarm(1800)
root=Path('/Users/uot/Documents/ChatGPT/ros');unit=root/'results/phase5-reference/scp-workpackage40-44-v1-20261011';store=unit/'root-archive1';payload=store/'payload';assert not store.exists();payload.mkdir(parents=True)
def sha(q):
 h=hashlib.sha256()
 with q.open('rb') as f:
  for b in iter(lambda:f.read(524288),b''):h.update(b)
 return h.hexdigest()
def sealed_tree(a,b):
 assert (a/'READY.json').exists(),str(a)
 shutil.copytree(a,b,copy_function=lambda x,y:os.link(x,y))
units={40:'centered-trust-failed40-v1-20261011',41:'centered-trust-failed41-v1-20261011',42:'scp-fixed-trust-failed42-v1-20261011',43:'scp-backtrack-failed43-v1-20261011',44:'scp-rank64-complete44-v1-20261011'}
for k,n in units.items():
 u=root/'results/phase5-reference'/n;sealed_tree(u/'root-import1',payload/f'producer{k}');shutil.copyfile(u/'ROOT_PACKET_VERIFICATION.json',payload/f'ROOT_PACKET_VERIFICATION{k}.json')
for name in ['root_independent_centered_trust_failures40_41_review_20261011','root_independent_scp_fixed42_review_20261011','root_independent_scp_backtrack43_rank44_review_20261011']:
 sealed_tree(Path('/private/tmp')/name,payload/name)
for name in ['current_trial_extra_verification42_20261011','current_trial_extra_verification43_20261011']:
 p=Path('/private/tmp')/name
 if p.exists():shutil.copytree(p,payload/name)
for name in ['tools/phase5_nonzero_progress_session_v4','reviews/evidence/phase5_scp_workpackage40_44_v1_20261011','figures/phase5_centered_trust_failures40_41_v1_20261011','figures/phase5_scp_workpackage40_44_v1_20261011']:
 shutil.copytree(root/name,payload/'public-snapshot'/name)
for name in ['docs/phase5_development_status.md','docs/showcase.md','AGENTS.md','PROJECT_PAUSED.json']:
 d=payload/'public-snapshot'/name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,d)
for n in ['NONZERO_BUFFERED111_COMPLETE_DELL_D_MIRROR_VERIFIED.json','verify_current_trial_bindings.py']:
 p=Path('/private/tmp')/n
 if p.exists():shutil.copyfile(p,payload/n)
shutil.copyfile(__file__,payload/Path(__file__).name)
files={}
for q in sorted(payload.rglob('*')):
 assert not q.is_symlink(),str(q)
 if q.is_file():files[str(q.relative_to(payload))]={'bytes':q.stat().st_size,'sha256':sha(q)}
scope='Actual bounded development40-44: all failures preserved; 44 completes64 same-session current transactions/128 physical2ms halves with141 fresh proposals, no complete task/physicalstop/realtime/heldout/Phase5acceptance. Source40-44, all producer raw/decode/retained preparation failures and independent saved-data reviews included. Original affine/d3d4/evidence and old1.024B source budget not modified or reset. Source SDK/ELF/runtime dependencies pinned on Dell, not portable vendored build. Phase6 NOT_STARTED.'
mf=payload/'ARCHIVE_MANIFEST.json';mf.write_text(json.dumps({'schema':'ROOT_SCP40_44_FULL_MANIFEST_V1','files':files,'scope':scope,'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED'},indent=2)+'\n')
archive=store/'scp40-44-functional64-full-review-v1.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=3,dereference=True) as tf:
 for q in sorted(payload.rglob('*')):
  if q.is_file():tf.add(q,arcname=str(q.relative_to(payload)),recursive=False)
with tarfile.open(archive,'r|gz') as tf:
 seen=set()
 for m in tf:
  assert m.isfile() and m.name not in seen,m.name;seen.add(m.name);h=hashlib.sha256();size=0;stream=tf.extractfile(m)
  for b in iter(lambda:stream.read(524288),b''):h.update(b);size+=len(b)
  stream.close();e={'bytes':mf.stat().st_size,'sha256':sha(mf)} if m.name=='ARCHIVE_MANIFEST.json' else files[m.name]
  assert size==e['bytes'] and h.hexdigest()==e['sha256'],m.name
 assert seen==set(files)|{'ARCHIVE_MANIFEST.json'}
r={'schema':'ROOT_UNIT_ARCHIVE_READY_V1','unit':unit.name,'archive':str(archive),'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'manifest_sha256':sha(mf),'regular_members':len(files)+1,'payloads':len(files),'payload_bytes':sum(e['bytes'] for e in files.values()),'Mac_all_payloads_verified':True,'Dell_copy_verified':False,'scope':scope,'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED','archive_memory_scope':'512KiB streaming SHA/member readback, CPU600s wall1800s. Darwin AS limit unavailable. Root payloads hardlink already sealed same-Mac copies; not an independent second physical copy. Public snapshot copied separately; independent Dell D copy/readback follows.'}
ready=store/'ARCHIVE_READY.json';ready.write_text(json.dumps(r,indent=2)+'\n')
for q in sorted(payload.rglob('*'),key=lambda q:len(q.parts),reverse=True):q.chmod(0o444 if q.is_file() else 0o555)
payload.chmod(0o555);archive.chmod(0o444);ready.chmod(0o444);print(json.dumps(r))

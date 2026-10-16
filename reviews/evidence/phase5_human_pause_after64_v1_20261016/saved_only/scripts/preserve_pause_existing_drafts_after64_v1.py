from pathlib import Path
import os,json,hashlib,tarfile,zlib,time
R=Path('/Users/uot/Documents/ChatGPT/ros');D=R/'reviews/evidence/phase5_human_pause_after64_v1_20261016';P=R/'transfer/cold-backups/human-pause-after64-drafts65-20261016-v1';P.mkdir(exist_ok=False);CAP=64*1024**2;start=time.monotonic();sha=lambda b:hashlib.sha256(b).hexdigest()
w=Path('/private/tmp/phase5_pause_after64_20261016_v1/PAUSE_PRESERVATION_AND_DRAFT_MANIFEST.json');j=json.loads(w.read_text());files={Path(e['path']):{'bytes':e['bytes'],'sha256':e['sha256']}for e in j['preserved_small_draft_files']};files[w]={'bytes':w.stat().st_size,'sha256':sha(w.read_bytes())}
for folder in [Path('/private/tmp/root65_saved_design_review_v1_20261016'),Path('/private/tmp/root65_mac_consumer_fixture_tests_v1_20261016')]:
 for p in folder.rglob('*'):
  if p.is_file():assert not p.is_symlink();files[p]={'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
for p in [R/'tools/cold_stream_backup_v1/mac_consumer.py',Path('/private/tmp/root65_doublehat_saved_review_v1.py'),Path('/private/tmp/root65_fetch_band_probe_v1.py'),Path('/private/tmp/root65_band_saved_review_v1.py'),Path('/private/tmp/root65_mac_consumer_fixture_tests_v1.py')]:files[p]={'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
assert len(files)<=1000 and sum(e['bytes']for e in files.values())<=CAP
expected={};snapshot={}
for p,e in files.items():
 b=p.read_bytes();assert len(b)==e['bytes']and sha(b)==e['sha256'];s=p.stat();snapshot[p]=(s.st_ino,s.st_size,s.st_mtime_ns);name='private_tmp/'+str(p.relative_to('/private/tmp'))if p.is_relative_to('/private/tmp')else'workspace/'+str(p.relative_to(R));expected[name]=e
part=P/'paused_existing_drafts.tar.gz.part';final=P/'paused_existing_drafts.tar.gz'
class Capped:
 def __init__(self,f):self.f=f;self.n=0
 def write(self,b):
  assert len(b)<=CAP-self.n;self.n+=len(b);return self.f.write(b)
 def flush(self):self.f.flush()
with part.open('xb')as f:
 sink=Capped(f)
 with tarfile.open(fileobj=sink,mode='w|gz',compresslevel=1)as t:
  for p in sorted(files):
   name='private_tmp/'+str(p.relative_to('/private/tmp'))if p.is_relative_to('/private/tmp')else'workspace/'+str(p.relative_to(R));t.add(p,arcname=name,recursive=False)
 f.flush();os.fsync(f.fileno())
for p,identity in snapshot.items():
 s=p.stat();assert(s.st_ino,s.st_size,s.st_mtime_ns)==identity
seen=set()
with tarfile.open(part,'r|gz')as t:
 for e in t:
  assert e.isfile()and e.name in expected and e.name not in seen and e.size==expected[e.name]['bytes'];h=hashlib.sha256();n=0;f=t.extractfile(e)
  while b:=f.read(65536):h.update(b);n+=len(b)
  assert n==e.size and h.hexdigest()==expected[e.name]['sha256'];seen.add(e.name)
assert seen==set(expected)
h=hashlib.sha256();z=zlib.decompressobj(31);n=raw=0
with part.open('rb')as f:
 while b:=f.read(65536):
  n+=len(b);h.update(b);data=b
  while True:
   out=z.decompress(data,65536);raw+=len(out);assert raw<=128*1024**2 and not z.unused_data;data=z.unconsumed_tail
   if not data and len(out)<65536:break
assert z.eof and not z.unconsumed_tail and not z.unused_data and n<=CAP
part.chmod(0o444);os.rename(part,final);record={'schema':'HUMAN_PAUSE_ALREADY_CREATED_DRAFTS_RECOVERY_BACKUP_V1','archive':str(final),'archive_bytes':n,'archive_sha256':h.hexdigest(),'members':len(seen),'all_existing_member_SHA_size_readback_passed':True,'persisted_whole_archive_SHA_CRC_singleEOF_passed':True,'no_source_or_test_execution':True,'source_payload_bytes':sum(e['bytes']for e in expected.values()),'cap_bytes':CAP,'wall_seconds':time.monotonic()-start,'scope':'Backup finishing after direct human pause only. Existing scripts, data and positive/failed local-consumer fixture bytes copied without running them; UNKNOWN/corrupt nested bytes preserved byte-for-byte, no new CRC/experiment validation of those nested files. No native65/source implementation or real Dell-stream fixture occurred. Primary Mac persistent recovery archive plus Git small source/reports; old actual64 Mac/Dell full archives retained.'}
(P/'CONTENTS.json').write_text(json.dumps({'members':expected,'original_sources':{str(p):e for p,e in files.items()}},indent=2)+'\n');(P/'READY.json').write_text(json.dumps(record,indent=2)+'\n')
for p in P.iterdir():p.chmod(0o444)
fd=os.open(P,os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd);P.chmod(0o555)
(D/'MAC_EXISTING_DRAFT_RECOVERY_BACKUP.json').write_text(json.dumps(record,indent=2)+'\n');(D/'EXISTING_DRAFT_FILE_IDENTITIES.json').write_text(json.dumps({'files':{str(p):e for p,e in files.items()}},indent=2)+'\n');print(json.dumps(record))

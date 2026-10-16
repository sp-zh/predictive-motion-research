from pathlib import Path
import subprocess,json,hashlib,shlex,os,sys,time,tarfile,selectors
sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write_bytes
D=Path(__file__).resolve().parent
remote=json.loads((D/'REMOTE63.json').read_text())['remote']
OUT=Path('/private/tmp/phase5_controlled_stop_explicit_warm_nominal_terminal63_v1_20261016')
TRANSPORT=Path('/private/tmp/phase5_stop63_minimal_transport_external_v1_20261016')
assert not OUT.exists() and not TRANSPORT.exists()
TRANSPORT.mkdir();part=TRANSPORT/'transport.tar.gz.part'
code=r'''
from pathlib import Path
import sys,json,hashlib,tarfile,os
p=Path(REMOTE)
assert any((p/'run-attempt1'/n).is_file()for n in ['BUILD_RESULT.json','BUILD_FAILURE.json']),'native driver must finish first'
before=json.loads((p/'run-attempt1/BEFORE_INPUT_IDENTITIES.json').read_text());after=json.loads((p/'run-attempt1/AFTER_INPUT_IDENTITIES.json').read_text());assert before==after
files=[]
for root in ['src','profile-version1']:
 files += [q for q in (p/root).rglob('*') if q.is_file()]
run=p/'run-attempt1';artifact=run/'artifacts'
files += [q for q in run.iterdir() if q.is_file()]
files += [q for q in artifact.iterdir() if q.is_file()]
cycles=sorted(artifact.glob('cycle-*'),key=lambda q:int(q.name.split('-')[1]));assert cycles
last=cycles[-1];files += [q for q in last.rglob('*') if q.is_file()]
extra=[c for c in cycles[:-1]if c.name in ['cycle-0','cycle-32']]
for c in extra:files += [q for q in c.rglob('*')if q.is_file()]
for cycle in cycles[:-1]:
 if cycle in extra:continue
 files += [q for q in cycle.iterdir() if q.is_file()]
 for trial in cycle.glob('trial-*'):
  files += [q for q in trial.iterdir() if q.is_file() and q.name in ['actual_commit.bin','MANIFEST.yaml']]
# Full native hash inventory remains on Dell; only selected terminal/last
# current inputs are Mac copied. Uncopied data are not claimed Mac verified.
native=[]
for q in sorted(run.rglob('*')):
 if q.is_file():
  h=hashlib.sha256()
  with q.open('rb')as f:
   while b:=f.read(65536):h.update(b)
  native.append({'path':str(q.relative_to(p)),'bytes':q.stat().st_size,'sha256':h.hexdigest()});q.chmod(0o444)
with(p/'FULL_NATIVE63_DELL_INVENTORY.json').open('x')as f:json.dump({'scope':'Producer full-native stored hashes; only terminal-selected subset has Mac byte readback; not full archive.', 'files':native},f,indent=2)
for root in ['build-attempt1','link-attempt1']:
 files += [q for q in (p/root).iterdir() if q.is_file() and (q.suffix in ['.json','.stdout','.stderr'] or q.name=='active_first_cycle')]
files += [q for q in p.iterdir() if q.is_file()]
for root in ['pure-tests-attempt1','pure-math-attempt1']:
 files += [q for q in (p/root).iterdir()if q.is_file()and q.suffix in ['.json','.stdout','.stderr']]
assert len(files)==len(set(files)) and len(files)<25000
assert all(not q.is_symlink() for q in files)
assert sum(q.stat().st_size for q in files)<=int(256*1024**2)
def digest(q):
 h=hashlib.sha256();n=0
 with q.open('rb')as f:
  while b:=f.read(65536):h.update(b);n+=len(b)
 return {'path':str(q.relative_to(p)),'bytes':n,'sha256':h.hexdigest()}
rows=[digest(q)for q in sorted(files)]
r={'schema':'FRESH63_MINIMAL_TERMINAL_LAST_CURRENT_TRANSFER_ROSTER_V1','files':rows,'files_count':len(rows),'bytes':sum(x['bytes']for x in rows),'source_model_inputs_before_after_equal':True,'outcome':'See actual driver and artifact records; successful copying is not native/stop/task acceptance.'}
with(p/'TRANSPORT_CAPTURE_ROSTER.json').open('x')as f:json.dump(r,f,indent=2)
files.append(p/'TRANSPORT_CAPTURE_ROSTER.json')
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz',compresslevel=1)as t:
 for q in sorted(files):t.add(q,arcname='actual-dell/'+p.name+'/'+str(q.relative_to(p)))
'''.replace('REMOTE',repr(remote))
argv=['/Users/uot/Documents/ChatGPT/ros/tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(code)]
started=time.monotonic();n=0;h=hashlib.sha256();err=bytearray()
child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
sel=selectors.DefaultSelector();sel.register(child.stdout,selectors.EVENT_READ,'out');sel.register(child.stderr,selectors.EVENT_READ,'err')
with part.open('xb')as f:
 while sel.get_map():
  assert time.monotonic()-started<1200,'transport finite wall cap; partial preserved'
  for key,_ in sel.select(.25):
   b=os.read(key.fileobj.fileno(),65536)
   if not b:sel.unregister(key.fileobj);continue
   if key.data=='out':
    assert len(b)<=512*1024**2-n,'minimal external transport512MiB prewrite cap';f.write(b);h.update(b);n+=len(b)
   else:
    assert len(err)+len(b)<=65536;err.extend(b)
 f.flush();os.fsync(f.fileno())
assert child.wait(timeout=5)==0,bytes(err)
final=TRANSPORT/'transport.tar.gz';os.rename(part,final)
print('transport received',n,h.hexdigest(),flush=True)
# Streamed member readback: no bulk decompression. Verify every output identity.
OUT.mkdir();prefix='actual-dell/'+Path(remote).name+'/';members={};total=0
with tarfile.open(final,'r|gz')as t:
 for m in t:
  assert m.isfile() and m.name.startswith(prefix) and '..' not in Path(m.name).parts and m.name not in members
  assert m.size<=256*1024**2 and total+m.size<=int(256*1024**2)+16*1024**2
  q=OUT/m.name;q.parent.mkdir(exist_ok=True,parents=True);digest=hashlib.sha256();count=0
  with q.open('xb')as sink:
   src=t.extractfile(m)
   while b:=src.read(65536):sink.write(b);digest.update(b);count+=len(b)
  assert count==m.size;members[m.name]={'bytes':count,'sha256':digest.hexdigest()};total+=count;q.chmod(0o444)
unit=OUT/prefix;roster=json.loads((unit/'TRANSPORT_CAPTURE_ROSTER.json').read_text())
expected={prefix+x['path']:{'bytes':x['bytes'],'sha256':x['sha256']}for x in roster['files']}
assert set(members)==set(expected)|{prefix+'TRANSPORT_CAPTURE_ROSTER.json'}
assert all(members[k]==v for k,v in expected.items())
# gzip full CRC/EOF/single/no trailing independently using bounded zlib streaming.
import zlib
z=zlib.decompressobj(31);seen=0
with final.open('rb')as f:
 while b:=f.read(65536):
  seen+=len(b);data=b
  while True:
   out=z.decompress(data,65536);assert not z.unused_data;data=z.unconsumed_tail
   if not data and len(out)<65536:break
assert z.eof and not z.unused_data and not z.unconsumed_tail and seen==n
ready={'schema':'FRESH63_MINIMAL_TERMINAL_LAST_CURRENT_PACKET_READY_V1','payload':[{'path':k,**v}for k,v in sorted(members.items())],'payload_count':len(members),'payload_bytes':total,'transport':{'path':str(final),'bytes':n,'sha256':h.hexdigest(),'full_tar_member_size_sha_and_outergzip_crc_eof_single_no_trailing':True},'scope':'Selected source/profile/ELF/runtime metadata, all whole-cycle records/actual commits and full last current plus complete-cycle0-and-firstbrake32 inputs/failures only. Uncopied full native files remain on Dell with producer hashes and were not Mac-readback verified. This is not a complete evidence archive. Results/stop/fulltask require review; no Git/phase acceptance implied.'}
with(OUT/'READY.json').open('x')as f:json.dump(ready,f,indent=2)
(OUT/'READY.json').chmod(0o444)
print('packet complete',len(members),total,'READYsha',hashlib.sha256((OUT/'READY.json').read_bytes()).hexdigest(),flush=True)

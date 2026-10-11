from pathlib import Path
import io,tarfile,subprocess,shlex,json,hashlib
O=Path('/private/tmp/phase5_geometry_provider_checkpoint_v1_20261011');O.mkdir(exist_ok=False)
s='''from pathlib import Path
import sys,io,tarfile,json,hashlib,resource,signal
resource.setrlimit(resource.RLIMIT_CPU,(45,45));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));signal.alarm(55)
r=Path('/home/codextransfer/predictive_motion/results/phase5');selected=[];index=[]
for version in ['nominal-geometry-provider-recorded-v1-20261011-attempt23','nominal-geometry-provider-recorded-v2-20261011-attempt24','nominal-geometry-provider-recorded-v3-20261011-attempt25','nominal-geometry-provider-recorded-v4-20261011-attempt26']:
 p=r/version
 for q in sorted(p.rglob('*')):
  if not q.is_file():continue
  rel=q.relative_to(p);first=rel.parts[0]
  if first.startswith(('build-','link-')) and q.suffix not in ['.json','.stdout','.stderr']:continue
  selected.append((q,version+'/'+str(rel)))
 for q in p.glob('link-*/provider_probe'):index.append({'path':str(q),'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'retained_dell_only':True})
assert len(selected)<2000 and sum(p.stat().st_size for p,n in selected)<268435456
b=io.BytesIO()
with tarfile.open(fileobj=b,mode='w:gz') as t:
 for q,n in selected:t.add(q,arcname=n,recursive=False)
 data=(json.dumps(index,indent=2)+'\\n').encode();m=tarfile.TarInfo('NATIVE_ELF_INDEX.json');m.size=len(data);t.addfile(m,io.BytesIO(data))
assert len(b.getvalue())<100663296;sys.stdout.buffer.write(b.getvalue())
'''
(O/'readonly_collection_source.py').write_text(s)
x=subprocess.run(['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(s)],capture_output=True,timeout=60);(O/'collection.stderr').write_bytes(x.stderr);assert x.returncode==0,x.stderr
(O/'actual_collection.tar.gz').write_bytes(x.stdout)
with tarfile.open(fileobj=io.BytesIO(x.stdout)) as t:
 ms=t.getmembers();assert all(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts for m in ms);assert sum(m.size for m in ms)<268435456;t.extractall(O/'actual-dell',filter='data')
print(json.dumps({'packet':str(O),'archive_bytes':len(x.stdout),'archive_sha256':hashlib.sha256(x.stdout).hexdigest(),'files':len(ms)}))

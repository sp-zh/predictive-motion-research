from pathlib import Path
import hashlib
import json
import shlex
import subprocess

root = Path('/Users/uot/Documents/ChatGPT/ros')
unit_name = 'nonzero-128cycle-buffered-failed-v1-20261011'
unit = root / 'results/phase5-reference' / unit_name
store = unit / 'root-archive1'
ready = store / 'ARCHIVE_READY.json'
r = json.loads(ready.read_text())
remote = '/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/' + unit_name + '-root1'
ssh = [str(root / 'tools/dell-ssh.sh'), '-T', '-o', 'BatchMode=yes', '-o',
       'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8', 'DellTransfer']
create = f'from pathlib import Path; p=Path({remote!r}); assert not p.exists(); p.mkdir(parents=True)'
subprocess.run(ssh + ['/usr/bin/python3.12 -I -S -B -c ' + shlex.quote(create)], check=True, capture_output=True, timeout=20)
scp = ['scp', '-F', str(root / '.transfer-private/ssh_config'), '-o', 'BatchMode=yes',
       '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8']
for p in [Path(r['archive']), ready]:
    subprocess.run(scp + [str(p), 'DellTransfer:' + remote + '/' + p.name], check=True, capture_output=True, timeout=360)
checks = {'archive_name': Path(r['archive']).name, 'ready_sha256': hashlib.sha256(ready.read_bytes()).hexdigest(), **r}
program = '''from pathlib import Path
import hashlib,json,tarfile,resource
resource.setrlimit(resource.RLIMIT_CPU,(300,300))
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
root=Path(REMOTE)
r=json.loads(CHECKS)
def sha(b): return hashlib.sha256(b).hexdigest()
def file_sha(q):
    h=hashlib.sha256()
    with q.open('rb') as f:
        for b in iter(lambda:f.read(524288),b''):h.update(b)
    return h.hexdigest()
p=root/r['archive_name']
assert p.stat().st_size==r['archive_bytes'] and file_sha(p)==r['archive_sha256']
assert sha((root/'ARCHIVE_READY.json').read_bytes())==r['ready_sha256']
with tarfile.open(p,'r:gz') as tf:
    members=tf.getmembers()
    assert len(members)==r['regular_members'] and all(m.isfile() for m in members)
    assert len({m.name for m in members})==len(members)
    b=tf.extractfile('ARCHIVE_MANIFEST.json').read()
    assert sha(b)==r['manifest_sha256']
    files=json.loads(b)['files']
    assert len(files)==r['payloads']
    for m in members:
        if m.name=='ARCHIVE_MANIFEST.json':continue
        stream=tf.extractfile(m);h=hashlib.sha256();size=0
        for b in iter(lambda:stream.read(524288),b''):h.update(b);size+=len(b)
        stream.close();e=files[m.name]
        assert size==e['bytes'] and h.hexdigest()==e['sha256']
st=p.stat()
print(json.dumps({'schema':'ROOT_UNIT_DELL_FULL_READBACK_V1','archive':str(p),
 'archive_bytes':r['archive_bytes'],'archive_sha256':r['archive_sha256'],
 'ready_sha256':r['ready_sha256'],'manifest_sha256':r['manifest_sha256'],
 'regular_members_verified':len(members),'payloads_verified':len(files),
 'all_payloads_verified':True,'payload_bytes_verified':r['payload_bytes'],'readback':'512KiB streaming SHA/member data, AS512MiB CPU300s','observed_mode':st.st_mode&0o7777,
 'observed_uid':st.st_uid,'observed_gid':st.st_gid,
 'qualification':'NTFS POSIX sealing/ownership change not asserted; no chmod attempted.'}))
'''.replace('REMOTE', repr(remote)).replace('CHECKS', repr(json.dumps(checks)))
(unit / 'ROOT_DELL_ARCHIVE_READBACK_SOURCE.py').write_text(program)
result = subprocess.run(ssh + ['/usr/bin/python3.12 -I -S -B -c ' + shlex.quote(program)], capture_output=True, timeout=360)
(unit / 'DELL_ARCHIVE_READBACK.stdout.json').write_bytes(result.stdout)
(unit / 'DELL_ARCHIVE_READBACK.stderr').write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode()
print(result.stdout.decode())

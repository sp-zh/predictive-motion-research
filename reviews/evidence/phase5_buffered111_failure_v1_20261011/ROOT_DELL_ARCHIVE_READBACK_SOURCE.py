from pathlib import Path
import hashlib,json,tarfile,resource
resource.setrlimit(resource.RLIMIT_CPU,(300,300))
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
root=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/nonzero-128cycle-buffered-failed-v1-20261011-root1')
r=json.loads('{"archive_name": "buffered111-and-failed112-full-review-v1.tar.gz", "ready_sha256": "52bb77d2a8c1ea5564790062ed2c8838c19e3afcb51c7e86068a98d8c249a1f7", "schema": "ROOT_UNIT_ARCHIVE_READY_V1", "unit": "nonzero-128cycle-buffered-failed-v1-20261011", "archive": "/Users/uot/Documents/ChatGPT/ros/results/phase5-reference/nonzero-128cycle-buffered-failed-v1-20261011/root-archive1/buffered111-and-failed112-full-review-v1.tar.gz", "archive_bytes": 4671316890, "archive_sha256": "ee46bb5919b049a9f59127706a942b21d4da14f67fa9a8db1c76ed5585dc594a", "manifest_sha256": "71354a37ce061988d83bab6622186c111617145eb8c831b6560e65ba62e1555c", "regular_members": 3985, "payloads": 3984, "payload_bytes": 8742414998, "Mac_all_payloads_verified": true, "Dell_copy_verified": false, "scope": "Consumed39:111 currentgeometryQP/B44400/C222/history111/444ms, failed112thhint and originalfixture+unalteredlaststate exactlyverified; full111savedcost/SI+first32matcheddata+inclusivefine times. All1114msmiss, original1.024B cumulative slotsnotreset, newlogical1.2B tracked, nonzero r/no physicalstop. All3675producer+200independent+8fractionsource payloads/retainedadapter+layoutfailures andexactpublicsource39 retained. No128completion/fulltask/stopping/realtime/researchranking/hardware/Phase5acceptance. SDK/ELF/dependencies pinnedDell only.", "phase5": "NOT_ACCEPTED", "phase6": "NOT_STARTED", "archive_memory_scope": "512KiB streamed hash/memberreadback, fixed512KiB data chunks CPU360s; Darwin RLIMIT_AS unavailable; completepayloads hardlink only alreadysealedproducer/independentreview on sameMacvolume; publicsource copied separately"}')
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

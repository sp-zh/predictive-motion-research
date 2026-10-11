from pathlib import Path
import hashlib,json,tarfile,resource
resource.setrlimit(resource.RLIMIT_CPU,(300,300))
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
root=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/nonzero-32cycle-actual-v1-20261011-root1')
r=json.loads('{"archive_name": "nonzero32-actual-full-review-v1.tar.gz", "ready_sha256": "09e810cf74f9333a0b0393e4aa4fa1dce5d3ba9854624a340cc945592848e1f8", "schema": "ROOT_UNIT_ARCHIVE_READY_V1", "unit": "nonzero-32cycle-actual-v1-20261011", "archive": "/Users/uot/Documents/ChatGPT/ros/results/phase5-reference/nonzero-32cycle-actual-v1-20261011/root-archive1/nonzero32-actual-full-review-v1.tar.gz", "archive_bytes": 1345966615, "archive_sha256": "055216a72383724184098d062f55a030a86500012080a6d36695282baf5339af", "manifest_sha256": "02b5e499ffeb394523a08587ee1112231cd232f2c5a758c54d1d2e6a712e72b4", "regular_members": 1390, "payloads": 1389, "payload_bytes": 2588190375, "Mac_all_payloads_verified": true, "Dell_copy_verified": false, "scope": "Actual38 consumedonce;32 genuine closed-loop geometryQP/B12800/C64/history0to32/128ms, fullsaved-data cost/SI/TCP independent review, truthful all32deadline misses. Allproducer1233 files including raw654MBtar retained, full independent failures and views/source. No fulltask, exactphysicalstop, unrestrictedoptimality, realtime, hardware or Phase5acceptance. SDK/ELF/dependencies pinned Dell, not fullycopied.", "phase5": "NOT_ACCEPTED", "phase6": "NOT_STARTED", "archive_memory_scope": "512KiB streamed hash/memberreadback, fixed512KiB data chunks CPU360s; Darwin RLIMIT_AS unavailable; completepayloads hardlink only alreadysealedproducer/independentreview on sameMacvolume; publicsource copied separately"}')
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

from pathlib import Path
import hashlib,json,tarfile,resource
resource.setrlimit(resource.RLIMIT_CPU,(600,600))
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
root=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/controlled-stop-failed47-v1-20261011-root1')
assert not root.is_symlink()
r=json.loads('{"archive_name": "controlled-stop47-full-failure-review-v1.tar.gz", "ready_sha256": "e1f9e7d52b36efb91819284a825e77bd97f0f276c3a890d674afd98add13d198", "schema": "ROOT_STOP47_ARCHIVE_READY_V1", "unit": "controlled-stop-failed47-v1-20261011", "archive": "/Users/uot/Documents/ChatGPT/ros/results/phase5-reference/controlled-stop-failed47-v1-20261011/root-archive1/controlled-stop47-full-failure-review-v1.tar.gz", "archive_bytes": 1645144313, "archive_sha256": "55c679b252546ccd63290c03592d747fccaa6ee9121fdb8f0141d00add7708ea", "manifest_sha256": "94471c62aa024aebedea2746bb506a9eaf3d66e3d7c95f8b20e25c693a99e179", "regular_members": 3180, "payloads": 3179, "payload_bytes": 4426771112, "archive_compressed_and_uncompressed_streams_cap_bytes": 20401094656, "actual_uncompressed_tar_stream_bytes": 4433285120, "all_member_sum_cap_bytes": 20401094656, "Mac_all_payloads_verified": true, "Dell_copy_verified": false, "coverage": "Full actual47 underlying native evidence once, full reviews/failures and public snapshot. Full saved47 failure replay diagnostics included as identified reference. Future48 repair pure/native work outside this frozen archive. External duplicate compressed transport remains Mac-only; No local caches imported. Prior40-46 archives referenced unchanged.", "resource_scope": "CPU600s wall1200s,512KiB SHA/readback. Darwin AS unavailable, no hard RSS claim. Public/reference copies globally precharged3GiB; sealed source/raw payload aliases not duplicate physical storage. Archive streams independently capped19GiB.", "phase5": "NOT_ACCEPTED", "phase6": "NOT_STARTED"}')
def sha(b): return hashlib.sha256(b).hexdigest()
def file_sha(q):
    h=hashlib.sha256()
    with q.open('rb') as f:
        for b in iter(lambda:f.read(524288),b''):h.update(b)
    return h.hexdigest()
p=root/r['archive_name']
assert p.is_file() and not p.is_symlink()
assert p.stat().st_size==r['archive_bytes'] and file_sha(p)==r['archive_sha256']
assert sha((root/'ARCHIVE_READY.json').read_bytes())==r['ready_sha256']
with tarfile.open(p,'r:gz') as tf:
    members=tf.getmembers()
    assert len(members)==r['regular_members'] and all(m.isfile() for m in members)
    assert len({m.name for m in members})==len(members)
    b=tf.extractfile('ARCHIVE_MANIFEST.json').read()
    assert sha(b)==r['manifest_sha256']
    files=json.loads(b)['files']
    assert len(files)==r['payloads'] and sum(e['bytes'] for e in files.values())==r['payload_bytes']
    assert {m.name for m in members}==set(files)|{'ARCHIVE_MANIFEST.json'}
    assert sum(m.size for m in members)<=r['all_member_sum_cap_bytes']
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
 'all_payloads_verified':True,'payload_bytes_verified':r['payload_bytes'],'readback':'512KiB streaming SHA/member data, AS512MiB CPU600s','observed_mode':st.st_mode&0o7777,
 'observed_uid':st.st_uid,'observed_gid':st.st_gid,
 'qualification':'NTFS POSIX sealing/ownership change not asserted; no chmod attempted.'}))

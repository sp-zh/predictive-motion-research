from pathlib import Path
import hashlib,json,tarfile,resource
resource.setrlimit(resource.RLIMIT_CPU,(600,600))
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
root=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/seed47-prefix-review-supplement-v1-20261011-root1')
assert not root.is_symlink()
r=json.loads('{"archive_name": "seed47-prefix-review-supplement-v1.tar.gz", "ready_sha256": "afe548f61bffbaa2c8b51deab44a3cce895d73a0efc7b3eb43feb2fe0e1952a1", "schema": "ROOT_SEED47_PREFIX_REVIEW_SUPPLEMENT_READY_V1", "unit": "seed47-prefix-review-supplement-v1-20261011", "archive": "/Users/uot/Documents/ChatGPT/ros/results/phase5-reference/seed47-prefix-review-supplement-v1-20261011/root-archive1/seed47-prefix-review-supplement-v1.tar.gz", "archive_bytes": 46425, "archive_sha256": "23439ab8e71f67af20682e9749c1041bd6613f9e6914739bd0f220a53f166a19", "manifest_sha256": "1258c428d1138c0a4feae71eba90926bd8e17715f87231529a797247d79038e6", "regular_members": 42, "payloads": 41, "payload_bytes": 132834, "all_member_sum_cap_bytes": 4194304, "actual_uncompressed_tar_stream_bytes": 225280, "Mac_all_payloads_verified": true, "Dell_copy_verified": false, "references": [{"directory": "/private/tmp/stop47_feasible_start_pure_v3_20261011", "READY_sha256": "6daf7daf7bff0bffde2e419f681335371dc151fa21c431d718391879ff99643c", "payloads": 10, "payload_bytes": 45533}, {"directory": "/private/tmp/root_seed47_preparation_review_20261011", "READY_sha256": "765b61acb0d0b9024fa86b08e237bb08a19bda93b8d51e43e21f0965cad05bc8", "payloads": 11, "payload_bytes": 46009}, {"directory": "/private/tmp/stop47_initializer_source_review_v3_20261011", "READY_sha256": "fa178ade6f5519946882445c515b7402e5d996418a247f215aa16caf9a79781e", "payloads": 5, "payload_bytes": 14662}, {"directory": "/private/tmp/stop47_profile_resource_preentry_review_v1_20261011", "READY_sha256": "1a1499bed60fd73712351dbdef8157f9d30059c404ea497a75b53e78deb380ac", "payloads": 3, "payload_bytes": 6595}, {"directory": "/private/tmp/root_stop47_source_integration_review_20261011", "READY_sha256": "b4dab16c80c3d7d1d211e8a6de8f1d8b8f27fd44f323177a46c48a2a0d93ea3c", "payloads": 5, "payload_bytes": 8164}], "scope": "Separate pureV3/helper/source/profile reviews and coordinator error history. Root integration review timestamp is after actual47 entry, not a preentry permission. Actual47 raw/outcome outside scope. No Model/OSQP/B/C/physicalstop or phase acceptance by this archive. Sharedglobal3GiB prewrite plus4MiB compressed/uncompressed archive caps, CPU30wall60. Same-Mac aliases not secondphysicalcopy."}')
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

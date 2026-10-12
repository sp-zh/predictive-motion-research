from pathlib import Path
import hashlib,json,tarfile,resource
resource.setrlimit(resource.RLIMIT_CPU,(600,600))
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
root=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/seed48-prototype-supplement-v1-20261011-root1')
assert not root.is_symlink()
r=json.loads('{"archive_name": "seed48-prototype-supplement-v1.tar.gz", "ready_sha256": "236320052a5c871bb0afd52dc5d12507a06e4abf24080e4c8a5051fc22851749", "schema": "ROOT_SEED48_PROTOTYPE_SUPPLEMENT_READY_V1", "unit": "seed48-prototype-supplement-v1-20261011", "archive": "/Users/uot/Documents/ChatGPT/ros/results/phase5-reference/seed48-prototype-supplement-v1-20261011/root-archive1/seed48-prototype-supplement-v1.tar.gz", "archive_bytes": 72001, "archive_sha256": "dbcbcc612e38fa7230150398b391753b5e4d8e48e3d127f878432ac2675a35bb", "manifest_sha256": "5b2efd28012ef2104dfcaf3d3c35cff0d733004c68fb948487ecb5b65070f9f5", "regular_members": 58, "payloads": 57, "payload_bytes": 351587, "all_member_sum_cap_bytes": 4194304, "actual_uncompressed_tar_stream_bytes": 471040, "Mac_all_payloads_verified": true, "Dell_copy_verified": false, "references": [{"directory": "/private/tmp/stop47_face_cap_saved48analysis_v1_20261011", "READY_sha256": "70bb0d4867641fe26b049f8117133ce40f71a906bd595b213843f0cd9bffba04", "payloads": 9, "payload_bytes": 32830}, {"directory": "/private/tmp/stop47_face_basis_saved48pure_v1_20261011", "READY_sha256": "f4c5131c3d42623df15e86e350d3f2a5ccb9d33227ee62d860b89324fce32a44", "payloads": 10, "payload_bytes": 43880}, {"directory": "/private/tmp/stop47_face_basis_zero_step_saved48diagnostic_v1_20261011", "READY_sha256": "8b6b7368fa2a94d6cc3c9e17851d3d3d035c148e9092257191ef6168fc9cb479", "payloads": 10, "payload_bytes": 101767}, {"directory": "/private/tmp/stop47_face_basis_saved48pure_v2_20261011", "READY_sha256": "b7abcc3ab4d1f46dedbff9ef61f2536622eedc25a1e41ad8a12eb9e497e2ce3e", "payloads": 10, "payload_bytes": 101432}, {"directory": "/private/tmp/root_seed48_preparation_review_20261011", "READY_sha256": "a9b96e4d5dfcbeff7fb74d9712bb4ce79b50e7c8289e8f4c1832e4f27349e150", "payloads": 11, "payload_bytes": 56431}], "scope": "Separate saved47 diagnostic/prototype48 pure packets and narrowRootreview with failures and input-provenance limitation. Structured48source/budget/codec and actual48 outcomes outside scope. No Model/OSQP/B/C/physicalstop or phase acceptance by this archive. Sharedglobal3GiB prewrite plus4MiB compressed/uncompressed archive caps, CPU30wall60. Same-Mac aliases not secondphysicalcopy."}')
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

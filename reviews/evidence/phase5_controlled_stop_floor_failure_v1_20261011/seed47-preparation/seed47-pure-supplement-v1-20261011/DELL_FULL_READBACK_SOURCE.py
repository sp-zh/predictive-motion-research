from pathlib import Path
import hashlib,json,tarfile,resource
resource.setrlimit(resource.RLIMIT_CPU,(600,600))
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
root=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/seed47-pure-supplement-v1-20261011-root1')
assert not root.is_symlink()
r=json.loads('{"archive_name": "seed47-pure-current46-supplement-v1.tar.gz", "ready_sha256": "e1ff67940bee49ceafb57e264d236be2755dc72be090283dc2b65c707a583384", "schema": "ROOT_SEED47_PURE_SUPPLEMENT_READY_V1", "unit": "seed47-pure-supplement-v1-20261011", "archive": "/Users/uot/Documents/ChatGPT/ros/results/phase5-reference/seed47-pure-supplement-v1-20261011/root-archive1/seed47-pure-current46-supplement-v1.tar.gz", "archive_bytes": 29838, "archive_sha256": "66cf3ea7f20a88042263474bbfbc972c31ff7af08d2c7c1bc1e1461f5dd954fd", "manifest_sha256": "07a8485a59451470c85af174b84d7a36414e01d28d1c90040da05b600ab4385d", "regular_members": 27, "payloads": 26, "payload_bytes": 92386, "all_member_sum_cap_bytes": 4194304, "actual_uncompressed_tar_stream_bytes": 153600, "Mac_all_payloads_verified": true, "Dell_copy_verified": false, "references": [{"directory": "/private/tmp/stop47_feasible_start_pure_v1_20261011", "READY_sha256": "99bbb21be1920427d2a1b9aac3d2d02a390dc8440d6e393239739ea16bd0e6d1", "payloads": 11, "payload_bytes": 39799}, {"directory": "/private/tmp/stop47_feasible_start_pure_v2_20261011", "READY_sha256": "236f955fc7e22d47fd707397b0789f6dafc2f951b72c69fc8fb910e85dfd9f3a", "payloads": 11, "payload_bytes": 44323}], "scope": "Separate pure47 numerical initializer supplementary work after immutableactual46 archive capture. V1failure retained, V2pure result; NO actual47/Model/OSQP/B/C/physicalstop or phase acceptance. Sharedglobal3GiB prewrite plus4MiB compressed/uncompressed archive caps, CPU30wall60. Same-Mac aliases not secondphysicalcopy."}')
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

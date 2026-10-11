from pathlib import Path
import hashlib,json,tarfile
root=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/geometry-provider-actual-v1-20261011-root1')
r=json.loads('{"archive_name": "recorded-nominal-geometry-provider-v1.tar.gz", "ready_sha256": "8c31c6919ac5a53cb6321a511dd99abb3612777434b0fde0a85673e6df81233d", "schema": "ROOT_UNIT_ARCHIVE_READY_V1", "unit": "geometry-provider-actual-v1-20261011", "archive": "/Users/uot/Documents/ChatGPT/ros/results/phase5-reference/geometry-provider-actual-v1-20261011/root-archive1/recorded-nominal-geometry-provider-v1.tar.gz", "archive_bytes": 6884866, "archive_sha256": "ddcaebf79a1135d9c8a0699da618da393282de1327c08cb3fe0ce36df176cf55", "manifest_sha256": "fe3812dc6b93982d2477fe24389f59462443224f69e9ecdecfcec8e44192ca38", "regular_members": 400, "payloads": 399, "payload_bytes": 23245242, "Mac_all_payloads_verified": true, "Dell_copy_verified": false, "scope": "Fresh26 one recorded-nominal geometry diagnostic on immutable20 genuine q:1200 full9035-query snapshots/1326 Scene/11980410 primitives/4800 selected assistance rows and9 fixed FD probes; original floors/options/gates/11nonsmooth retained. Complete152 producer payloads,23 compilefailure/24-25 compileonly/26 actual graph, full independent saved-data review and inspected producer/Root plots; native SDK/cache and ELF remain pinned Dell only. No new ModelF1/MuJoCo/optimizer/control/privateowner/full-task/physical-stop/realtime/hardware/phase acceptance. Full FD aggregates are recorded native measurements, not independently replayed collision-engine outputs.", "phase5": "NOT_ACCEPTED", "phase6": "NOT_STARTED"}')
sha=lambda b:hashlib.sha256(b).hexdigest()
p=root/r['archive_name']
assert p.stat().st_size==r['archive_bytes'] and sha(p.read_bytes())==r['archive_sha256']
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
        b=tf.extractfile(m).read()
        if m.name!='ARCHIVE_MANIFEST.json':
            e=files[m.name]
            assert len(b)==e['bytes'] and sha(b)==e['sha256']
st=p.stat()
print(json.dumps({'schema':'ROOT_UNIT_DELL_FULL_READBACK_V1','archive':str(p),
 'archive_bytes':r['archive_bytes'],'archive_sha256':r['archive_sha256'],
 'ready_sha256':r['ready_sha256'],'manifest_sha256':r['manifest_sha256'],
 'regular_members_verified':len(members),'payloads_verified':len(files),
 'all_payloads_verified':True,'observed_mode':st.st_mode&0o7777,
 'observed_uid':st.st_uid,'observed_gid':st.st_gid,
 'qualification':'NTFS POSIX sealing/ownership change not asserted; no chmod attempted.'}))

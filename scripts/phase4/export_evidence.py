#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,os,sys,tarfile,io,subprocess,shutil,re,time
r=Path('/home/codextransfer/predictive_motion');sys.path.insert(0,str(r/'scripts'))
from source_manifest import source_files
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def write_atomic(p,data):
    tmp=p.with_name(p.name+'.part')
    with tmp.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.rename(tmp,p)
libs={};outputs={}
for name in ['results/phase4/frozen-v4/executed-identity/phase4_benchmark','build-phase4-adapters/phase4_benchmark','build-phase4-servo/servo_sidecar']:
    output=subprocess.check_output(['ldd',str(r/name)],text=True);outputs[name]=output
    for line in output.splitlines():
        paths=re.findall(r'(?:=>\s+)?(/\S+)',line)
        for value in paths:
            p=Path(value)
            if p.is_file():libs[str(p.resolve())]=sha(p.resolve())
for p in (r/'.vendor/osqp-1.0.0-install').rglob('*.a'):libs[str(p)]=sha(p)
(r/'results/phase4/post-run-dependency-identities.json').write_text(json.dumps({'scope':'post-run identity observation, not retrospective pre-run freeze','ldd':outputs,'sha256':libs},indent=2)+'\n')
note='''\nFinal export records full generated Servo URDF/SRDF/STL/robot configuration and all selected scene assets in its SHA-256 manifest. Dependency identities are explicitly post-run observations, not additions to the unchanged pre-run frozen-v4 identity. Future research freeze must close all model/scene/library inputs. Frozen diagnostic pose_position_m is the norm of the SE3 logarithm translation component; it must not be presented as final Euclidean physical position error.\nFocused post-freeze guard regression:21 checks passed and repaired benchmark compiled. Preparatory paired-analysis regression:8 tests passed; no final research comparison is implied.\n'''
for name in ['reviews/phase_4_executor_review.md','results/phase4/phase_4_executor_review.md']:
    p=r/name;p.write_text(p.read_text()+note)
files={str(p.relative_to(r)):p for p in source_files(r)}
for directory in ['results/phase4','results/cad','results/analysis','experiments/generated/phase4','experiments/generated/inspection','cad/generated','.vendor/menagerie/franka_fr3','.vendor/franka_description/robots']:
    for p in (r/directory).rglob('*'):
        if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts:files[str(p.relative_to(r))]=p
raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase4/raw')
for p in raw.rglob('*'):
    if p.is_file() and not p.is_symlink():files['results/phase4/raw/'+str(p.relative_to(raw))]=p
out=Path('/mnt/d/CodexTransfer/outbox/project-phase4');out.mkdir(exist_ok=False)
items={name:{'sha256':sha(p),'bytes':p.stat().st_size} for name,p in sorted(files.items())}
manifest=json.dumps({'scope':'Phase4 component and diagnostic evidence; root gate pending; no Phase5','files':items},indent=2).encode()+b'\n'
print(f'Packaging {len(items)} files, {sum(i["bytes"] for i in items.values())} bytes',flush=True)
partial=out/'phase4-evidence.tar.gz.part'
with partial.open('xb') as f:
    with tarfile.open(fileobj=f,mode='w:gz',compresslevel=4) as t:
        for name,p in sorted(files.items()):t.add(p,arcname='predictive_motion/'+name,recursive=False)
        info=tarfile.TarInfo('PHASE4_MANIFEST.json');info.size=len(manifest);t.addfile(info,io.BytesIO(manifest))
    f.flush();os.fsync(f.fileno())
print('Archive written; verifying every member against manifest',flush=True)
seen=set()
with tarfile.open(partial,'r:gz') as t:
    for member in t:
        if member.name=='PHASE4_MANIFEST.json':assert t.extractfile(member).read()==manifest;continue
        assert member.isfile() and member.name.startswith('predictive_motion/')
        name=member.name[len('predictive_motion/'):];assert name in items and name not in seen
        h=hashlib.sha256();f=t.extractfile(member)
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
        assert h.hexdigest()==items[name]['sha256'] and member.size==items[name]['bytes'],name
        seen.add(name)
assert seen==set(items)
# Recheck source and raw files so a growing payload cannot silently publish.
for name,p in files.items():assert p.stat().st_size==items[name]['bytes'] and sha(p)==items[name]['sha256'],name
digest=sha(partial);size=partial.stat().st_size
os.rename(partial,out/'phase4-evidence.tar.gz')
write_atomic(out/'PHASE4_MANIFEST.json',manifest)
write_atomic(out/'SHA256SUMS',(digest+'  phase4-evidence.tar.gz\n').encode())
ready={'archive':'phase4-evidence.tar.gz','sha256':digest,'bytes':size,'files':len(items),'frozen_trials':20,'completed_trials':15,'audited_raw_rows':185151,'actual_unit_cases':29,'post_freeze_guard_checks':21,'root_gate':'pending','phase5':'not started','scope':'component/diagnostic only'}
write_atomic(out/'READY.json',(json.dumps(ready,indent=2)+'\n').encode())
windows=Path('/mnt/c/Users/SYSUR/Documents/Codex/2026-09-16/zh/outputs/phase4')
for name in ['READY.json','SHA256SUMS','PHASE4_MANIFEST.json']:shutil.copyfile(out/name,windows/name)
for name in ['phase_4_executor_review.md','post-freeze-guard-source.json','root-independent-csv-audit.json']:shutil.copyfile(r/'results/phase4'/name,windows/name)
print(json.dumps(ready,indent=2),flush=True)

#!/usr/bin/env python3
import datetime,hashlib,json,tarfile
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/signed-command-cone-v1';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();frozen=json.loads((base/'frozen.json').read_text());assert all(sha(f)==h for f,h in frozen['files'].items())
review=p/'reviews/phase_5_signed_command_velocity_cone_20261007.md'
review.write_text('''# Isolated signed command velocity continuation

PASS_ISOLATED_SPEED_CONE:6 independent sequence/grid/contract tests pass; source frozen before tests and unchanged. No plant run, native QP, main MPC modification, physical/geometry/position stopping certificate or Phase5 acceptance.

History is signed accepted velocity w and accepted acceleration alpha, candidate acceleration a, timestep δ=.004s. Limits |w|≤V=.0625rad/s,|a|≤A=1rad/s²,|a-alpha|≤Jδ with J=20rad/s³ remain fixed. Candidate next w'=w+δa. Maximum-jerk recovery toward zero gives all integer constraints -V-.5Jδ²K(K-1)≤w+Kδa≤V+.5Jδ²K(K-1). Only K=1..ceil(A/(Jδ))+1 are required: beyond the stationary integer recovery point the extremum decreases. Exact closed-form acceleration bound is the minimum of distance/(δ(n+1))+.5Jδn at floor/ceil(max(0,sqrt(2distance/J)/δ-1)). Use RET00264epsilon interior margin, no enlargement of hard bounds.

This translates RET002 progressStopBounds speed component under r=w+V,R=2V. Progress position s endpoint bound is not applicable and omitted. The existing main-MPC coneRows prefix/terminal formulation starts from r_after and holds the chosen acceleration once more, so is more conservative; prefix semantics must not be conflated. Here constraints from w_before include the immediate issued candidate and all future max-jerk recovery. QP rows on w' have coefficient K and bounds (K-1)w±V±.5Jδ²K(K-1). Existing derivative SI acceptance still required independently; passing velocity cone alone does not prove future position/geometry feasibility.

Independent oracle explicitly integrates extremal recovery rather than the closed form.1500 randomized histories×33 candidate samples match it;3000 random QP-row candidates match it;500 random initial histories test repeated bounded stopping when feasible. Actual v1 failed history at tick792 is rejected without command. A separate immediate-feasible candidate(.062,.16,a=.12) passes immediate speed/jerk but fails future recovery, while a safer candidate interval exists. Reflection and exact hard boundaries pass.

All retained v1 substep2 command histories examined without modifying raw. First noncontinuable history is tick785, joint3,w=-.040700006326262854,alpha≈-1; tick785–792 cannot continue under the unchanged speed/jerk rules. No issued command rewritten and no success claim from this retrospective analysis. Inputs and exact controller source snapshot are archived. The plot displays recorded w and independent recovery headroom; units radians/s and milliradians/s. No geometry or CAD change; previous backed actual recorded-state render remains applicable.
''')
image=base/'phase5_signed_velocity_continuation.png';(base/'visual_inspection.json').write_text(json.dumps({'image_sha256':sha(image),'status':'PASS_PRESENTATION_LAYOUT','inspected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'findings':'Recorded speed and future recovery deficit legible; first failing tick785 correctly marked; no clipping or CAD change.'},indent=2)+'\n')
sources=['scripts/phase5/signed_command_velocity_cone.py','scripts/phase5/signed_command_velocity_cone_test.py','scripts/phase5/run_signed_cone_analysis.py','scripts/phase5/plot_signed_command_cone.py','scripts/phase5/publish_signed_cone_analysis.py',str(review.relative_to(p))];items={'project/'+s:p/s for s in sources}
for f in base.rglob('*'):
 if f.is_file():items['project/'+str(f.relative_to(p))]=f
for f in frozen['files']:
 path=Path(f)
 if f.startswith(str(p)):items['project/'+str(path.relative_to(p))]=path
 else:items['raw/retained-v1/raw.csv']=path
manifest={name:{'sha256':sha(f),'bytes':f.stat().st_size} for name,f in items.items()};(base/'CHECKPOINT_FILE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
small={s:manifest['project/'+s] for s in sources}
for name in ['report.json','phase5_signed_velocity_continuation.png','phase5_signed_velocity_continuation.json','visual_inspection.json']:
 f=base/name;small[str(f.relative_to(p))]={'sha256':sha(f),'bytes':f.stat().st_size}
(base/'BACKUP_SOURCE_MANIFEST.json').write_text(json.dumps(small,indent=2)+'\n')
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:items['project/'+str((base/name).relative_to(p))]=base/name
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/signed-command-cone-v1-20261007');dest.mkdir(exist_ok=False);part=dest/'signed-command-cone-v1.tar.gz.part'
with tarfile.open(part,'w:gz') as t:
 for name,f in sorted(items.items()):t.add(f,arcname=name,recursive=False)
archive=dest/'signed-command-cone-v1.tar.gz';part.rename(archive)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(items)
 for m in t.getmembers():assert m.isfile() and m.name in items and hashlib.sha256(t.extractfile(m).read()).hexdigest()==sha(items[m.name])
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(items),'archive_members_verified':True,'mac_copy_verified':False,'source_manifest':str(base/'BACKUP_SOURCE_MANIFEST.json'),'source_manifest_sha256':sha(base/'BACKUP_SOURCE_MANIFEST.json'),'scope':'Isolated signed command speed cone analysis/tests only; main MPC unchanged; no position/geometry future stop or Phase5 acceptance'}
(dest/'READY.json.part').write_text(json.dumps(ready,indent=2)+'\n');(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2))

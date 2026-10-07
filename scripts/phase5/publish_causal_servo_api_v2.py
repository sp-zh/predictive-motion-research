#!/usr/bin/env python3
import datetime,hashlib,json,tarfile
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/causal-soft-servo-cpp-v2';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();freeze=json.loads((base/'frozen.json').read_text());assert all(sha(f)==h for f,h in freeze['files'].items())
review=p/'reviews/phase_5_causal_servo_api_v2_20261007.md';review.write_text('''# Causal servo v2 public API and frozen branch verification

PASS_ISOLATED_CAUSAL_API_BRANCH_V2 only. Previous v1 source/binary/compile failures/reference archives unchanged. New isolated directory adds model validation at domain/cell public entry and state/control shape/finite validation before cell composition. Scalar soft physics,4ms/two2ms clock, Jacobian/defect composition, all FR3 parameters and original domain unchanged. No refitting, native QP/plant/main-MPC/guard integration or Phase5 acceptance.

27 invalid scenarios/78 direct public-entry checks all reject before dimension-unsafe Eigen operations: empty/mismatched vectors; nonfinite mass/bias/impedance/box; nonpositive mass,kp,decay/velocity bound; negative damping/friction; impedance outside(0,1]; reversed q/error boxes; wrong/nonfinite state/control. Domain checks do not take control arguments, so three control-only scenarios apply to cycle/cell only.10 original initial/forecast/mesh negative controls remain rejected. Public model validation can therefore be used independently of a correct canonical CLI.

Root exports fixedc63f oracle packet SHA8f09f79a23a6be6f3785dc76612c9a1f43b90b038e1fb248d616116dcb1276f7 directly from the already independently reviewed functions. Eight cases: n1/n7 interior and both saturations (six original smooth fixtures), and artificial n1 exact±clip thresholds (two). Compare all next state,A,B,defect and both physical branch vectors. Maximum branch numerical difference5.825201432330118e-15 below prefrozen5e-12; every branch matches. Exact thresholds choose the declared saturated-side Jacobian and then enter interior on substep2. Ordinary derivative at equality is nonunique: no ordinary central FD or unique-derivative claim. Only the separate synthetic threshold fixture has±2 box; original FR3 box/parameters immutable.

Both prior n1/nonuniform5cell/.2s and n7/nonuniform20cell/.8s nominal oracle regressions match states,A/B,defects,condensed offsets and full control/initial sensitivities, maximum2.2709265024012382e-14. No new oracle or FD is generated. Model/source/binary/reference/inputs frozen before probes and verified unchanged. GNU13.3 C++17 -Wall -Wextra -Werror builds both targets successfully.

Inspected categorical plot shows actual matched two-substep branches, including threshold saturated→interior switch. N7 vector branches are uniform in these fixtures, explicitly stated in metadata. It is a model algebra visual, not physical behavior or acceptance evidence. No CAD/geometry change; existing actual FR3 recorded-state render remains applicable. Model accuracy still fails v3 larger recorded inputs at2/4ms, so v2 robust API/parity does not expand eligibility. Root owns source/showcase/private-Git checkpoint integration.
''');image=base/'phase5_causal_servo_api_v2_branches.png';(base/'visual_inspection.json').write_text(json.dumps({'image_sha256':sha(image),'status':'PASS_PRESENTATION_LAYOUT','inspected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'findings':'All8 case labels and2 substeps legible; exact threshold nonunique derivative caveat visible; no clipping or CAD change.'},indent=2)+'\n')
sources=['tools/phase5_causal_servo_v2/CMakeLists.txt','tools/phase5_causal_servo_v2/causal_soft_servo.hpp','tools/phase5_causal_servo_v2/causal_soft_servo_probe.cpp','tools/phase5_causal_servo_v2/causal_soft_servo_api_probe.cpp','scripts/phase5/prepare_causal_servo_api_v2.py','scripts/phase5/run_causal_servo_api_v2.py','scripts/phase5/plot_causal_servo_api_v2.py','scripts/phase5/publish_causal_servo_api_v2.py',str(review.relative_to(p))];items={'project/'+s:p/s for s in sources}
for f in base.rglob('*'):
 if f.is_file():items['project/'+str(f.relative_to(p))]=f
for f in freeze['files']:
 path=Path(f);items['project/'+str(path.relative_to(p))]=path
manifest={name:{'sha256':sha(f),'bytes':f.stat().st_size} for name,f in items.items()};(base/'CHECKPOINT_FILE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');small={s:manifest['project/'+s] for s in sources}
for name in ['report.json','phase5_causal_servo_api_v2_branches.png','phase5_causal_servo_api_v2_branches.json','visual_inspection.json']:
 f=base/name;small[str(f.relative_to(p))]={'sha256':sha(f),'bytes':f.stat().st_size}
(base/'BACKUP_SOURCE_MANIFEST.json').write_text(json.dumps(small,indent=2)+'\n')
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:items['project/'+str((base/name).relative_to(p))]=base/name
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/causal-soft-servo-cpp-v2-20261007');dest.mkdir(exist_ok=False);part=dest/'causal-soft-servo-cpp-v2.tar.gz.part'
with tarfile.open(part,'w:gz') as t:
 for name,f in sorted(items.items()):t.add(f,arcname=name,recursive=False)
archive=dest/'causal-soft-servo-cpp-v2.tar.gz';part.rename(archive)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(items)
 for m in t.getmembers():assert m.isfile() and m.name in items and hashlib.sha256(t.extractfile(m).read()).hexdigest()==sha(items[m.name])
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(items),'archive_members_verified':True,'mac_copy_verified':False,'source_manifest':str(base/'BACKUP_SOURCE_MANIFEST.json'),'source_manifest_sha256':sha(base/'BACKUP_SOURCE_MANIFEST.json'),'scope':'Robust public API and8 fixed-root branch algebra/nominal regressions only; original FR3 domain; no predictor expansion/plant/controller/Phase5 acceptance'};(dest/'READY.json.part').write_text(json.dumps(ready,indent=2)+'\n');(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2))

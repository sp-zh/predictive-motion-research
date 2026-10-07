#!/usr/bin/env python3
import datetime,hashlib,json,tarfile,sys
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/public-coupled-servo-v2-reference-contract';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();freeze=json.loads((base/'frozen.json').read_text());assert all(sha(f)==h for f,h in freeze['files'].items());sys.path.insert(0,str(p/'scripts/phase5'));from materialize_identity import materialize
materialize(base/'frozen.json')
review=p/'reviews/phase_5_public_coupled_reference_v2_20261007.md';review.write_text('''# Public coupled reference contract v2

PASS_FIXED_FR3_REFERENCE_CONTRACT_V2 only. Clone v1 into independent Python modulev2, correct standard positive-solref friction B=2/(dmax*timeconst), removing erroneous dampratio factor. Original fixedratio1 B remains bitwise identical105.26315789473685s^-1. Originalv1 source/40pre-scan/failedpublication/finalarchives/reports unchanged and old generic-parameter limitation retained.

Support is deliberately narrow: fixed seven-axis FR3 inspection public model, instantaneous affine joint actuators/gear1, same M/bias/payload/armature once, same R andforce/control clamp/implicitfast. Solimp profile must remain exactly(.9,.95,.001,.5,2) on7axes; positive finite solref and timeconst≥2*.002 required. Below2h, engine reference-safety replacement is not implemented and is explicitly rejected, not approximated. Nonpositive/nonfinite reference values and different impedance profiles reject. Other robot/force/contact/limit/equality/unknown-force regimes are unsupported; no generic physical accuracy or safety certificate. No derivatives,C++prediction/mainMPC/newfit/physicalvalidation.

Synthetic dampratio.5 and2 both give unchanged standardB; these are algebraic metadata tests, not real robot or simulator parameter changes. Five unsupported cases reject:timeconst.003,ratio0,negative timeconst,nonfinite ratio,changed solimp. Current ratio1 baseline19fixed original TRAIN windows (starts100,500,1250,2400,2500;horizons2/4/40/800ms) are bitwise equalv1/v2. Selected actual errors≤4.440892098500626e-16rad and2.288967626551397e-15rad/s. Tick2500/800ms has only380substeps and is retained as incomplete, not shortened. No full TRAINv2rescan claim; no new untouched holdout. Seven fixed rootfriction fixtures recur with originalH/ell KKT checked by unchanged solver.

88 explicit source/SDK/reader/staticparameters/oldTRAIN input/runtime/XML+transitiveasset identities are recorded before anyv2prediction. All40XML/asset current hashes remain originalTRAIN cache identities; NumPy/linalg/BLAS files now explicitly listed with pre-run timestamp. This is a listed-input closure, not a claim that every Python environment file is frozen. Post-probe hashes and originalv1 all40files checked unchanged.

One inspected coefficient plot uses actual synthetic test values and documented retainedv1formula. B units s^-1,ratio dimensionless;actualrobot ratio1and no physical parameter changes labeled. Existing actual FR3 render/task videos remain appropriate unchanged geometry context; no new CAD/trajectory. Root independent review/privateGitbackup required before a separately prefrozen new development validation protocol. Original accuracy/command/physical/geometry/nativeSOLVED/SI/age/budget gates unchanged;Phase5pending.
''');image=base/'phase5_public_coupled_reference_v2.png';(base/'visual_inspection.json').write_text(json.dumps({'image_sha256':sha(image),'status':'PASS_PRESENTATION_LAYOUT','inspected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'findings':'Standard coefficient, legacy formula and frozenactualratio1 clearly distinguished; synthetic metadata/compatibility scope and units visible without clipping; no CAD change.'},indent=2)+'\n')
sources=['scripts/phase5/public_coupled_servo_v2.py','scripts/phase5/prepare_public_coupled_servo_v2.py','scripts/phase5/run_public_coupled_reference_v2.py','scripts/phase5/plot_public_coupled_reference_v2.py','scripts/phase5/publish_public_coupled_reference_v2.py',str(review.relative_to(p))];items={'project/'+s:p/s for s in sources};cache=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/identity-cache')
for name,h in freeze['files'].items():assert sha(cache/h)==h;items['frozen-input-cache/'+h]=cache/h
for f in base.rglob('*'):
 if f.is_file():items['project/'+str(f.relative_to(p))]=f
manifest={name:{'sha256':sha(f),'bytes':f.stat().st_size} for name,f in items.items()};(base/'CHECKPOINT_FILE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');small={s:manifest['project/'+s] for s in sources}
for name in ['report.json','protocol.json','frozen.json','phase5_public_coupled_reference_v2.png','phase5_public_coupled_reference_v2.json','visual_inspection.json']:
 f=base/name;small[str(f.relative_to(p))]={'sha256':sha(f),'bytes':f.stat().st_size}
(base/'BACKUP_SOURCE_MANIFEST.json').write_text(json.dumps(small,indent=2)+'\n')
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:items['project/'+str((base/name).relative_to(p))]=base/name
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-coupled-servo-v2-reference-contract-20261007');dest.mkdir(exist_ok=False);part=dest/'public-coupled-servo-v2-reference-contract.tar.gz.part'
with tarfile.open(part,'w:gz',dereference=True) as t:
 for name,f in sorted(items.items()):t.add(f,arcname=name,recursive=False)
archive=dest/'public-coupled-servo-v2-reference-contract.tar.gz';part.rename(archive)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(items)
 for m in t.getmembers():assert m.isfile() and m.name in items and not m.name.startswith('/') and '..' not in Path(m.name).parts and hashlib.sha256(t.extractfile(m).read()).hexdigest()==sha(items[m.name])
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(items),'archive_members_verified':True,'explicit_prelisted_cache_inputs':len(freeze['files']),'mac_copy_verified':False,'source_manifest':str(base/'BACKUP_SOURCE_MANIFEST.json'),'source_manifest_sha256':sha(base/'BACKUP_SOURCE_MANIFEST.json'),'scope':'Standard reference coefficient/fixedFR3support and19existingTRAIN compatibility only; no fullnewtraining/physical/holdout/controller/Phase5 acceptance'};(dest/'READY.json.part').write_text(json.dumps(ready,indent=2)+'\n');(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2))

#!/usr/bin/env python3
"""Preserve the fixed-model C++ prototype and all diagnostic outcomes."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path('/home/codextransfer/predictive_motion');BASE=ROOT/'results/phase5/development/public-coupled-cpp-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n')
freeze=json.loads((BASE/'frozen_before_predictions.json').read_text());report=json.loads((BASE/'parity-attempt1/report.json').read_text())
assert report['status']=='PASS_FIXED_RECORDED_CPP_PROTOTYPE_ONLY' and not report['errors']
assert report['source_freeze_sha256']==sha(BASE/'frozen_before_predictions.json')
for rec in freeze['files']:
 assert sha(rec['path'])==rec['sha256'] and sha(rec['immutable_copy'])==rec['sha256']
review=ROOT/'reviews/phase_5_public_coupled_cpp_20261007.md'
review.write_text('''# Independent C++ public transition prototype

Phase5 remains NOT_ACCEPTED; Phase6 NOT_STARTED. This work ports the fixed FR3 public Python v2 2ms conditional transition into a separate C++ Model/Data API. The main MPC, old URDF, accepted Phase4 results and original Python/public constants remain unchanged. No plant stepping, new seed run, fitting, Jacobian or controller integration occurs here.

The model uses Pinocchio4.1.0 MJCF with nq/nv7, scalar joints in exact idx_q/idx_v0..6, joint7 mass1.077143kg including the0.45kg tool, and armature[.195x4,.074x3]kg*m^2 as parsed. CRBA already includes armature. Full nle includes gravity/Coriolis; public affine actuator/control/joint actuator force clamps and passive damping are applied. W=M^-1; R comes from static invweight0; B=2/(dmax*timeconst). The coupled friction force solves a box QP with original-H KKT<=1e-10. v_next=v+.002*(M+.002*diag(D))^-1*(smooth+friction); q_next=q+.002*v_next. Full affine damping D remains in the implicit solve at force clamps. The API owns independent Pinocchio Model/Data and receives no plant pointer. Nonfinite inputs, intermediate actuator arithmetic before clamps, factorization inputs/results/residuals and output states are rejected.

Constructor support is explicit fixed FR3: MuJoCo3.3.7 public constants, instantaneous affine joint gear1, fixed impedance, no external wind/fluid/spring/gravitycompensation, no constraints or joint-limit contacts. Compared with the Python reader, C++ also requires passive>=0, invweight0>0, trnid second column-1, exactly12 body gravitycompensation values, finite ordered ranges and binary flags. These stricter checks do not certify a generalized Python parameter support set. Generic box API checks n1..7, finite symmetric SPD H, finite ell and nonnegative finite eta; eta0 is supported and labeled2. Arbitrary tiny positive eta is not supported correctly: with H=[1],ell=[1],eta=[1e-12], the optimum is lower-bound x=-eta but final labels overlap within tolerance1e-10 and the upper label wins, producing a false original-KKT rejection. The frozen Python implementation has the same limitation, so Python parity does not detect it. Current fixed FR3 eta>=.248 avoids this overlap; safe false rejection affects API support, not the reported fixed-FR3 forecasts. Preserve frozenv1 unchanged; independent root native reproduction and a later separate API correction are required before broader eta support is claimed.

Before forecasts, 2548 source/input/native-SDK/model/asset/compiler dependency identities were SHA-256 frozen and materialized in Dell D storage. Runtime library closure is captured with ldd; SDK headers are captured from compiler dependency files. Both previously seen TRAIN91011 and development91013 raw hashes are pinned. Conditional targets are read from recorded input, while predicted states propagate without future actual-state use.

Fixed TRAIN starts100/500/1250/2400/2500 and seen91013 starts100/500/690/920/2400/2500 are checked at1/2/20/400 substeps. All40 complete recorded windows pass; four EOF windows are incomplete and retained. Four positive synthetic transition cases cover nominal/mixed friction/control and force clamps; eight state rejection cases include wrong dimensions, NaN/Inf, boundary contact and finite pre-clamp overflow. Fourteen generic friction cases include five Python parity positives and nine invalid inputs. Twenty public-constant variants reject explicitly. Every diagnostic case is checked by typed bool and complete trace, rather than process exit0 alone; per-case failures are retained in JSON with success=false. Constructor failure exits1 and refuses existing outputs.

3437 forecast substeps pass. Maximum C++/Python position difference0rad; velocity difference5.551115123125783e-17rad/s. Selected recorded physical maximum q error4.440892098500626e-16rad, v error3.9603736956550506e-15rad/s. Declared parity tolerances q1e-12/v1e-11 and box force1e-12 are met; original short q1e-6/v1e-4 and long q1e-4/v1e-3 gates remain unchanged. State friction branches-1/0/+1 appear; eta0 generic case covers2. These are near-roundoff fixed-input results, not numerical bounds over a general domain.

The actual parity plot is a development diagnostic, with rad/rad/s/ms units and a declared1e-18 display floor for zeros. Its first layout had footer overlap and is retained under visual-attempt1; final image was visually inspected. The initial build Eigen matrix+diagonal expression failure and exact source snapshots, metadata preflight string-typed output, and first dependency-cache parent creation failure are all retained. Later source fixes were compiled and frozen before the first forecasts. No numerical parity failure occurred in the reported run. Dependency/build caches remain out of Git; immutable regular-member evidence archive and SHA/READY verification carry the large bytes.

Selected overlapping conditional windows on previously seen data do not establish generalization, task completion, derivatives, friction-switch differentiability or250Hz. No new complete task trajectory exists, so no task-success video is produced. Independent root checks and remote-verified Git checkpoint are required before this work unit is reported backed up; neither backup nor prototype PASS accepts Phase5.
''')
items={}
def add(prefix,p):
 p=Path(p)
 if p.is_dir():
  for f in p.rglob('*'):
   if f.is_file():items[prefix+'/'+str(f.relative_to(p))]=f
 else:items[prefix]=p
add('project/tools/phase5_public_coupled_cpp',ROOT/'tools/phase5_public_coupled_cpp');add('project/'+str(BASE.relative_to(ROOT)),BASE)
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json','publisher.stdout','publisher.stderr']:
 items.pop('project/'+str((BASE/name).relative_to(ROOT)),None)
small={}
for name in ['scripts/phase5/verify_public_coupled_cpp.py','scripts/phase5/plot_public_coupled_cpp.py','scripts/phase5/publish_public_coupled_cpp.py',str(review.relative_to(ROOT)),'figures/phase5/phase5_public_coupled_cpp_parity.png','figures/phase5/phase5_public_coupled_cpp_parity.json']:
 add('project/'+name,ROOT/name);small[name]={'sha256':sha(ROOT/name),'bytes':(ROOT/name).stat().st_size}
for f in (ROOT/'tools/phase5_public_coupled_cpp').glob('*'):
 if f.is_file():small[str(f.relative_to(ROOT))]={'sha256':sha(f),'bytes':f.stat().st_size}
for name in ['frozen_before_predictions.json','parity-attempt1/report.json','inputs/declared_scope.json']:
 p=BASE/name;small[str(p.relative_to(ROOT))]={'sha256':sha(p),'bytes':p.stat().st_size}
for rec in freeze['files']:add('immutable_dependencies/'+rec['sha256'],rec['immutable_copy'])
save(BASE/'CHECKPOINT_FILE_MANIFEST.json',{n:{'sha256':sha(p),'bytes':p.stat().st_size} for n,p in items.items()})
save(BASE/'BACKUP_SOURCE_MANIFEST.json',small)
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:add('project/'+str((BASE/name).relative_to(ROOT)),BASE/name)
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-coupled-cpp-v1-scope-correction-20261007');dest.mkdir(exist_ok=False)
part=dest/'public-coupled-cpp-v1.tar.gz.part'
with tarfile.open(part,'w:gz',dereference=True) as tar:
 for name,p in sorted(items.items()):tar.add(p,arcname=name,recursive=False)
archive=dest/'public-coupled-cpp-v1.tar.gz';part.rename(archive)
with tarfile.open(archive) as tar:
 members=tar.getmembers();assert len(members)==len(items)
 for m in members:
  assert m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts and m.name in items
  blob=tar.extractfile(m).read();assert len(blob)==items[m.name].stat().st_size and hashlib.sha256(blob).hexdigest()==sha(items[m.name])
for rec in freeze['files']:assert sha(rec['path'])==rec['sha256']
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'regular_members':len(items),'archive_payloads_verified':True,'frozen_manifest_sha256':sha(BASE/'frozen_before_predictions.json'),'source_manifest_sha256':sha(BASE/'BACKUP_SOURCE_MANIFEST.json'),'gate':report['status'],'all_failures_retained':True,'Mac_copy_verified':False,'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED','scope':'Selected previously seen fixed-recorded-input C++ prototype; no plant/controller/runtime/task acceptance.'}
save(dest/'READY.json.part',ready);(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2),flush=True)

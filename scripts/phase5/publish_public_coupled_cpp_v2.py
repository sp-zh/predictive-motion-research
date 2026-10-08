#!/usr/bin/env python3
"""Archive v2 exact-bound/API gate repair, including both failed QA attempts."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path('/home/codextransfer/predictive_motion');BASE=ROOT/'results/phase5/development/public-coupled-cpp-v2'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n')
freeze_path=BASE/'frozen_after_report_repair_before_repeat.json';freeze=json.loads(freeze_path.read_text());original=json.loads((BASE/'frozen_before_predictions.json').read_text());report=json.loads((BASE/'parity-attempt2/report.json').read_text())
assert report['status']=='PASS_FIXED_RECORDED_CPP_PROTOTYPE_ONLY' and not report['errors']
assert report['source_freeze_sha256']==sha(freeze_path)
for rec in freeze['files']:assert sha(rec['path'])==rec['sha256'] and sha(rec['immutable_copy'])==rec['sha256']
for rec in original['files']:assert sha(rec['immutable_copy'])==rec['sha256']
for file,digest in json.loads((BASE/'v1_preserved_before_v2.json').read_text()).items():assert sha(ROOT/file)==digest
review=ROOT/'reviews/phase_5_public_coupled_cpp_v2_20261007.md'
review.write_text('''# Isolated C++ v2 bound-label and output-gate correction

Phase5 remains NOT_ACCEPTED; Phase6 NOT_STARTED. v1 is retained with its original source, native binary, Python baseline, public constants, raw evidence and frozen packet unchanged. Before this work, v1 checkpoint c7e0cb057562ec8fbfd8e53d6b5ed6788d342d45 was independently checked against the private remote. v2 owns a separate namespace phase5_public_coupled_v2, tool directory and build target. No main-MPC, plant, parameter fitting, Jacobian or augmentation changes occur.

The v1 final labels could overlap when eta was smaller than the1e-10 labeling tolerance, overwriting lower with upper and incorrectly rejecting H=[1],ell=[1],eta=[1e-12]. v2 marks eta0 fixed2 first. Positive eta uses the actual lower/upper bound comparisons, with strict interior0. An exact bound with zero gradient reports that bound side. The active-face numerical algorithm, original-H KKT<=1e-10, force constraints, finite checks and factorization/solve-residual guards remain unchanged. The convention at a threshold does not imply a unique derivative. Fixed FR3 physical equations and public parameters are identical to v1; tool mass and armature remain parsed once.

The independent scalar oracle is clamp(-ell/H,-eta,eta). At ell±1 the tiny saturated force must equal the exact floating bound and have the correct side label, not merely pass an absolute1e-10 force tolerance. Tiny interior components require<=8ULP. Coupled fixtures use independent face enumeration and the original H; its normal-cone classifications use actual bounds rather than overlapping tolerance labels. All ten declared ell±1 cases across eta1e-12/1e-100/min-normal/1e-310/min-subnormal pass with exact force and0ULP error. Four tiny interior/zero-gradient threshold fixtures and two multi-dimensional tiny/large/zero fixtures pass. Input serialization accepts all tested values, including5e-324, without silent zero conversion. A bad-conversion serialization rejection policy was declared before predictions, but no such rejection occurred. This is tested serialization scope, not a universal parser or arithmetic certificate.

Thirty generic QP cases include21 positive analytic/enumerated fixtures and9 expected invalid-input rejections. The explicit finite/SPD/iteration/residual support limits remain; no guarantee is made for arbitrary numerical scale, every mathematical SPD input or generic termination. Eight state inputs and twenty public-constant variants reject as expected. All52 state cases are accounted for:40 complete recorded windows,4 positive synthetic transition cases and8 invalid inputs.

The new native-output gate runs before numerical scoring: exact state/box lengths, unique ordered names, genuine bool values, full finite seven-dimensional traces including negative partial traces, last/trace consistency, finite M/W/H and other diagnostics, clip-count integer ranges and native original KKT. Metadata scalar dimensions, joint indices and names are typed/unique, and model metadata is compared with the fixed Python MJCF model. All numeric outputs must be finite; JSON NaN and integers outside finite-double range raise NativeOutputError. Two valid structural controls pass;33 deliberately corrupted output controls reject, including empty/dropped/repeated rosters, string bools, short traces, NaN/Inf, bad clip/KKT/branch fields, huge integers and a nonfinite negative partial trace. These synthetic output corruptions are not actual native-core failures.

The same predeclared TRAIN91011 starts100/500/1250/2400/2500 and previously seen development91013 starts100/500/690/920/2400/2500 remain at1/2/20/400 substeps. Forty complete windows plus the four positive transition cases produce3437 substeps. All original short q1e-6/v1e-4 and long q1e-4/v1e-3 error gates pass; four EOF windows remain incomplete and retained. C++/Python maximum q parity0rad, v5.551115123125783e-17rad/s; recorded physical q4.440892098500626e-16rad and v3.9603736956550506e-15rad/s. Native force labels obey the new exact-bound convention, while v1 near-bound labels are not used to define v2 correctness. Recorded-target conditional forecasting, previously seen inputs and overlapping windows do not establish a general accuracy domain, new task result, online timing or controller acceptance.

The first input preparation failed because a NumPy bool support flag was not JSON serializable; source and failure are preserved under prepare-attempt1. The first frozen forecast/scoring attempt subsequently failed while serializing a NumPy bool exact_bound report field. Complete native outputs, stdout/stderr/exit and original source/freeze/cache remain under parity-attempt1 and serialization-attempt1. Only the report field cast and attempt paths changed; native/model/helper/inputs stayed unchanged. A second source/dependency freeze preceded the repeat predictions. Its initial reused scope wording was corrected before the repeat to explicitly describe report-only repair; the original metadata-at-creation record is retained. No numerical failure is reclassified as success, no failed file is overwritten, and no physical run is repeated. Final freeze3593ef671e31d6bee9a2b93a2642ebe8a50fb9a39cc5dccff3a788264c8b4a1f contains2540 live/cache identities; first freeze cdac053a941da1eec0754e266da4447a56f3511a3e08922c55cf4b0120897181 is preserved. v1 preservation hashes are checked before and after.

Two actual data-backed figures are inspected: the recorded-state regression plot uses rad/rad/s/ms and the declared1e-18 display floor for zeros; the API plot shows actual force/eta for every tiny-bound scalar case and separates real input rejections from synthetic output-gate controls. Hashes, source/report identities and scope are in the corresponding figure provenance JSON. No complete new task trajectory exists, so no new task-success video is produced. Source/reviews/figures and a small checkpoint record go to private Git after independent root review; immutable dependency/data evidence is retained in SHA/READY regular-member archives on Dell and Mac. Backup and this API/gate PASS do not accept Phase5.
''')
items={}
def add(name,p):
 p=Path(p)
 if p.is_dir():
  for f in p.rglob('*'):
   if f.is_file():items[name+'/'+str(f.relative_to(p))]=f
 else:items[name]=p
add('project/tools/phase5_public_coupled_cpp_v2',ROOT/'tools/phase5_public_coupled_cpp_v2');add('project/'+str(BASE.relative_to(ROOT)),BASE)
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:items.pop('project/'+str((BASE/name).relative_to(ROOT)),None)
sources=['scripts/phase5/verify_public_coupled_cpp_v2.py','scripts/phase5/validate_public_coupled_native_output_v2.py','scripts/phase5/plot_public_coupled_cpp_v2.py','scripts/phase5/plot_public_coupled_cpp_v2_api.py','scripts/phase5/publish_public_coupled_cpp_v2.py',str(review.relative_to(ROOT))]
sources += ['figures/phase5/'+name for name in ['phase5_public_coupled_cpp_v2_parity.png','phase5_public_coupled_cpp_v2_parity.json','phase5_public_coupled_cpp_v2_api.png','phase5_public_coupled_cpp_v2_api.json']]
small={}
for name in sources:add('project/'+name,ROOT/name);small[name]={'sha256':sha(ROOT/name),'bytes':(ROOT/name).stat().st_size}
for p in (ROOT/'tools/phase5_public_coupled_cpp_v2').glob('*'):
 if p.is_file():small[str(p.relative_to(ROOT))]={'sha256':sha(p),'bytes':p.stat().st_size}
for p in [freeze_path,BASE/'frozen_before_predictions.json',BASE/'parity-attempt2/report.json',BASE/'inputs/declared_scope.json']:
 small[str(p.relative_to(ROOT))]={'sha256':sha(p),'bytes':p.stat().st_size}
for rec in freeze['files']+original['files']:add('immutable_dependencies/'+rec['sha256'],rec['immutable_copy'])
save(BASE/'CHECKPOINT_FILE_MANIFEST.json',{name:{'sha256':sha(p),'bytes':p.stat().st_size} for name,p in items.items()});save(BASE/'BACKUP_SOURCE_MANIFEST.json',small)
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:add('project/'+str((BASE/name).relative_to(ROOT)),BASE/name)
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-coupled-cpp-v2-20261007');dest.mkdir(exist_ok=False);part=dest/'public-coupled-cpp-v2.tar.gz.part'
with tarfile.open(part,'w:gz',dereference=True) as tar:
 for name,p in sorted(items.items()):tar.add(p,arcname=name,recursive=False)
archive=dest/'public-coupled-cpp-v2.tar.gz';part.rename(archive)
with tarfile.open(archive,'r|gz') as tar:
 count=0
 for member in tar:
  assert member.isfile() and not member.name.startswith('/') and '..' not in Path(member.name).parts and member.name in items
  blob=tar.extractfile(member).read();assert len(blob)==items[member.name].stat().st_size and hashlib.sha256(blob).hexdigest()==sha(items[member.name]);count+=1
assert count==len(items)
for rec in freeze['files']:assert sha(rec['path'])==rec['sha256']
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'regular_members':len(items),'archive_payloads_verified':True,'frozen_manifest_sha256':sha(freeze_path),'original_freeze_sha256':sha(BASE/'frozen_before_predictions.json'),'source_manifest_sha256':sha(BASE/'BACKUP_SOURCE_MANIFEST.json'),'gate':report['status'],'all_failures_retained':True,'Mac_copy_verified':False,'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED','scope':'v2 exact-bound API and strict native-output gate correction; selected fixed recorded regression only, no plant/controller/timing/task acceptance.'}
save(dest/'READY.json.part',ready);(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2),flush=True)

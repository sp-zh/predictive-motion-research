#!/usr/bin/env python3
"""Regular-member immutable augmented-component evidence packet."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path('/home/codextransfer/predictive_motion');BASE=ROOT/'results/phase5/development/public-coupled-augmented-cpp-v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
freeze_path=BASE/'frozen_before_predictions.json';freeze=json.loads(freeze_path.read_text());report=json.loads((BASE/'parity-attempt1/report.json').read_text());assert report['status']=='PASS_BOUNDED_AUGMENTED_COMPONENT_ONLY' and report['freeze_sha256']==sha(freeze_path)
for rec in freeze['files']:assert sha(rec['path'])==rec['sha256'] and sha(rec['immutable_copy'])==rec['sha256']
positive=[x for x in report['records'] if x['success']];negative=[x for x in report['records'] if not x['success']];maxima={key:max(x['maxima'][key] for x in positive) for key in positive[0]['maxima']}
review=ROOT/'reviews/phase_5_public_coupled_augmented_cpp_20261007.md'
review.write_text(f'''# Isolated augmented public-coupled C++ transition

Phase5 NOT_ACCEPTED; Phase6 NOT_STARTED. This separately named wrapper links frozen C++v2 without modifying its source, public constants, raw recordings, Python baseline or model parameters. Base probe fa1a00344e73d8fe2266541ba4e2b34c362351b30a4f21dfa34c04867f585a04 is retained for independent physical composition. Private remote backup b1d5c2f034735b3955255f16c0c9b8ac86c7ca49 was verified before this unit; root preservation addendum is 260397685e83db1b39546eb8c65caca31d8a4252. Backup does not accept Phase5.

State z=(qphysical,vphysical,Caccepted,waccepted,s,r) has30 scalars, input (alpha_command,b_progress) has8. Each actual4ms cycle computes w_next=w+.004alpha and C_next=C+.004w_next, then holds C_next across two frozen-base2ms physical steps with q/v passed forward. Progress state uses pre-update r: s_next=s+.004r+.5*.004^2*b and r_next=r+.004b. Every2ms reference is evaluated from the mesh-cell origin s0+t*r0+.5*t^2*b and r0+t*b. An integer mesh cell composes actual cycles;40ms never becomes a single command update. No command velocity is inferred from physical velocity; no command acceleration is inferred from physical acceleration.

This is a bounded numerical component domain: fixed FR3 strict physical joint ranges and finite physical velocity; accepted C inside public control limits, |w|<=.0625rad/s, |alpha|<=1rad/s^2, 0<=s<=1,0<=r<=.2/s, finite signed b. Cells are unquoted canonical positive integers,<=512cells and<=5000 each/total4ms cycles; cases<=128. No remainder rounding, silent command/progress clipping or reset. Physical force clamps remain the frozen base law and are explicit diagnostics. Domain checks do not certify physical velocity/acceleration/jerk, clearance, command jerk, progress slew, stops, task accuracy or real-time execution.

All {len(positive)} positive cases and {len(negative)} expected native input/future-domain failures are explicitly accounted for. Recorded tests use TRAIN91011 starts100/500/1250/2400/2500 and previously seen91013 starts100/500/690/920/2400/2500 at1/10/200cycles. Twenty-nine complete windows use each actual future command acceleration with initial previous accepted target/velocity; four EOF windows remain incomplete. Progress in recorded tests is declared virtual progress, not measured task progress. Five synthetic cases include C!=q,w!=v,4/40/12/8ms nonuniform cells, mixed signed alpha/b, held-vs-subdivided cells, negative b and zero control.

Independent exact-rational closed forms (binary floating inputs interpreted as exact fractions) check command/progress and origin-based2ms references. A separate frozen original base native probe consumes independently derived held targets and checks every q/v point. Maximum differences: C/w {maxima['command']:.17g}, progress/time {maxima['progress']:.17g}, paired q {maxima['paired_q']:.17g}rad, paired v {maxima['paired_v']:.17g}rad/s. Conditional recorded physical differences q {maxima['physical_q']:.17g}rad, v {maxima['physical_v']:.17g}rad/s. Algebra<=2e-13, paired q<=1e-12/v<=1e-11; unchanged short recorded q1e-6/v1e-4 and long q1e-4/v1e-3 gates. These overlapping previously seen windows establish this regression scope only.

The producer output gate checks exact unique ordered roster, actual bool success/final flags, finite typed7-vectors including failed partial outputs, exact declared trace/cycle lengths, explicit error strings, held C/w per half pair, original KKT<=1e-10, typed friction labels/iterations/clips and complete-cycle/final consistency. Scoring additionally checks exact mesh order and all cycle/cell progress/end states against closed forms. One valid actual-output control passes;{len(report['synthetic_output_gates']['negative_controls'])} deliberately corrupted output controls reject. Those synthetic output mutations are not actual native failures. Two native cases complete their first4ms cycle and reject the second for command-velocity/progress-rate domain violations, retaining two2ms points and the last valid complete cycle. Parser/domain-invalid cases retain explicit errors. No failed trace is dropped or scored as a complete forecast.

First build and first QA attempt complete successfully; full logs/native outputs are retained. Source/dependency freeze {sha(freeze_path)} precedes all augmented forecasts and records{len(freeze['files'])} live/immutable identities, including old v2 source/probe, SDK/runtime/compiler dependencies, model assets/raw data and new input/harness. All2540 prior v2 identities were checked unchanged before predictions. Rechecks guard both live and immutable bytes. Two figures show actual synthetic transition telemetry and QA differences/counts with units, data/script/hash provenance. The initial verification figure had crowded category labels and was retained with its source/provenance under visual-attempt1 before a layout-only repair; both final figures were visually inspected. They are development diagnostics, not accepted task images or performance ranking. No successful complete Phase5 task trajectory is available for a new task-success video.

Only this transition component is delivered. Jacobian, main/controller integration, plant rerun, untouched evaluation seeds and later phases remain outside this unit. Source/review/figures are imported by the Mac backup owner and independently audited before private Git commit/push. The complete regular-member archive and SHA/READY manifests retain large evidence on Dell and Mac; a Git checkpoint record documents actual verified copies.
''')
items={}
def add(name,p):
 p=Path(p)
 if p.is_dir():
  for f in p.rglob('*'):
   if f.is_file() and '__pycache__' not in f.parts:items[name+'/'+str(f.relative_to(p))]=f
 else:items[name]=p
add('project/tools/phase5_public_coupled_augmented_cpp',ROOT/'tools/phase5_public_coupled_augmented_cpp');add('project/'+str(BASE.relative_to(ROOT)),BASE)
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:items.pop('project/'+str((BASE/name).relative_to(ROOT)),None)
sources=['scripts/phase5/verify_public_coupled_augmented_cpp.py','scripts/phase5/plot_public_coupled_augmented_cpp.py','scripts/phase5/publish_public_coupled_augmented_cpp.py',str(review.relative_to(ROOT))]
sources+=['figures/phase5/phase5_public_coupled_augmented_cpp_'+stem+ext for stem in ('transition','verification') for ext in ('.png','.json')]
small={}
for name in sources:add('project/'+name,ROOT/name);small[name]=dict(sha256=sha(ROOT/name),bytes=(ROOT/name).stat().st_size)
for p in list((ROOT/'tools/phase5_public_coupled_augmented_cpp').glob('*'))+[freeze_path,BASE/'parity-attempt1/report.json',BASE/'inputs/declared_scope.json',BASE/'visual_inspection.json',BASE/'prior_v2_preservation_verified.json']:
 if p.is_file():small[str(p.relative_to(ROOT))]=dict(sha256=sha(p),bytes=p.stat().st_size)
for rec in freeze['files']:add('immutable_dependencies/'+rec['sha256'],rec['immutable_copy'])
save(BASE/'CHECKPOINT_FILE_MANIFEST.json',{name:dict(sha256=sha(p),bytes=p.stat().st_size) for name,p in items.items()});save(BASE/'BACKUP_SOURCE_MANIFEST.json',small)
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:add('project/'+str((BASE/name).relative_to(ROOT)),BASE/name)
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-coupled-augmented-cpp-v1-20261007');dest.mkdir(exist_ok=False);part=dest/'public-coupled-augmented-cpp-v1.tar.gz.part'
with tarfile.open(part,'w:gz',dereference=True) as tar:
 for name,p in sorted(items.items()):tar.add(p,arcname=name,recursive=False)
archive=dest/'public-coupled-augmented-cpp-v1.tar.gz';part.rename(archive)
with tarfile.open(archive,'r|gz') as tar:
 count=0
 for m in tar:
  assert m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts and m.name in items
  blob=tar.extractfile(m).read();assert len(blob)==items[m.name].stat().st_size and hashlib.sha256(blob).hexdigest()==sha(items[m.name]);count+=1
assert count==len(items)
for rec in freeze['files']:assert sha(rec['path'])==rec['sha256']
ready=dict(archive=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,regular_members=len(items),archive_payloads_verified=True,frozen_manifest_sha256=sha(freeze_path),source_manifest_sha256=sha(BASE/'BACKUP_SOURCE_MANIFEST.json'),gate=report['status'],all_failures_retained=True,Mac_copy_verified=False,phase5='NOT_ACCEPTED',phase6='NOT_STARTED',scope='Bounded augmented state wrapper; rational algebra and paired frozen base composition, conditional seen records only. No new plant/controller/task/timing acceptance.')
save(dest/'READY.json.part',ready);(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2),flush=True)

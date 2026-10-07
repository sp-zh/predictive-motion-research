#!/usr/bin/env python3
import datetime,hashlib,importlib,json,subprocess,sys,tarfile
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/public-coupled-servo-v1-training';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();freeze=json.loads((base/'frozen.json').read_text());assert all(sha(f)==h for f,h in freeze['files'].items())
sys.path.insert(0,str(p/'scripts/phase5'));from materialize_identity import materialize
materialize(base/'frozen.json')
post_files={}
for name in ['numpy.linalg._umath_linalg','numpy.core._multiarray_umath']:
 file=Path(importlib.import_module(name).__file__);post_files[str(file)]={'sha256':sha(file),'bytes':file.stat().st_size}
 for line in subprocess.check_output(['ldd',str(file)],text=True).splitlines():
  candidate=next((Path(x) for x in line.split() if x.startswith('/') and Path(x).is_file()),None)
  if candidate:post_files[str(candidate)]={'sha256':sha(candidate),'bytes':candidate.stat().st_size}
(base/'numerical_runtime_after_run.json').write_text(json.dumps({'recorded_after_training_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Supplemental post-run NumPy/BLAS identity only. Not included in original40 pre-scan frozen files, not retroactively promoted to prefreeze closure.','files':post_files},indent=2)+'\n')
(base/'execution_record.json').write_text(json.dumps({'recorded_after_run_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'return_code':0,'command':'source /opt/ros/jazzy/setup.bash && python3 scripts/phase5/run_public_coupled_servo_training_v1.py','record_source':'Actual exec tool session67439 exit0 and immutable final report; no separate stdout/stderr file capture was made.','wall_time_claim':False,'report_sha256':sha(base/'training_report.json'),'frozen_sha256':sha(base/'frozen.json')},indent=2)+'\n')
review=p/'reviews/phase_5_public_coupled_servo_training_v1_20261007.md';review.write_text('''# Public coupled servo baseline: original training-only check

PASS_PUBLIC_COUPLED_TRAINING_ONLY. No calibration, fitting, validation-output selection, new physical run, main-MPC or derivative integration. Original scalar/model/domain failures remain unchanged. This is a public-model conditional prediction baseline at original TRAIN91011, not untouched holdout, universal exact-engine or controller/Phase5 acceptance. Candidate equations and40 source/model/binary/native-input identities were frozen before any training prediction; final hashes unchanged. Freeze SHAdaec068c50c3362a3810642d7e2c01223926e4c04fc59ed1c8bc33e32ddd2907; raw SHAab9d14efa1a5886c0683db25345f24d5cacd55343e2768eb60536fa180a11dce.

Pure Python predictor imports inspection-MJCF into Pinocchio4.1, including declared0.45kg tool and armature automatically in CRBA (never added twice). The static-reader-only C++ program uses mj_loadXML/mjModel constants and no mjData/mj_forward/mj_step. Model M/bias on subsequent forecast q/v are analytic public calculations. Actuator/control and joint-force clamp flags/ranges are read from compiled model, affine gear1 maps are checked. tau_smooth=clipped affine actuator-passive damping*v-full rigid-body bias. Friction force solves originalH=M^-1+diag(max(mjMINVAL,(1-d)/d*staticinvweight0)),ell=M^-1*tau+Bv with coupled active-face linear solves and original KKT verification. Independent clipping is only feasible initialization/line-search projection, never the final coupled solution without KKT. M+hD integration is distinct from forceQP M^-1; full affine velocity-bias derivative remains inD even when torque clamps. No ordinary derivative implementation or ordinary threshold-Jacobian claim.

Candidate assumes seven instantaneous affine joint actuators and contact/joint-limit/equality-free dynamics with no unknown/applied/fluid/spring/gravity-comp forces. It validates public mapping/types/constants, finite inputs and strict joint ranges. Recorded contact annotations are an offline regime audit, not forecast-state inputs; a contact window would remain an explicit failure rather than disappear. Unknown forces and engine termination/parser differences remain limitations. This model has no accuracy-certified box or physical/command/geometry stopping certificate.

Each4ms-aligned window uses actual past/start q_before,v_before once and conditions on recorded accepted targets; it never resets with future actual physical q/v. A2ms physical model step uses own q/v. Recorded target is held identically over two substeps. Accepted command velocity is not substituted for physical v; instantaneous position actuators here need current c, with future c supplied by the conditional recorded sequence. This is not a live future-command prediction or planner performance test.

All original active full2/4/40/800ms windows2190/2190/2181/1991 and separate500 warmup starts at every horizon complete with zero solver/regime failures. Stop rows380 are retained, plus excitation4000/warmup1000. Every horizon has190 stop-containing windows;800ms has no stop-start window because the actual stop tail is shorter than800ms. Incomplete trailing windows cannot be invented; no full stop window is deleted. Overlapping windows are not independent trials.

Active maximum q errors4.440892098500626e-16,8.881784197001252e-16,8.881784197001252e-16,8.881784197001252e-16rad; v errors9.566999970012091e-16,9.289444213855802e-16,5.747572556780156e-15,6.499317685600137e-15rad/s. Original2/4ms q1e-6/v1e-4 and40/800ms q1e-4/v1e-3 unchanged; all pass. Full maximum/RMSE/worststart/joint records and warmup metrics in training_report.json. Machine-roundoff-size errors demonstrate this recorded conditional check only, not arbitrary exact-engine equivalence.

Seven frozen root nominal box fixtures cross-check force within2.22e-16Nm, originalKKT≤7.77e-16. All prediction original forceQP KKT≤2.22e-15, maximum iterations2 (budget100); zero force/control clamps in this training trace. Repeated prediction-coordinate branch counts interior6946555/lower235017/upper225058 total7406630 (1058090physical model evaluations); these overlap and do not count distinct physical events. Saturation paths are therefore exercised; force/control clamp implementation remains not physically exercised in this trace.

Provenance limitation: NumPy version1.26.4 and single-thread setting are pre-recorded; its separate linalg extension/BLAS files were not explicitly in original40 frozen identities. Supplemental post-run hashes are kept in numerical_runtime_after_run.json, never backdated as pre-run freeze.40 listed bytes are cache-materialized/verified; do not call this a complete Python-environment freeze. No separate execution stdout/stderr capture was made; actual exec tool exit0/finalreport are recorded with this limitation and no timing claim. Neither limitation alters oldfreeze.

Inspected log-ratio figure uses final report and all active window counts, original gate1 line and training-only caption; source/data/image/units recorded. No geometry/CAD or newly executed arm motion; prior actual recorded FR3 renders and task videos provide unchanged visual context. Root owns showcase/source/private-Git backup. New development validation is pending independent root design/evidence review and a separately prefrozen unused development seed; final/evaluation seeds unused.
''')
image=base/'phase5_public_coupled_training_v1.png';(base/'visual_inspection.json').write_text(json.dumps({'image_sha256':sha(image),'status':'PASS_PRESENTATION_LAYOUT','inspected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'findings':'All4horizon counts, normalized error ratios/log scale, original gate and conditional-training scope visible; no clipping, zero-error or physical/controller certificate claim.'},indent=2)+'\n')
sources=['scripts/phase5/public_coupled_servo_v1.py','scripts/phase5/coupled_friction_box_v1.py','scripts/phase5/run_public_coupled_servo_training_v1.py','scripts/phase5/plot_public_coupled_servo_training_v1.py','scripts/phase5/publish_public_coupled_servo_training_v1.py','tools/phase5_public_servo_constants/public_servo_constants.cpp',str(review.relative_to(p))];items={'project/'+s:p/s for s in sources};cache=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/identity-cache')
for name,h in freeze['files'].items():assert sha(cache/h)==h;items['frozen-input-cache/'+h]=cache/h
for name,meta in post_files.items():items['post-run-runtime/'+meta['sha256']]=Path(name)
for f in base.rglob('*'):
 if f.is_file():items['project/'+str(f.relative_to(p))]=f
manifest={name:{'sha256':sha(f),'bytes':f.stat().st_size} for name,f in items.items()};(base/'CHECKPOINT_FILE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');small={s:manifest['project/'+s] for s in sources}
for name in ['training_report.json','window_phase_roster.json','phase5_public_coupled_training_v1.png','phase5_public_coupled_training_v1.json','visual_inspection.json','public_constants.json','protocol.json','frozen.json']:
 f=base/name;small[str(f.relative_to(p))]={'sha256':sha(f),'bytes':f.stat().st_size}
(base/'BACKUP_SOURCE_MANIFEST.json').write_text(json.dumps(small,indent=2)+'\n')
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:items['project/'+str((base/name).relative_to(p))]=base/name
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-coupled-servo-v1-training-20261007');dest.mkdir(exist_ok=False);part=dest/'public-coupled-servo-v1-training.tar.gz.part'
with tarfile.open(part,'w:gz') as t:
 for name,f in sorted(items.items()):t.add(f,arcname=name,recursive=False)
archive=dest/'public-coupled-servo-v1-training.tar.gz';part.rename(archive)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(items)
 for m in t.getmembers():assert m.isfile() and m.name in items and hashlib.sha256(t.extractfile(m).read()).hexdigest()==sha(items[m.name])
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(items),'archive_members_verified':True,'pre_recorded_input_cache_verified':len(freeze['files']),'post_run_NumPy_identity_separate':True,'mac_copy_verified':False,'source_manifest':str(base/'BACKUP_SOURCE_MANIFEST.json'),'source_manifest_sha256':sha(base/'BACKUP_SOURCE_MANIFEST.json'),'scope':'Public uncalibrated conditional TRAIN91011 allhorizonsPASS only; no exactengine/holdout/controller/Phase5 acceptance'};(dest/'READY.json.part').write_text(json.dumps(ready,indent=2)+'\n');(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2))

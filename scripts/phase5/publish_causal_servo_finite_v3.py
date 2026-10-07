#!/usr/bin/env python3
import datetime,hashlib,json,tarfile
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/causal-soft-servo-cpp-v3';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();freeze=json.loads((base/'frozen.json').read_text());assert all(sha(f)==h for f,h in freeze['files'].items())
old=json.loads((p/'results/phase5/development/causal-soft-servo-cpp-v2/frozen.json').read_text());assert all(sha(f)==h for f,h in old['files'].items())
failure=p/'results/phase5/development/causal-soft-servo-v3-build-failure';(failure/'failure.json').write_text(json.dumps({'exit_code':2,'stage':'Initial v3 overflow test consumer compilation','flags':'-Wall -Wextra -Werror','error':'causal_soft_servo_overflow_probe.cpp:13: this if clause does not guard... [-Werror=misleading-indentation]','retained_source_sha256':sha(failure/'causal_soft_servo_overflow_probe.cpp'),'fix':'Separate output statement onto its own line; keep Werror. Before freeze, denominator-overflow synthetic fixture decay also set .1 to reach denominator check rather than earlier drive overflow. No FR3 model change.'},indent=2)+'\n')
review=p/'reviews/phase_5_causal_servo_finite_v3_20261007.md';review.write_text('''# Causal scalar model v3 derived-arithmetic rejection

PASS_ISOLATED_CAUSAL_FINITE_V3, not Phase5/model/controller acceptance. Clone tools/phase5_causal_servo_v2 into separatev3; all v1/v2 source, binaries, inputs and immutable archives preserved byte for byte. Root counterexample consumer source reused unchanged. Frozen FR3 coefficients/domain and scalar soft law unchanged. No plant, fit, native QP or main MPC integration.

Public cycle/cell returns now check state,A,B,defect finite. Physical scalar drive, implicit denominator,gain,derivative/state; physical P/f; every cycle/cell A/B/defect composition; and derived target-error arithmetic reject nonfinite values immediately rather than carrying them through later matrix operations. The probe checks horizon offsets/control/initial sensitivities before propagation/serialization and checks every emitted vector/matrix. No arbitrary parameter envelope or clamp is imposed to hide overflow.

Root actual finite-parameter counterexample(mass1e-300,kp1e308,D/friction0,zero nominal force/control) still passes parameter validation but now throws before overflowing derivatives are returned. Four declared finite synthetic parameter scenarios yield7 expected cycle/cell overflow rejections: derivative overflow,gain overflow,finite one-cycle Jacobian with two-cycle A overflow,implicit denominator overflow. One finite one-cycle positive control in the composition case still returns finite output. Two separate horizon fixtures retain finite single cells but reject nonfinite control sensitivity product and initial sensitivity respectively, returning error3 with explicit reason; partial JSON outputs retained as negative-control artifacts, not valid datasets. Counts overlap across APIs and do not represent independent research trials.

Previously frozen8 root branch cases and both n1/nonuniform5cell/.2s,n7/nonuniform20cell/.8s nominal full state,A/B/defect,offset/control/initial sensitivity arrays all match prior oracle. Maximum nominal difference2.2709265024012382e-14 below unchanged5e-12 numerical comparison. All78 malformed-entry and10 initial/forecast/mesh rejections recur. Exact±clip threshold derivative remains only the declared saturation-side convention, not a unique ordinary Jacobian. All source/binary/input/reference bytes frozen before probes and verified unchanged after. No FD or independent oracle regenerated.

GNU13.3 C++17 with -Wall -Wextra -Werror builds four targets. Initial overflow-test consumer formatting failed Werror misleading-indentation; exact pre-fix source and failure record retained. Production arithmetic checks were unaffected by that formatting repair. Extreme synthetic coefficients are algebraic counterexamples, not FR3 calibrations or physical states.

One inspected count figure records actual rejection/branch regression outcomes with logarithmic count axis and scoped caption; source/data/image hashes documented. No CAD/geometry modification; the actual recorded FR3 render and verified task videos in previous checkpoints remain the applicable visual context. Scalar larger-input v3 predictor2/4ms failures and all task/physical/command/geometry/age/native policies remain unchanged. Root owns independent review/private-Git checkpoint/showcase update before proceeding to another completed work unit.
''')
image=base/'phase5_causal_servo_finite_v3.png';(base/'visual_inspection.json').write_text(json.dumps({'image_sha256':sha(image),'status':'PASS_PRESENTATION_LAYOUT','inspected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'findings':'Scoped arithmetic rejection/regression counts, log axis, labels and no-acceptance caveat legible without clipping; no model/CAD unit changes.'},indent=2)+'\n')
sources=['tools/phase5_causal_servo_v3/CMakeLists.txt','tools/phase5_causal_servo_v3/causal_soft_servo.hpp','tools/phase5_causal_servo_v3/causal_soft_servo_probe.cpp','tools/phase5_causal_servo_v3/causal_soft_servo_api_probe.cpp','tools/phase5_causal_servo_v3/causal_soft_servo_overflow_probe.cpp','tools/phase5_causal_servo_v3/root_edge_probe.cpp','scripts/phase5/prepare_causal_servo_finite_v3.py','scripts/phase5/prepare_run_causal_servo_finite_v3.py','scripts/phase5/run_causal_servo_finite_v3.py','scripts/phase5/plot_causal_servo_finite_v3.py','scripts/phase5/publish_causal_servo_finite_v3.py',str(review.relative_to(p))];items={'project/'+s:p/s for s in sources}
for directory in [base,failure]:
 for f in directory.rglob('*'):
  if f.is_file():items['project/'+str(f.relative_to(p))]=f
for f in freeze['files']:
 path=Path(f);items['project/'+str(path.relative_to(p))]=path
manifest={name:{'sha256':sha(f),'bytes':f.stat().st_size} for name,f in items.items()};(base/'CHECKPOINT_FILE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');small={s:manifest['project/'+s] for s in sources}
for name in ['report.json','phase5_causal_servo_finite_v3.png','phase5_causal_servo_finite_v3.json','visual_inspection.json']:
 f=base/name;small[str(f.relative_to(p))]={'sha256':sha(f),'bytes':f.stat().st_size}
(base/'BACKUP_SOURCE_MANIFEST.json').write_text(json.dumps(small,indent=2)+'\n')
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:items['project/'+str((base/name).relative_to(p))]=base/name
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/causal-soft-servo-cpp-v3-20261007');dest.mkdir(exist_ok=False);part=dest/'causal-soft-servo-cpp-v3.tar.gz.part'
with tarfile.open(part,'w:gz') as t:
 for name,f in sorted(items.items()):t.add(f,arcname=name,recursive=False)
archive=dest/'causal-soft-servo-cpp-v3.tar.gz';part.rename(archive)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(items)
 for m in t.getmembers():assert m.isfile() and m.name in items and hashlib.sha256(t.extractfile(m).read()).hexdigest()==sha(items[m.name])
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(items),'archive_members_verified':True,'v2_all_frozen_inputs_unchanged_verified':True,'mac_copy_verified':False,'source_manifest':str(base/'BACKUP_SOURCE_MANIFEST.json'),'source_manifest_sha256':sha(base/'BACKUP_SOURCE_MANIFEST.json'),'scope':'Isolated scalar arithmetic rejection/root counterexample and unchanged nominal regression only; no model accuracy expansion/plant/controller/Phase5 acceptance'};(dest/'READY.json.part').write_text(json.dumps(ready,indent=2)+'\n');(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2))

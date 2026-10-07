#!/usr/bin/env python3
import datetime,hashlib,json,tarfile
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/causal-soft-servo-cpp-v1';ref=p/'results/phase5/development/causal-soft-servo-cpp-reference-v1';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();frozen=json.loads((base/'frozen.json').read_text());assert all(sha(f)==h for f,h in frozen['files'].items())
ready=json.loads((ref/'READY.json').read_text());assert all(sha(ref/name)==m['sha256'] for name,m in ready['files'].items())
failure=p/'results/phase5/development/causal-soft-servo-build-failure-v1';(failure/'failure.json').write_text(json.dumps({'gate':'RETAINED_BUILD_FAILURE','exit_code':2,'binary_generated':False,'compiler':'GNU13.3.0','flags':'-Wall -Wextra -Werror','errors':[{'file':'causal_soft_servo.hpp','line':75,'error':'this if clause does not guard... [-Werror=misleading-indentation]','cause':'model.domain(initial) shared line after if throw'},{'file':'causal_soft_servo_probe.cpp','line':18,'error':'this if clause does not guard... [-Werror=misleading-indentation]','cause':'auto m=model... shared line after if output comma'}],'fix':'Separate statements onto separate lines; no mathematics, guard or compiler flag relaxation. Exact pre-fix sources retained.'},indent=2)+'\n')
review=p/'reviews/phase_5_causal_soft_servo_cpp_parity_20261007.md'
review.write_text('''# Isolated causal soft-servo C++ module

PASS_ISOLATED_CAUSAL_SOFT_CPP_PARITY only; Phase5 unaccepted and main MPC unchanged. Root-independent oracle SHA363d077546c92fb0eed6d43e0cd4826a9d322628a5cd7c7b1d2f67e03bf5ebab/sourcec63f524d2002323ca635574addcf8ef04a498154ea171ac5a58deda088853710/model984ee85d086aeba7da8260a20b21b301e23dfd2c698a6c61ace0ff956bbec1bb consumed directly, without refitting or regenerating an oracle. All six original reference packet files preserved and READY-verified.

State=[physical q/v,accepted c/w,progress s/r], input=[command alpha,progress b]. Each4ms updates w+=delta alpha,c+=delta w_next; holds c across two2ms physical empirical soft-friction model steps; progress uses s+=delta r_old+.5delta²b,r+=delta b. Every initial and pre/post physical forecast state checks original frozen q/v/target-error and progress s∈[0,1],r∈[0,.2]. Only positive integer4ms mesh supported. Model is surrogate diagonal mass/bias and soft box friction, not real robot inertial/gravity identity. No future real-plant state or mj_step used.

n1 synthetic5 nonuniform cells/.2s/50cycles/100physical model steps and n7 original frozen parameters20 nonuniform cells/.8s/200cycles/400physical model steps match all saved root states, every cycle state/branch/clock, cellA/B/defects and condensed control/initial-state sensitivities. Maximum numerical difference2.2709265024012382e-14 (n7 offsets), below prefrozen5e-12 implementation threshold. Model-state differences≤6.776263578034403e-21; clock exactly equal. C++ source/binary/input/reference freeze precedes execution; hashes unchanged.

10 negative controls reject initial q,v,target-error,progress speed/position; future target-error/progress-speed; and undefined mesh .041,0,-.004. This packet's nominal branch coverage and zero clip equalities are explicit in report; no claim of complete C++ saturation/threshold derivative tests. Root may supply full frozen branch fixture outputs for further independent comparisons. Equality uses saturated one-sided branch convention and cannot be treated as a unique ordinary Jacobian.

The module implements causal dynamics/local branch Jacobians and integer-period cell composition. It does not enforce original physical/command hard limits, finite-jerk command speed cone, native SOLVED/SI rows, nonlinear geometry/command/stop guards, task cost, lifted-state elimination or real-time deadlines. These remain required independent integration work, not hidden acceptance by this model-only test. Passing declared domain does not establish model accuracy under arbitrary commands.

GNU13.3 C++17 build uses Eigen3/yaml-cpp with -Wall -Wextra -Werror. Initial compilation failed on two misleading-indentation diagnostics; exact original source and failure record retained; formatting-only fix compiled successfully without relaxing flags. No other prior source/binary/guard altered.

One inspected plot displays model-only n7 q/c in microradians relative to initial q and progress s against root frozen reference. Twenty cell boundaries reflect nonuniform integer4ms periods. All model/source/data/image hashes recorded. No CAD or geometry modification; existing actual recorded-state render from prior checkpoint remains applicable. Root independent review required before controller integration.
''')
image=base/'phase5_causal_soft_servo_cpp_parity.png';(base/'visual_inspection.json').write_text(json.dumps({'image_sha256':sha(image),'status':'PASS_PRESENTATION_LAYOUT','inspected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'findings':'Model-only scope, q/c distinction, progress and mesh markers legible with no clipping; microradian/s/dimensionless units visible; no CAD change.'},indent=2)+'\n')
sources=['tools/phase5_causal_servo/causal_soft_servo.hpp','tools/phase5_causal_servo/causal_soft_servo_probe.cpp','tools/phase5_causal_servo/CMakeLists.txt','scripts/phase5/run_causal_soft_servo_parity.py','scripts/phase5/plot_causal_soft_servo_parity.py','scripts/phase5/publish_causal_soft_servo_parity.py',str(review.relative_to(p))];items={'project/'+s:p/s for s in sources}
for directory in [base,ref,failure]:
 for f in directory.rglob('*'):
  if f.is_file():items['project/'+str(f.relative_to(p))]=f
for f in frozen['files']:
 path=Path(f);items['project/'+str(path.relative_to(p))]=path
manifest={name:{'sha256':sha(f),'bytes':f.stat().st_size} for name,f in items.items()};(base/'CHECKPOINT_FILE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
small={s:manifest['project/'+s] for s in sources}
for name in ['report.json','phase5_causal_soft_servo_cpp_parity.png','phase5_causal_soft_servo_cpp_parity.json','visual_inspection.json']:
 f=base/name;small[str(f.relative_to(p))]={'sha256':sha(f),'bytes':f.stat().st_size}
(base/'BACKUP_SOURCE_MANIFEST.json').write_text(json.dumps(small,indent=2)+'\n')
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:items['project/'+str((base/name).relative_to(p))]=base/name
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/causal-soft-servo-cpp-v1-20261007');dest.mkdir(exist_ok=False);part=dest/'causal-soft-servo-cpp-v1.tar.gz.part'
with tarfile.open(part,'w:gz') as t:
 for name,f in sorted(items.items()):t.add(f,arcname=name,recursive=False)
archive=dest/'causal-soft-servo-cpp-v1.tar.gz';part.rename(archive)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(items)
 for m in t.getmembers():assert m.isfile() and m.name in items and hashlib.sha256(t.extractfile(m).read()).hexdigest()==sha(items[m.name])
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(items),'archive_members_verified':True,'root_reference_READY_all_five_payloads_verified':True,'mac_copy_verified':False,'source_manifest':str(base/'BACKUP_SOURCE_MANIFEST.json'),'source_manifest_sha256':sha(base/'BACKUP_SOURCE_MANIFEST.json'),'scope':'Isolated causal local model/Jacobian/mesh sensitivities parity only; original domains; main MPC untouched; no native QP/physical trial/controller/Phase5 acceptance'}
(dest/'READY.json.part').write_text(json.dumps(ready,indent=2)+'\n');(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2))

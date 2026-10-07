#!/usr/bin/env python3
import datetime,hashlib,json,tarfile
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/signed-command-cone-cpp-v1';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();frozen=json.loads((base/'frozen.json').read_text());assert all(sha(f)==h for f,h in frozen['files'].items())
review=p/'reviews/phase_5_signed_command_cone_cpp_parity_20261007.md'
review.write_text('''# Isolated C++ signed command cone implementation parity

PASS_ISOLATED_CPP_SPEED_CONE only. C++17 pure scalar interval and linear row module built with GNU13.3, -Wall -Wextra -Werror; no third-party/real-plant dependency. No main MPC, native QP solve, fixture or physical run. Model984ee coefficients/thresholds and all prior source evidence untouched.

2040 cases:33 retained v1 histories tick760–792,7 hand-selected boundaries/out-of-bounds/counterexamples,2000 deterministic random cases with three signed speed/acceleration/jerk/timestep profiles.42466? Exact count is42666 candidate rows, all logged. Frozen before probe: C++ source/binary/compiler cache, runner, inputs, expected outputs and already independently tested Python mathematical contract. All hashes unchanged after test. Interval/stop maximum difference2.220446049250313e-16; linear row bound maximum difference1.7763568394002505e-15; implementation parity tolerance5e-14. Zero feasibility disagreements.

Header uses long double for recovery calculations, original64double-epsilon interior margin, and inward double conversion for acceleration intervals. For invalid/out-of-bound history no command is returned. This parity test covers finite cases and strict hard-bound rejection; it is not a comprehensive extreme-number C++ validation. The mathematical review/independent extremal sequence tests are in the preceding backed unit. QP velocity rows do not replace original direct command derivative SI rows, native SOLVED-only or physical/position/geometry guards. No joint future geometric stopping guarantee follows from speed continuation.

Single plot derives from report.json and records raw numerical implementation differences in native SI units (acceleration interval rad/s²; stop update rad/s or rad/s²; velocity rows rad/s). The common5e-14 numerical threshold only measures implementation agreement and is not a physical accuracy requirement. No CAD or model geometry changes; previous actual recorded-state render remains applicable. Independent root review required before fixture or controller integration; Phase5 remains unaccepted.
'''.replace('42466? Exact count is42666','42666'))
image=base/'phase5_signed_cone_cpp_parity.png';(base/'visual_inspection.json').write_text(json.dumps({'image_sha256':sha(image),'status':'PASS_PRESENTATION_LAYOUT','inspected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'findings':'All three numerical differences and tolerance legible; explicit isolated parity scope; native-unit definitions in accompanying metadata/review; no clipping or CAD change.'},indent=2)+'\n')
sources=['tools/phase5_command_cone/signed_velocity_cone.hpp','tools/phase5_command_cone/signed_velocity_cone_probe.cpp','tools/phase5_command_cone/CMakeLists.txt','scripts/phase5/run_signed_cone_cpp_parity.py','scripts/phase5/plot_signed_cone_cpp_parity.py','scripts/phase5/publish_signed_cone_cpp_parity.py',str(review.relative_to(p))];items={'project/'+s:p/s for s in sources}
for f in base.rglob('*'):
 if f.is_file():items['project/'+str(f.relative_to(p))]=f
for f in frozen['files']:
 path=Path(f)
 if f.startswith(str(p)):items['project/'+str(path.relative_to(p))]=path
 else:items['raw/retained-v1/raw.csv']=path
manifest={name:{'sha256':sha(f),'bytes':f.stat().st_size} for name,f in items.items()};(base/'CHECKPOINT_FILE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
small={s:manifest['project/'+s] for s in sources}
for name in ['report.json','phase5_signed_cone_cpp_parity.png','phase5_signed_cone_cpp_parity.json','visual_inspection.json']:
 f=base/name;small[str(f.relative_to(p))]={'sha256':sha(f),'bytes':f.stat().st_size}
(base/'BACKUP_SOURCE_MANIFEST.json').write_text(json.dumps(small,indent=2)+'\n')
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:items['project/'+str((base/name).relative_to(p))]=base/name
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/signed-command-cone-cpp-v1-20261007');dest.mkdir(exist_ok=False);part=dest/'signed-command-cone-cpp-v1.tar.gz.part'
with tarfile.open(part,'w:gz') as t:
 for name,f in sorted(items.items()):t.add(f,arcname=name,recursive=False)
archive=dest/'signed-command-cone-cpp-v1.tar.gz';part.rename(archive)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(items)
 for m in t.getmembers():assert m.isfile() and m.name in items and hashlib.sha256(t.extractfile(m).read()).hexdigest()==sha(items[m.name])
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(items),'archive_members_verified':True,'mac_copy_verified':False,'source_manifest':str(base/'BACKUP_SOURCE_MANIFEST.json'),'source_manifest_sha256':sha(base/'BACKUP_SOURCE_MANIFEST.json'),'scope':'Isolated C++ speed continuation parity only; main MPC unchanged; no native QP/plant/position/geometry future stop or Phase5 acceptance'}
(dest/'READY.json.part').write_text(json.dumps(ready,indent=2)+'\n');(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2))

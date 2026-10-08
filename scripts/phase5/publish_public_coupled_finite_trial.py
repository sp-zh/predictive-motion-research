#!/usr/bin/env python3
"""Immutable finite sampled-trial evidence and small source handoff."""
import json,hashlib,tarfile,collections
from pathlib import Path
ROOT=Path('/home/codextransfer/predictive_motion');BASE=ROOT/'results/phase5/development/public-coupled-finite-trial-cpp-v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
assert (BASE/'visual_inspection.json').is_file(),'visual inspection must precede publisher snapshot'
fp=BASE/'frozen_before_predictions.json';freeze=json.loads(fp.read_text());report=json.loads((BASE/'parity-attempt1/report.json').read_text())
assert report['status']=='PASS_FIXED_FINITE_SAMPLED_TRIAL_DIAGNOSTICS_ONLY' and report['freeze_sha256']==sha(fp)
for r in freeze['files']:assert sha(r['path'])==r['sha256'] and sha(r['immutable_copy'])==r['sha256']
counts=dict(collections.Counter(x['outcome'] for x in report['records']))
review=ROOT/'reviews/phase_5_public_coupled_finite_trial_20261008.md'
review.write_text(f'''# Finite candidate diagnostics and global affine residuals

Phase5 remains NOT_ACCEPTED; Phase6 is NOT_STARTED. This bounded development
unit follows remotely verified checkpoint
a48f7773bdd01894c65723c205744089c8e249a4. A separate namespace, library and CLI
compare original closed-model nominal and trial predictions. Original f1
extension, e2c physical derivatives, 2fa augmented values, fa1 physical values,
model constants, SDK and accepted Phase4 evidence remain unchanged. No fresh
plant, untouched seed, fitting, controller, cost or horizon planner is added.

Both nonlinear rollouts independently propagate their own q/v at every actual
2 ms step. Original values, errors, valid initial/last complete-cycle states,
actual half steps and failed prefixes are preserved exactly. No nominal-state
teacher forcing, projection, epsilon shift or fake future point is introduced.
Mesh comparison is topology equality: the same parsed cell count and exact
cycles in each cell. Positivity, caps and domain validity belong to the
unchanged original forward model. Equal zero/empty topology still fails its
original forward checks. Equal total duration with different per-cell cycles
or cell counts is a mismatch, never resampled into a matched trajectory.

Every actually produced step uses original e2c at its own physical INPUT:
q_before, v_before and the actual held C. The API retains exact per-joint
control, actuator-force and joint-force enabled/side metadata, plus every
friction side. Aggregate clip counts are insufficient. Original strict support
and finite/SPD/condition/KKT policies remain unchanged, including strict C.
Physical/C boundary refusal is an API support limitation, not a proof that
the composite is mathematically nondifferentiable.

Each paired actual timestamp exposes strict-support and full-signature
comparison flags. Outcomes preserve separate forward failure, mismatch,
unsupported point, changed sampled branch and unchanged strict sampled
branches. Full unchanged status requires complete original forwards, supported
nominal extension maps and all matched physical points strictly supported.
Prefix agreement never becomes a full status. An infrastructure error has a
separate diagnostic_error outcome and is not accepted by the numerical harness.

Policy, cases, inspections, comparisons and residuals explicitly set seven
claims false: connecting segment, perturbation ball, admissibility, execution,
safety, uniform error bound and controller readiness. Agreement of sampled
endpoint signatures does not prove the connecting segment or a finite ball.
This diagnostic neither approves an actual command nor applies a controller
fallback. Earlier independent two-epsilon FD gate FAIL remains immutable.

Residuals use the required GLOBAL first-order nominal cell chain. Initially,
delta_z equals trial initial minus nominal initial. For each cell,
delta_z_next = A_cell * delta_z + B_cell * delta_u_cell.
Every half/cycle/cell prediction uses its literal nonlinear nominal endpoint
plus A_cell_prefix * delta_z and B_cell_prefix * delta_u_cell. The deviation
origin is propagated through nominal cell maps, never reset to the actual
trial cell origin. Each cell has its own eight input deviations; inputs are
not silently tied across cells. Original matched origins/defects remain in
the nominal map package. Residual is actual trial minus this global prediction.

There is no residual-smallness gate, uniform error envelope or automatic
execution permission. Block values have q/C in rad, v/w in rad/s, s
dimensionless and r in 1/s. Only available actual trial endpoints with
certified nominal maps are emitted. Before packing deviations or computing
du, the implementation returns if either required prefix is empty and stops
before any cell without both prefixes. Invalid initials or absent future
control cells therefore cannot generate an invented affine error or residual.

Root reviewed the static contract and core global chain before predictions.
Its requested prefix guards and topology/validity clarification were applied
before freezing, with earlier source drafts retained. A null-node serializer
hazard was fixed statically by passing the false-claim YAML node by reference.
One client command-template interpolation failure occurred before any nested
tool execution and is recorded. Configure, build, deterministic preparation
and the first EMPTY native metadata call all exited zero. The unadapted old
v2 metadata checker then required its unused box_cases roster; this
nonnumerical failure and raw output/source/logs are retained. A separate
read-only adapter supplied an empty unused box roster to the unchanged
checker and passed. It made no repeated native call and changed no predictor,
input, physical policy or numeric comparison gate.

Freeze {sha(fp)} contains {len(freeze['files'])} live/immutable identities:
all inherited dependencies, new numerical source and harness, compiler/CMake
identities and flags, runtime/header dependencies, exact prepared inputs and
the independent root's prospectively fixed 13-pair declaration. New native
identity is {report['binary_sha256']}. No nonempty diagnostic preceded freeze.
The original model sources and binaries remain held.

The producer predeclared {report['fixed_cases']} finite pairs. Known q[1]+epsilon and
C[1]-epsilon probes at epsilon1e-6 and3e-7 are explicitly already-seen
counterexamples/diagnostics, not fresh seeds or holdout evidence. Other cases
include 0/0 startup plus/minus s/r/b controls, independent nonuniform state and
per-cell input perturbations on [1,3,2,4], unsupported physical/C points,
original future progress/command failures, invalid dimensions/nonfinite
initials, invalid later controls and zero/empty topology. Original2fa
prevalidates ALL alpha/b cells before its first physical half; malformed later
controls retain zero actual points rather than a fabricated prefix.

The first frozen numerical attempt passed diagnostic verification with no
numeric source/input/parameter/margin/epsilon/gate repair or repeated attempt.
Exact reference checks include {report['original_closed_rollouts']} original2fa
closed nominal/trial rollouts, {report['original_nominal_extension_rollouts']} original f1
nominal map rollouts and {report['original_physical_diagnostics']} original e2c
diagnostics at every actual own physical input. Every original value/map,
strict support, per-axis signature, timestamp, prefix and classification is
checked. Independent NumPy reconstruction checks GLOBAL residual arithmetic
at all available half/cycle/cell endpoints using fixed 2e-13 arithmetic
tolerance. This checks implementation arithmetic, not prediction-error quality.

Producer outcome counts are {json.dumps(counts)}.
Known1e-6 probes are correctly marked sampled_branch_changed;3e-7 diagnostics
are unchanged. The old FD failure is never relabeled. One actual-output
control passes; {len(report['synthetic_output_controls']['negative'])} modified-output controls are
rejected, including a consistent actual-origin-reset prediction falsely
labeled GLOBAL, incorrect per-axis types/sides, false safety claims, fabricated
future points, equal-duration mesh equality and nonfinite residuals.

Root independently fixed 13 pairs before finite predictor calls, including
combined small q/C changes, distinct finite state/controls, same-duration
mismatch and equal aggregate force-clip counts with different signed faces.
Its independent numerical verdict is pending at this producer packet's
publication and must be recorded separately by the Mac backup owner. This
producer pass does not substitute for root review or a Phase5 gate.

Three actual-output figures show all outcome counts and declared prefix
categories, six SI residual blocks on the prospectively selected finite
nonuniform case, and lower/free friction labels for the known original-step
controls. C/w/s/r rounding-scale residuals are arithmetic, not controller
precision claims. Figure selection, source/data/native/freeze hashes and
visual inspection are recorded. All three were viewed on Mac before snapshot.
They depict predictor diagnostics, not physical execution or task success.
No complete successful accepted Phase5 task trajectory exists for a new task
video; accepted Phase4 CAD and curated task clips remain preserved.

Small numerical source/configuration/harness/review/figures are handed to the
Mac backup owner. Large raw results, SDK dependencies, retained failed
preflights and all original failed-domain cases remain in immutable SHA/READY
archives verified on Dell and subsequently Mac. Remote private Git checkpoint
verification and independent root review must finish before any next unit.
Backup completion never accepts a failed research gate or Phase5.
''')
items={}
def add(name,p):
 p=Path(p)
 if p.is_dir():
  for f in p.rglob('*'):
   if f.is_file() and '__pycache__' not in f.parts:items[name+'/'+str(f.relative_to(p))]=f
 else:items[name]=p
add('project/tools/phase5_public_coupled_finite_trial_cpp',ROOT/'tools/phase5_public_coupled_finite_trial_cpp')
add('project/'+str(BASE.relative_to(ROOT)),BASE)
for n in ('CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json'):items.pop('project/'+str((BASE/n).relative_to(ROOT)),None)
sources=['scripts/phase5/'+s+'.py' for s in ('prepare_public_coupled_finite_trial','verify_public_coupled_finite_trial','plot_public_coupled_finite_trial','publish_public_coupled_finite_trial')]+[str(review.relative_to(ROOT))]
sources+=['figures/phase5/phase5_public_coupled_finite_trial_'+stem+ext for stem in ('outcomes','global_residuals','known_branches') for ext in ('.png','.json')]
small={}
for name in sources:add('project/'+name,ROOT/name);small[name]=dict(sha256=sha(ROOT/name),bytes=(ROOT/name).stat().st_size)
for p in list((ROOT/'tools/phase5_public_coupled_finite_trial_cpp').glob('*'))+[fp,BASE/'parity-attempt1/report.json',BASE/'inputs/declared_scope.json',BASE/'contract_before_predictions.json',BASE/'visual_inspection.json',BASE/'finite_trial_preflight_failure1.json',BASE/'metadata_preflight2.json']:
 if p.is_file():small[str(p.relative_to(ROOT))]=dict(sha256=sha(p),bytes=p.stat().st_size)
for r in freeze['files']:add('immutable_dependencies/'+r['sha256'],r['immutable_copy'])
save(BASE/'CHECKPOINT_FILE_MANIFEST.json',{name:dict(sha256=sha(p),bytes=p.stat().st_size) for name,p in items.items()})
save(BASE/'BACKUP_SOURCE_MANIFEST.json',small)
for n in ('CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json'):add('project/'+str((BASE/n).relative_to(ROOT)),BASE/n)
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-coupled-finite-trial-cpp-v1-20261008');dest.mkdir(exist_ok=False)
part=dest/'public-coupled-finite-trial-cpp-v1.tar.gz.part'
with tarfile.open(part,'w:gz',dereference=True) as tar:
 for name,p in sorted(items.items()):tar.add(p,arcname=name,recursive=False)
archive=dest/'public-coupled-finite-trial-cpp-v1.tar.gz';part.rename(archive)
with tarfile.open(archive,'r|gz') as tar:
 count=0
 for m in tar:
  assert m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts and m.name in items
  blob=tar.extractfile(m).read();assert len(blob)==items[m.name].stat().st_size and hashlib.sha256(blob).hexdigest()==sha(items[m.name]);count+=1
assert count==len(items)
for r in freeze['files']:assert sha(r['path'])==r['sha256']
ready=dict(archive=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,regular_members=len(items),archive_payloads_verified=True,frozen_manifest_sha256=sha(fp),source_manifest_sha256=sha(BASE/'BACKUP_SOURCE_MANIFEST.json'),gate=report['status'],independent_root_finite_gate='PENDING_AT_PRODUCER_PUBLICATION',earlier_independent_root_FD_gate='FAIL_RETAINED_IMMUTABLE',all_failures_retained=True,Mac_copy_verified=False,phase5='NOT_ACCEPTED',phase6='NOT_STARTED',small_source_items=len(small),scope='Finite original closed-model self-rollouts, sampled per-axis branch diagnostics and GLOBAL affine arithmetic only; no segment/ball/admissibility/execution/safety/uniform error bound/main/task/timing acceptance.')
save(dest/'READY.json.part',ready);(dest/'READY.json.part').rename(dest/'READY.json')
print(json.dumps(ready,indent=2),flush=True)

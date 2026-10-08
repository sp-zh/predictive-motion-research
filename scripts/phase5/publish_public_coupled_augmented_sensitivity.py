#!/usr/bin/env python3
"""Archive bounded cell sensitivities with full frozen dependencies and failures."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path('/home/codextransfer/predictive_motion');BASE=ROOT/'results/phase5/development/public-coupled-augmented-sensitivity-cpp-v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
assert (BASE/'visual_inspection.json').is_file(), 'visual inspection record required before archive snapshot'
freeze_path=BASE/'frozen_before_predictions.json';freeze=json.loads(freeze_path.read_text());report=json.loads((BASE/'parity-attempt1/report.json').read_text());assert report['status']=='PASS_BOUNDED_AUGMENTED_CYCLE_CELL_SENSITIVITIES_ONLY' and report['freeze_sha256']==sha(freeze_path)
for r in freeze['files']:assert sha(r['path'])==r['sha256'] and sha(r['immutable_copy'])==r['sha256']
positive=[x for x in report['records'] if x['sensitivity_success']];value_only=[x for x in report['records'] if x['value_success'] and not x['sensitivity_success']];failed=[x for x in report['records'] if not x['value_success']]
stats=[dict(epsilon=e,max_absolute=max(x['epsilons'][i]['max_absolute'] for x in positive),max_gate_ratio=max(x['epsilons'][i]['max_gate_ratio'] for x in positive)) for i,e in enumerate(report['epsilons'])]
review=ROOT/'reviews/phase_5_public_coupled_augmented_sensitivity_20261007.md'
review.write_text(f'''# Bounded augmented cycle and held-cell sensitivities

Phase5 NOT_ACCEPTED; Phase6 NOT_STARTED. Mac/private remote master 1df837310697ae7f129b74dd3b42c97eb1d15ce7 was independently verified before this unit. This new isolated wrapper links the frozen augmented value and physical analytic derivative models. Their independently checked original reference binaries are 2fa952127cdd37ceb56396231e2972d50d36c94e9a19c341c9c17169442acf57 and e2c75c09001ba354ca5371cbfc594a9765c62098d4cdb52e6a1442adc055c6a4. Original fa1 physical base, v2 solver, augmented/physical derivative sources, constants, raw seen records, SDK and binaries remain frozen. There is no engine pointer, mjData, fitting, new plant, untouched seed, global horizon condensation/cost/planner/main controller or task/timing acceptance. External global matrix composition below exists only in QA to validate chained cell output.

z=(q7,v7,C7,w7,s,r), u=(alpha7,b), 4ms cycles and two2ms physical halves. w_next=w+h*alpha, C_next=C+h*(w+h*alpha), with C_next/w_next already latched at both halves; q/v self-propagate through two original physical steps. s_next=s+h*r+.5*h^2*b and r_next=r+h*b. Reference progress at each half is evaluated from the original cell origin polynomial. Nominal values are always the exact frozen augmented rollout. The wrapper never applies its affine model to reset nominal state.

At the actual first-half input, J1=(P1,Q1) is14x21. J2 is evaluated at the actual first-half q/v and same held command. P=P2*P1 and Q=P2*Q1+Q2. For a full cycle, physical A blocks are(P,Q,hQ) for(q/v,C,w), B_alpha=h^2Q. C rows contain identity and hI, with B_alpha=h^2I; w rows contain identity with B_alpha=hI. Progress A=[[1,h],[0,1]], B_b=[.5h^2,h]. The first-half map uses J1 and progress time2ms, while command updates still use the full4ms latch. Half2 uses composed J2/J1 and progress4ms. A halfstep endpoint is explicitly a diagnostic map, not a valid ordinary4ms initialization.

For m cycles with fixed input in a cell, cell_A <- A_cycle*cell_A, cell_B <- A_cycle*cell_B+B_cycle, initialized to identity/zero at each actual cell origin. Every local and cell defect is exact nonlinear endpoint−A*matched_origin−B*held_input. Cycle maps carry local and cumulative cell blocks; cell maps expose only their final cumulative blocks. All products/sums and every affine-defect intermediate must be finite. First uncertified halfstep stops derivative output. Only completed certified prefix maps are retained; later/end-of-cell matrices are never fabricated, zero-filled or stale. Original valid forward output, completed halfsteps/cycles/cells and partial-failure final state remain available regardless of derivative certification.

Conservative central-domain policy requires1e-8SI interior distance for initial/generated C,w,s,r and alpha, additionally to inherited physical strict clamp/friction margins, finite intermediates and M/H/Hff/K SPD/condition/residual gates. b is finite only. This policy deliberately does not certify common actual task starts s=0 or r=0, terminal progress, command/input boundaries, or weak physical layers. Those valid values are retained without derivative certification. Unsupported is a component API support restriction, not proof of nondifferentiability of the composite map or a safety/performance failure. Progress polynomials have analytic derivatives at boundaries, but a separate boundary/canonical-extension or feasible-direction policy must be declared and independently validated before main-startup use. No actual progress/history was shifted to epsilon, no startup-ready claim is made, and numerical margins do not establish an accuracy domain or feasible perturbation radius.

Predeclared29 cases:6 supported fixtures (prospective all-free single cycle, held10, equal split[1,3,2,4], distinct-control nonuniform[1,3,2,4], strong joint-force saturation, and previously seen seed91013 tick690 using actual prior accepted C/w and current alpha);12 value-valid but unsupported cases;10 invalid initial/parser/arithmetic cases;1 future second-cycle w failure with two retained physical halves/one cycle and no full-cell matrix. Virtual s=.2,r=.08 is declared synthetic progress and is not recorded plant progress. The seen seed is not an untouched evaluation or new physical run. Weak friction and force threshold fixtures are copied from the previously frozen physical derivative case roster. Other fixtures cover initial/terminal progress, initial/generated w boundaries, exact alpha, generated progress half-prefix and later-cell boundary refusal.

One numerical attempt passed without model, input, parameter, epsilon, support margin or gate changes. All29 complete nominal results including invalid/parser/partial-forward failures equal the original augmented probe exactly. Original e2c performs{report['independent_nominal_physical_derivatives']} independent nominal J1/J2 calls. Matrices, tiny h^2Q and hQ coefficients, rational command/progress coefficients, everyhalf semiimplicit q sensitivities, matched defects and held/split equality are separately checked with2e-13 structural tolerance (1e-12 for held/split product accumulation).

Original augmented2fa performs{report['fd_augmented_cases']} predeclared finite-difference calls in cap96 batches (original CLI cap128). Each of6 supported cases includes a nominal plus all30 state+8 common held-input directions, both signs, both fixed epsilon1e-6 and3e-7. For multiple cells, input perturbations apply equally to each cell; the independent Mac/root auditor separately checks each distinct cell control coordinate. QA externally composes cell maps and tests every2ms half, complete cycle and cell endpoint. Every entry must satisfy |error|<=5e-7+5e-6|analytic| separately for both epsilon values, without choosing a favorable step.

Original fa1 performs{report['fd_original_physical_diagnostics']} independent physical diagnostics at every nominal/perturbed2ms point, using original actual preceding q/v and latched C. Exact q/v/friction parity is required. Every perturbation retains the same strict nested clamp and exact friction labels/margins as its nominal, satisfies the initial/generated command/progress/input domain, and has positive finite-condition<=1e12 M,K,H,Hff when free. K includes full implicit D even under force saturation. Diagnostic comparison inputs are mechanically derived by the frozen harness from the original frozen forward output; SHA manifests are written before their diagnostic calls. No diagnostic output fits parameters or selects a trajectory.

Observed selected component errors (mixed derivative units; gate ratios dimensionless):
{json.dumps(stats,indent=2)}

Strict roster/type/finite/shape/value checks pass one actual-output positive control and reject{len(report['synthetic_output_gates']['negative_controls'])} deliberate modified-output controls. These include fabricated unsupported matrices, shortened/reordered/duplicated rosters, wrong typed flags/indices/policy, ragged or nonfinite matrices/defects, invalid state dimensions and missing error. Synthetic corruptions are not actual native failures.

First isolated CMake configure/build succeeds. Before predictions, static review completed parser-failure canonical original-value output; first successful source/binary are preserved in build-attempt1/source-at-success and probe-before-parser-value-completion. Only CLI parser output completion changed; build-attempt2 succeeds. Empty-roster metadata preflight passes frozen native helper70b. Full freeze{sha(freeze_path)} contains{len(freeze['files'])} verified live/immutable identities, including prior2590 identities. A premature verify invocation while freeze creation was still in progress stopped at missing-freeze guard before any numerical call; raw stdout/stderr/exit remain under verification-prefreeze-invocation. No source/input/numeric repair followed that invocation. All actual predictions began after the complete freeze and hashes. An inline visual-record syntax typo failed before execution and was repaired with a saved record script/failure record. Archive-attempt1 correctly verified numerical/source payloads but took its file snapshot before the visual-inspection record existed; that incomplete publication attempt, exact publisher/review/manifests/logs and immutable59,155,029-byte archive SHA2fb772b5849c3f4efa842bb26cb8c1efb8ce034fd238de1225067f0091d95565 are retained. The final publisher requires the inspection record before its snapshot and embeds the untouched preliminary archive/READY in its regular-member evidence packet. No numerical/source/inputs/gates changed. Every failure/incomplete attempt is preserved.

Two data-backed figures show actual last-cell A/B blocks and both fixed-epsilon gates/support roster with explicit mixed block units, source/input/report/native/freeze hashes and visual inspection. Initial verification legend overlapped the gate annotation and a case label crowded the footer; original figure pair/source/provenance/logs are retained under visual-attempt1. Only layout and the accurate forward-failed roster label were repaired, without numerical changes. They are development diagnostics, not accepted arm-task/controller results. No successful complete new Phase5 task trajectory exists for a task-success video; existing accepted Phase4 CAD and curated task clips remain intact. Small source/config/QA/reviews/figures and checkpoint manifests are imported by the Mac backup owner; large original inputs/dependencies/all attempts stay in verified regular-member SHA/READY Dell+Mac archives. Independent audit, full closure verification and private remote checkpoint are required before any next unit. Backup does not accept Phase5.
''')
items={}
def add(name,p):
 p=Path(p)
 if p.is_dir():
  for f in p.rglob('*'):
   if f.is_file() and '__pycache__' not in f.parts:items[name+'/'+str(f.relative_to(p))]=f
 else:items[name]=p
prior_archive=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-coupled-augmented-sensitivity-cpp-v1-20261007-attempt1')
assert sha(prior_archive/'public-coupled-augmented-sensitivity-cpp-v1.tar.gz')=='2fb772b5849c3f4efa842bb26cb8c1efb8ce034fd238de1225067f0091d95565'
add('retained_preliminary_archive',prior_archive)
add('project/tools/phase5_public_coupled_augmented_sensitivity_cpp',ROOT/'tools/phase5_public_coupled_augmented_sensitivity_cpp');add('project/'+str(BASE.relative_to(ROOT)),BASE)
for n in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:items.pop('project/'+str((BASE/n).relative_to(ROOT)),None)
sources=['scripts/phase5/verify_public_coupled_augmented_sensitivity.py','scripts/phase5/plot_public_coupled_augmented_sensitivity.py','scripts/phase5/publish_public_coupled_augmented_sensitivity.py',str(review.relative_to(ROOT))]
sources+=['figures/phase5/phase5_public_coupled_augmented_sensitivity_'+stem+ext for stem in ('matrix','verification') for ext in ('.png','.json')]
small={}
for name in sources:add('project/'+name,ROOT/name);small[name]=dict(sha256=sha(ROOT/name),bytes=(ROOT/name).stat().st_size)
for p in list((ROOT/'tools/phase5_public_coupled_augmented_sensitivity_cpp').glob('*'))+[freeze_path,BASE/'parity-attempt1/report.json',BASE/'inputs/declared_scope.json',BASE/'visual_inspection.json']:
 if p.is_file():small[str(p.relative_to(ROOT))]=dict(sha256=sha(p),bytes=p.stat().st_size)
for r in freeze['files']:add('immutable_dependencies/'+r['sha256'],r['immutable_copy'])
save(BASE/'CHECKPOINT_FILE_MANIFEST.json',{name:dict(sha256=sha(p),bytes=p.stat().st_size) for name,p in items.items()});save(BASE/'BACKUP_SOURCE_MANIFEST.json',small)
for n in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:add('project/'+str((BASE/n).relative_to(ROOT)),BASE/n)
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-coupled-augmented-sensitivity-cpp-v1-20261007');dest.mkdir(exist_ok=False);part=dest/'public-coupled-augmented-sensitivity-cpp-v1.tar.gz.part'
with tarfile.open(part,'w:gz',dereference=True) as tar:
 for name,p in sorted(items.items()):tar.add(p,arcname=name,recursive=False)
archive=dest/'public-coupled-augmented-sensitivity-cpp-v1.tar.gz';part.rename(archive)
with tarfile.open(archive,'r|gz') as tar:
 count=0
 for m in tar:
  assert m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts and m.name in items
  blob=tar.extractfile(m).read();assert len(blob)==items[m.name].stat().st_size and hashlib.sha256(blob).hexdigest()==sha(items[m.name]);count+=1
assert count==len(items)
for r in freeze['files']:assert sha(r['path'])==r['sha256']
ready=dict(archive=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,regular_members=len(items),archive_payloads_verified=True,frozen_manifest_sha256=sha(freeze_path),source_manifest_sha256=sha(BASE/'BACKUP_SOURCE_MANIFEST.json'),gate=report['status'],all_failures_retained=True,Mac_copy_verified=False,phase5='NOT_ACCEPTED',phase6='NOT_STARTED',scope='Selected central-domain augmented cycle/cell sensitivities; all38 directions botheps at everyhalf/cycle/cell; no main-startup/globalplanner/controller/newplant/task/timing acceptance.')
save(dest/'READY.json.part',ready);(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2),flush=True)

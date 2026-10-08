#!/usr/bin/env python3
"""Immutable physical derivative reference packet, all prior failures retained."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path('/home/codextransfer/predictive_motion');BASE=ROOT/'results/phase5/development/public-coupled-derivative-cpp-v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
freeze_path=BASE/'frozen_before_predictions.json';freeze=json.loads(freeze_path.read_text());report=json.loads((BASE/'parity-attempt1/report.json').read_text());assert report['status']=='PASS_BOUNDED_PHYSICAL_DERIVATIVE_REFERENCE_ONLY' and report['freeze_sha256']==sha(freeze_path)
for r in freeze['files']:assert sha(r['path'])==r['sha256'] and sha(r['immutable_copy'])==r['sha256']
positives=[x for x in report['records'] if x['jacobian_success']];thresholds=[x for x in report['records'] if x['value_success'] and not x['jacobian_success']];invalid=[x for x in report['records'] if not x['value_success']]
stats=[]
for i,e in enumerate(report['epsilons']):
 stats.append(dict(epsilon=e,transition_absolute=max(x['epsilons'][i]['transition']['max_absolute'] for x in positives),transition_gate_ratio=max(x['epsilons'][i]['transition']['max_gate_ratio'] for x in positives),nq_absolute=max(x['epsilons'][i]['nq']['max_absolute'] for x in positives),nv_absolute=max(x['epsilons'][i]['nv']['max_absolute'] for x in positives),mass_absolute=max(m['max_absolute'] for x in positives for m in x['epsilons'][i]['mass_q'])))
review=ROOT/'reviews/phase_5_public_coupled_derivative_cpp_20261007.md'
review.write_text(f'''# Isolated analytic physical2ms transition derivative reference

Phase5 NOT_ACCEPTED; Phase6 NOT_STARTED. Private remote/master f381ba096ba25dd6914d338406df055c58dd5ded was independently verified against Mac HEAD before this unit. C++v2 and the augmented wrapper, Python baseline, public constants, all raw inputs and their existing binaries remain unchanged. This separate physical reference owns an independent Pinocchio MJCF Model/Data for derivatives and calls the frozen C++v2 model for the nominal value. There is no engine pointer, mjData, simulation stepping, parameter fitting, augmented-chain/horizon/main-controller integration, new plant run or untouched seed consumption.

Input x=(q7,v7,C7); output T=(q_next7,v_next7). The returned Jacobian is14x21 with columns q/v/C, rows q_next/v_next. h=.002s. The exact fixed forward equations are S=tau_clamped−P*v−n(q,v), W=M^-1,H=W+diagR,ell=W*S+diagB*v,f=argmin boxQP(H,ell), A=M+h*diagD,a=A^-1(S+f),v_next=v+h*a,q_next=q+h*v_next. B is the actual public velocity reference coefficient, not1/h. D=P−bias_v remains full and constant even when actual actuator torque is clamped. Full mass/coupling, gravity/Coriolis, passive damping, static regularizer, exact box labels and original-H KKT are retained.

Installed Pinocchio4.1.0 algorithm/rnea-derivatives.hpp139 documents zero-initialized output matrices and upper-only da. Source src/algorithm/rnea-derivatives.hxx540-543 adds parsed armature once to the mass derivative/torque; it is constant in q. computeRNEADerivatives(q,v,0) gives full Nq,Nv;7 calls with each fixed acceleration basis e_k give dM_j(i,k)=Dq_at_acc_e_k(i,j)−Nq(i,j). Each dM_j is mirrored from its upper triangle to match the forward CRBA convention. All8 calls initialize every output to zero. Their nominal torque/M are compared with the frozen base diagnostics. Parsed scalar indices/names, gravity, tool/body masses and armature are checked between models; no inertia or armature is added manually. Eight calls are an initial analytic reference implementation and carry no timing claim.

For each column, dW=−W*dM*W and dH=.5*(dW+dW^T) match the explicit forward box-Hessian symmetrization. dell=dW*S+W*dS+diagB*dv. Bound/fixed friction components have df=0; strict free F solve Hsym_FF*df_F=−(dH*f+dell)_F. Then da=A^-1(dS+df−dM*a), Jv=Ev+h*da and Jq=Eq+h*Jv. Smooth-force derivatives multiply the product of enabled affine-actuator/joint-force clamp slopes; C-columns additionally multiply the control clamp slope. These slopes never change implicit D. Actual public actuator-force flags are all disabled with range[0,0], so that stage records enabled=false,margin0,slope1 and is excluded from threshold tests. Enabled joint-force limits±87/±12 are represented separately.

Only a conservative strict-branch API is certified: control distance>1e-8rad, each enabled force-stage distance>1e-7Nm, friction free slack eta−abs(f)>1e-7Nm and free |gradient|<=1e-10, lower gradient>1e-7rad/s^2 or upper negative gradient>1e-7rad/s^2. eta0 is fixed2 with force/df0 independent of gradient. Exact labels alone do not establish strict complementarity. Every nested stage returns its input/output/bounds/enabled/side/slope/margin. Near/weak layers retain the correct value but return jacobian_success=false with no matrix.

Crucial scope: unsupported by this strict-branch API is not proof that the total composite map has no unique derivative. A downstream strict force clamp can annihilate a control-layer switching effect. Native error wording 'no unique Jacobian' denotes that this API does not supply a certified unique Jacobian; it is not a theorem of nondifferentiability. No one-sided/generalized Jacobian is delivered, and no unequal one-sided slopes are required for every control-threshold fixture. Margins are operational support gates, not an accuracy/safety certificate or a guaranteed perturbation radius.

All derivative intermediates must be finite. M,Hsym,H_FF when present and implicit A have SPD eigenspectrum/LLT, finite condition<=1e12 and original scaled solve residual<=1e-10. RNEA outputs/tensor, inverse/Hessian derivative products, friction RHS, acceleration RHS and14x21 outputs reject finite-input arithmetic overflow. Original native box KKT<=1e-10 remains independently checked. Current tests support selected fixed-profile numerical scale only, not every mathematical SPD system or all finite inputs.

The predeclared30 cases account for{len(positives)} supported Jacobians,{len(thresholds)} valid-but-unsupported weak/near thresholds and{len(invalid)} invalid-value inputs. Nine previously seen physical states are TRAIN91011 ticks100/500/1250/2400 and seen91013 ticks100/500/690/920/2400, first2ms half. Five prospective stable synthetic states cover all-free, mixed lower/upper/free, all strict friction bounds, strict joint-force saturation and strict control saturation. Synthetic prescribed f/gradient are built algebraically from retained original nominal_zero M/n/H, public affine torque and constant R; their prior input/output hashes and desired vectors are preserved. There is no fitted parameter or future plant evaluation. Weak lower/upper zero-gradient, near-free slack, exact/near control bounds and exact/near joint-force bounds are conservatively unsupported; wrong dimensions/nonfinite/preclamp overflow/physical joint-boundary inputs reject.

Original base probe fa1a00344e73d8fe2266541ba4e2b34c362351b30a4f21dfa34c04867f585a04 performs{report['fd_native_cases']} independently prepared one-step calls: each supported case has one exact-value baseline plus all21columns×both signs×both epsilon1e-6/3e-7. Every perturbed state must retain the same strict friction and nested clip branches/margins. The full transition, Nq,Nv and all7 mass partials are compared using |error|<=5e-7+5e-6|analytic| per entry, for both separately reported steps. No better-step selection or adaptive epsilon occurs. Exact baseline q/v and all force/M/W/H/bias diagnostics match the original value probe. First numerical attempt passes without source, input, margin or gate changes.

Observed maxima by epsilon (corresponding derivative units; normalized gate ratio dimensionless):
{json.dumps(stats,indent=2)}

Strict output validation reuses frozen native helper70b for every successful/failed value; it separately checks typed value/Jacobian flags, exact ordered unique roster, finite14x21 and7x21 matrices/tensor, complete branch diagnostics, explicit unsupported/invalid errors, absence of fabricated unsupported matrices and finite condition/residual arrays. One valid actual-output control passes;{len(report['synthetic_output_gates']['negative_controls'])} deliberate output corruptions reject. Those mutations are schema controls, not actual native numerical failures.

First CMake configure failed because Pinocchio's imported target was only discovered inside the base subdirectory. Exact source and configure logs/exit are retained in build-attempt1/source-at-failure. Only the new parent dependency declarations changed; build-attempt2 succeeds. Before predictions, static gate review completed metadata D/units keys; original successful source/binary remain under build-attempt2 and the updated probe build-attempt3 succeeds. The model equation implementation is unchanged by metadata completion. Metadata-only empty-roster preflight passes the frozen helper; no predictions occurred before final freeze{sha(freeze_path)} with{len(freeze['files'])} live/immutable identities. Prior2551 identities are checked unchanged before and after. No failure or incomplete evidence is overwritten.

Two actual data figures show the mixed analytic Jacobian with explicit block units and the separately reported FD comparisons/support counts. Initial matrix footer overlap and an axis range that hid the declared zero display floor were retained with both figures/source/provenance under visual-attempt1, then repaired without numerical changes. Final figures are visually inspected with script/data/input/native/freeze hashes. These are development diagnostics, not accepted controller/task images. Existing accepted CAD/task visuals remain; no successful complete new Phase5 task exists for a task-success video. Source/config/QA/reviews/figures plus a small checkpoint record are imported by the Mac backup owner for independent review/private Git backup. Large raw/SDK/runtime/failed-build evidence stays in verified immutable regular-member SHA/READY Dell+Mac archives. Backup does not accept Phase5. Further augmented sensitivities/controller/run work waits for this unit's remote-verified backup and narrow dispatch.
''')
items={}
def add(name,p):
 p=Path(p)
 if p.is_dir():
  for f in p.rglob('*'):
   if f.is_file() and '__pycache__' not in f.parts:items[name+'/'+str(f.relative_to(p))]=f
 else:items[name]=p
add('project/tools/phase5_public_coupled_derivative_cpp',ROOT/'tools/phase5_public_coupled_derivative_cpp');add('project/'+str(BASE.relative_to(ROOT)),BASE)
for n in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:items.pop('project/'+str((BASE/n).relative_to(ROOT)),None)
sources=['scripts/phase5/verify_public_coupled_derivative_cpp.py','scripts/phase5/plot_public_coupled_derivative_cpp.py','scripts/phase5/publish_public_coupled_derivative_cpp.py',str(review.relative_to(ROOT))]
sources+=['figures/phase5/phase5_public_coupled_derivative_cpp_'+stem+ext for stem in ('matrix','verification') for ext in ('.png','.json')]
small={}
for name in sources:add('project/'+name,ROOT/name);small[name]=dict(sha256=sha(ROOT/name),bytes=(ROOT/name).stat().st_size)
for p in list((ROOT/'tools/phase5_public_coupled_derivative_cpp').glob('*'))+[freeze_path,BASE/'parity-attempt1/report.json',BASE/'inputs/declared_scope.json',BASE/'visual_inspection.json']:
 if p.is_file():small[str(p.relative_to(ROOT))]=dict(sha256=sha(p),bytes=p.stat().st_size)
for r in freeze['files']:add('immutable_dependencies/'+r['sha256'],r['immutable_copy'])
save(BASE/'CHECKPOINT_FILE_MANIFEST.json',{name:dict(sha256=sha(p),bytes=p.stat().st_size) for name,p in items.items()});save(BASE/'BACKUP_SOURCE_MANIFEST.json',small)
for n in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:add('project/'+str((BASE/n).relative_to(ROOT)),BASE/n)
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-coupled-derivative-cpp-v1-20261007');dest.mkdir(exist_ok=False);part=dest/'public-coupled-derivative-cpp-v1.tar.gz.part'
with tarfile.open(part,'w:gz',dereference=True) as tar:
 for name,p in sorted(items.items()):tar.add(p,arcname=name,recursive=False)
archive=dest/'public-coupled-derivative-cpp-v1.tar.gz';part.rename(archive)
with tarfile.open(archive,'r|gz') as tar:
 count=0
 for m in tar:
  assert m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts and m.name in items
  blob=tar.extractfile(m).read();assert len(blob)==items[m.name].stat().st_size and hashlib.sha256(blob).hexdigest()==sha(items[m.name]);count+=1
assert count==len(items)
for r in freeze['files']:assert sha(r['path'])==r['sha256']
ready=dict(archive=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,regular_members=len(items),archive_payloads_verified=True,frozen_manifest_sha256=sha(freeze_path),source_manifest_sha256=sha(BASE/'BACKUP_SOURCE_MANIFEST.json'),gate=report['status'],all_failures_retained=True,Mac_copy_verified=False,phase5='NOT_ACCEPTED',phase6='NOT_STARTED',scope='Physical2ms analytic reference; strict selected branches, two independent base FD epsilon comparisons. No plant/fitting/augmented/controller/task/timing acceptance.')
save(dest/'READY.json.part',ready);(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2),flush=True)

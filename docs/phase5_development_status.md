# Phase 5 development status

Updated 2026-10-08, America/Toronto. **Project resumed by the human: “继续”.** The saved pause/checkpoint 365bcf6 remains preserved. Accepted through Phase4; Phase5 remains unaccepted and Phase6 has not started. The fixed affine-horizon algebra unit is independently verified and backed up. Current work is a separate live typed-model/horizon/cost source implementation after review of its interface, command history, configurable mesh and lossless compact capture design. No new plant/main/scorer protocol or phase acceptance follows from resumption.

Independent installed consumers verify the coupled horizon, nonuniform meshes, full objective, nonzero state/nominal coordinates and separated command/model histories. The dimension-amplified PSD certificate bug is repaired and independently regression-tested. Actual-state condensed/lifted matrices match through a closed-form embedding; signed-row compression preserves every original constraint. These mathematical checks are separate from robot results.

The v24 frozen installed-library consumer repeats 1,200 state-map checks, 120 full-cost checks and eight analytic solver/history checks successfully. Root also reruns the independent augmented-servo reference exactly: synthetic n=1/n=3 transitions, nonuniform meshes, initial/control sensitivities, lifted state elimination and full quadratic cost substitution agree. A separate frozen soft-model oracle now verifies the full30-state command/physical/progress transition, all160 horizon-control and30 initial-state sensitivities over nonuniform20cells/.8s, branch derivatives, generic lifted elimination and full test-cost substitution. Root reruns the final fixed-source publication with exact equality of all six files. Earlier source-identity race output is retained; final output snapshots and unchanged-source assertions prevent that ordinary workflow mismatch. These references do not validate an FR3 servo fit. They also expose why zero terminal physical/command velocity alone does not guarantee stationary physical rest when the held target differs from equilibrium.

The paused-simulation reference-v14 produces 195 predictive commands and advances to s=.060296. It fails with native INACCURATE; the original greedy progress stop then becomes infeasible. The dataset remains failed. Its maximum measured position error is 12.076 mm, and 138 substeps exceed its prefrozen declared 10 mm envelope. Model-versus-actual 4 ms velocity discrepancy reaches .00378529 rad/s. It does not establish Cartesian accuracy or online control.

The progress stop now preserves discrete speed continuation under bounded jerk. Root independently verifies five analytic cases and 1,000 sampled states. A focused test exactly replays all 1,390 original pre-stop physical records and applies the new shared stop. It completes in .932 s virtual time, with zero accepted speed, physical speed below 1e-4 rad/s, zero progress speed within numerical precision and zero progress acceleration. All recorded stop checks pass. This closes RET-002 only in its documented speed-continuation and moving-replay envelope. All 233 complete stop cycles still miss 4 ms.

The high-tracking-weight v19 run genuinely prepares the initial pose: measured position error falls from 3.216 to .337 mm over 139 predictive commits, while progress remains negligible before native INACCURATE. It does not establish indefinite progress starvation. Independent mathematical review identifies a more fundamental command/plant contract mismatch: the optimizer's acceleration input is converted from measured velocity into an accumulated position target, while the preview treats that input as physical double-integrator acceleration. The recorded acceleration identity is independently checked; a synthetic known-servo counterexample demonstrates the mismatch without claiming FR3 dynamics.

The Dell worker is addressing this contract with separate measured physical and accepted command states and a validated, robot-model/state-estimator-accessible servo prediction. A model may not use privileged simulation state or plant rollouts. An optional discounted progress objective passes its mathematical checks, but the first full diagnostic stops after three predictive commits on original SI-row CONSTRAINT_VIOLATION; this failed epoch is retained. Neither a cost change nor initial preparation repairs the actuator contract by itself. A complete 3-second functional diagnostic remains required. The 10 mm accuracy requirement, physical/command limits, original SI-row validation and native SOLVED-only policy remain. Paused reference budgets are distinct from the unchanged 50 ms online planner budget. No held-out evaluation tuning or final research claim follows from these development records.

The independent causal identification training fixture finishes 8 seconds of excitation and .76 seconds of stopping after warmup. Root verifies the three raw file hashes and all 5,380 records, including 4,380 active substeps: exact state/history continuity and command integration, no recorded contacts or audited frozen URDF/protocol bound violations, and native SOLVED/current-age checks. Final accepted velocity and acceleration are zero; physical speed is 9.992e-5 rad/s. Nine active full cycles miss 4 ms (maximum13.922 ms), so this is not online timing proof. The old Dell conversation released development writes for the human-authorized clean-conversation handoff; the new conversation owns Dell writes while root independently reviews and backs up.

The first causal affine model is frozen before seed91012 validation and remains unchanged. Root independently reconstructs its matrix forecasts and confirms no future-state resets. Reported metrics match to1.86e-14; 800 ms validation fails with q error4.437e-4rad and v error1.857e-3rad/s, above the prefrozen1e-4/1e-3 limits. Training also fails. Stable held-target dynamics and short-duration checks do not cure this mismatch. The model is retained and not integrated into the main controller. A configuration-bias extension improves excitation-only training but fails full training/stopping windows; it too remains rejected.

The public soft-friction local surrogate passes the same error limits on a prospectively frozen new91012 waveform. Root independently reconstructs scalar-box predictions: maximum800 ms error is1.190e-5rad and8.437e-5rad/s, report agreement1.08e-19; branch/held-target derivative checks also pass. Decision is only **PASS_LOCAL_RECORDED_INPUT_PREDICTION**. Effective inertia/bias are empirical parameters, not identified true rigid-body quantities; the surrogate omits full coupling. The earlier139-command preparation exceeds declared q/v/target-error bounds, so local success does not permit unrestricted main-controller use. A frozen larger-amplitude waveform stops at tick854 with native PRIMAL_INFEASIBLE and no completed-stop evidence. Its reconstructed QP has individually contradictory geometry and command/jerk rows; original failed data remains unchanged. A separate full 1,708-substep physical replay exactly reproduces every logged comparison; the first actual shared-stop QP also returns PRIMAL_INFEASIBLE with zero accepted stop commands and nonzero physical speed. Independent exact box-support arithmetic proves three geometry rows contradict the unchanged command/jerk box, even with the original SI acceptance tolerance. This negative diagnosis is verified, not a stopping pass. Admissible expanded-domain validation and C++ command/physical contract integration remain pending. Already inspected validation data cannot be called untouched model-selection evidence. A separate retrospective fixed-model diagnostic retains every complete v19 warmup/motion/stop window. Its139 motion-start800ms windows all cross stopping and leave the old domain; numerical errors are stress observations, not expanded accuracy acceptance. Root reruns full JSON and note exactly.

Evidence and scope:

The separate public C++ physical transition now passes40 complete previously seen recorded windows,4 synthetic transition cases,8 state rejections,14 QP cases and20 constant rejections;4 EOF requests remain incomplete. Root independently calls the frozen binary on10 state/14 QP cases. The model contains the tool and armature exactly once, owns PinoData, and never receives plant state. No augmentation/Jacobian/main-MPC integration occurs. A tiny-positive-eta labeling false rejection is shared with old Python and reproduced independently; fixed FR3 eta>=.248 is unaffected, while generic support remains open as NUM-007.
[Independent isolated C++ review](../reviews/evidence/public_coupled_cpp_v1_root_review_20261007.md).

Separate C++ v2 now corrects true-bound classification, including declared tiny
and subnormal force fixtures. All52 state/30 QP/20 constant results have their
expected outcomes;40 complete seen-input windows remain within original gates.
Root independently checks10 states/16 QPs and11 schema controls. The strict
v2 output verifier requires complete ordered unique rosters, typed statuses and
finite full traces. NUM-007/SCI-003 close only for v2; original Python/v1 limits
remain preserved. Exact bound labels do not certify a unique Jacobian. Both
hosts' immutable evidence and private source checkpoint b1d5c2f are verified.
[Independent v2 review](../reviews/evidence/public_coupled_cpp_v2_root_review_20261007.md).

The isolated coupled wrapper now passes34 positive/35 negative component cases,
including29 complete conditional recorded windows;4 EOF requests remain incomplete.
Root separately checks6 positive/21 negative cases,138 positive2ms points,
independent rational command/progress sums, exact held-input mesh subdivision,
and two mid-rollout failures with retained complete states. Accepted C/w remain
separate from physical q/v. All2551 dependencies and both immutable archives
are verified on both hosts. No derivative, main-controller, new plant,
physical-stop, task or timing acceptance follows. Physical local derivatives are recorded below; augmented sensitivities and
main integration remain pending.
[Independent augmented review](../reviews/evidence/public_coupled_augmented_root_review_20261007.md).

The separate analytic physical2ms derivative reference now passes14 selected
supported cases,8 uncertified thresholds and8 invalid inputs. Root independently
checks6 supported/3 uncertified/2 invalid cases and510 original-base FD calls
at both fixed epsilon values, full21-column transition and full bias/mass
partials. A nonzero-motion case verifies velocity-dependent bias. The strict
branch API omits uncertified matrices without proving the composite map lacks
a derivative. Eight RNEA calls are an analytic reference without timing claims.
All2590 dependencies and2644 payloads are verified on Mac/Dell; source/build
and layout failures remain preserved. Augmented/horizon sensitivities and main
integration remain pending.
[Independent physical derivative review](../reviews/evidence/public_physical_derivative_root_review_20261007.md).


The separate augmented cycle/cell sensitivity reference now passes6 supported
producer cases,12 valid but uncertified cases and11 forward failures. Root
independently checks4 positives/4 non-certifications/1 invalid input,555 old-value
FD calls and8,346 strict physical substep diagnostics. The nonuniform mesh
covers30 initial plus32 distinct cell-control coordinates, not tied inputs.
Both fixed epsilons and exact command/progress, h²Q, semiimplicit integration,
cell composition and matched-origin defects pass. Uncertified paths retain
original values and certified prefixes. The common actual start s=0/r=0 and
terminal bounds remain outside this interior prototype's support; do not move
history to epsilon. Boundary policy, horizon/cost and main integration, stopping,
task and timing gates remain pending. No new plant or numerical retuning occurred.
[Independent augmented sensitivity review](../reviews/evidence/public_augmented_sensitivity_root_review_20261007.md).


A separate command/progress extension API now preserves original closed-domain
values while providing composite Jacobians at nominal0/0startup and other
command/progress bounds. Producer17fixtures pass both fixedepsilons; root retains
all6 prospective fixtures, with5passing and1failed originalgate. The equilibrium-C
initialw+.0625/inwardalpha-.5 fixture changes friction branches for2epsilon1e-6
probes, with56 failed derivative entry comparisons; the smaller epsilon passes
but does not replace this failure. Every nominal map/prefix structure passes;
the failed case's nominal chain exactly matches original physical derivatives.
12 selected old-domain directional controls preserve actual closed-domain
rejection/acceptance. This is partial component validation, no finite branch
radius, admissible-neighborhood, safety or main-controller certificate. Full
horizon/cost/main integration, geometry/stopping/task and timing gates remain
pending. Source, cases, physical gates and both FDsteps remain unchanged.
[Independent boundary-extension review](../reviews/evidence/public_augmented_extension_root_review_20261008.md).


The one approved seed91013 simulation completes with the frozen public-v2 predictor and strict scorer. All9796 complete windows have zero failures; active2/4/40/800ms maxima are below original limits and near roundoff. Root independently verifies all5002 state records/2002attempts/262496captured QP rows and the exact window roster, plus21 predeclared forecasts and six enumerated force QPs. Source/model/parameters remain unchanged, with no fitting or rerun. There are1996full-cycle4ms misses, and the final new stop starts after a long hold. This is PASS_CONDITIONAL_RECORDED_INPUT_PREDICTION for known curated development input; main-controller integration, full task, moving-stop, uniform-domain,250Hz and Phase5 acceptance remain pending.
[Independent actual-run review](../reviews/evidence/public_coupled_validation_91013_root_review_20261007.md).

Separate scorer v2 now passes28 synthetic regressions (3 complete controls,25 rejected failures) and8 independent root capture-only checks. Every candidate, including tracking superseded by stop, receives continuation validation. Existing91012 data pass a retrospective integrity-only check with disclosed synthetic seed metadata; this supplies no new prediction result. Root re-reads all256 frozen live/cache inputs. The replacement protocol permits1..1250 shared-stop cycles and retains original active accuracy limits; warmup accuracy is descriptive, but any warmup/window/regime failure prevents PASS. Geometry-tail row-count and per-solve H/g logging limits remain explicit. The subsequent seed91013 run is reported above; Phase5 remains pending.
[Independent v2 review](../reviews/evidence/public_validation_91013_protocol_v2_root_review_20261007.md).

The first prepared seed91013 protocol is **not approved to run**. The collector/model/input identities and one-shot runner remain consistent, but its frozen scorer returns false PASS in nine isolated synthetic gate tests, including empty/truncated trace, nonfinite residual/QP values, warmup failure and invalid or omitted solver attempts. It also omits hash checks for consumed sidecar files. These are scorer-integrity counterexamples using a disclosed NoPlant stub, not physical trials or model failures. Preserve this unexecuted version and revise the scorer/protocol before any new simulation run. Root granted no run approval for rejected v1; later schema2 approval is separate.
[Independent rejected-protocol review](../reviews/evidence/public_validation_91013_protocol_v1_root_review_20261007.md).

The uncalibrated public coupled prototype now passes the original 2/4/40/800ms limits on every complete active TRAIN91011 window: 2190/2190/2181/1991 windows, plus500 warmup-start windows at each horizon. All stopping/crossing windows remain; there are no solver or scoring-regime failures. Reported maxima are near floating-point roundoff. Root independently reconstructs19 fixed windows with a separate coordinate friction solver, checks five actual force QPs by exhaustive active-set enumeration, and independently counts the complete raw-window roster. These are training-side conditional-input checks, not fresh validation, uniform model accuracy, an exact-engine claim or main-controller acceptance.

The v1 prototype's generic positive-solref B expression has an extra damping-ratio factor. All currently frozen ratios equal1, so the tested baseline values are unchanged; other ratios remain unsupported by this evidence and require a subsequent correction. The original source stays frozen. Root verifies the final80-regular-member archive and its78 declared payload hashes; all40 post-run XML/asset identities match the earlier original TRAIN freeze and immutable Dell cache. This closes preservation of that transitive asset set after the run, without pretending the original40-file pre-scan already included it. NumPy/BLAS identity is also recorded after the run. The earlier publication with four library symlinks remains NOT_READY and is preserved without extraction.

- [Selected independent public-model recomputation](../reviews/evidence/public_coupled_training_v1_math_audit_20261007.md)
- [Independent post-run preservation closure](../reviews/evidence/public_coupled_training_v1_post_closure_20261007.json)
- [Fixed baseline and publication limits](../reviews/phase_5_public_coupled_servo_training_v1_scope_20261007.md)

Separate public v2 corrects the positive-solref friction reference coefficient, preserves the original impedance profile, and explicitly rejects unsupported short time constants and nonfinite/nonpositive references. Independent fresh checks reproduce seven force-QP fixtures, two synthetic damping ratios and five rejected parameter cases; all19 fixed existing TRAIN windows match v1 exactly. Its88 explicitly frozen inputs include transitive model assets and the declared NumPy/BLAS dependencies. This closes the scoped reference-contract defect; it supplies no new training scan, fresh validation, generalized model accuracy or whole-environment reproduction claim.
[Independent v2 contract review](../reviews/evidence/public_coupled_v2_reference_root_review_20261007.md).

Six further development units are preserved with verified Mac/Dell archives and source checkpoint records. A position-catchup reference fails after its signed command-speed history becomes nonviable; an independent exact audit retains that empty intersection. Direct velocity replay avoids the catchup debt but fails original SI-row acceptance. Independent cold solves with tighter solver accuracy show that this captured QP is feasible, without reconstructing the missing original rejected point. Its fresh shared stop completes; this remains a failed primary trial.

The isolated signed command-velocity continuation cone passes independent exact recovery checks and C++/Python parity. It preserves both speed limits under bounded acceleration/jerk; it establishes no position or collision stopping guarantee. Actual accepted-history postchecks are required because floating-point rows and SI acceptance alone are not strict continuation certificates. The main predictive controller has not adopted this module.

A prospective v3 reference fixture combines direct recorded velocity, the signed cone, tighter solver accuracy and unchanged safety acceptance. Root independently verifies all 2,002 actual solved candidates against 262,495 exported original A/l/u rows, with maximum violation 1.640e-10, and all 2,001 applied command histories. The complete 5,002-row recorded audit also passes its stated bounds. However, the fixed scalar predictor still fails the original 2/4ms accuracy limits: maximum velocity errors are 2.696e-4/3.116e-4rad/s, against 1e-4; the 4ms position error is 1.163e-6rad, against 1e-6. Root reproduces all forecast metrics to 8.674e-19. The 40/800ms checks pass on this trace, but its long hold supplies most windows, and the final new stop begins already near rest. This does not establish a moving-stop challenge, domain-wide prediction, online250Hz execution, or main predictive-controller acceptance.

The causal C++ model modules reproduce the frozen augmented transition, Jacobians and nonuniform mesh sensitivities. Version2 adds malformed-input rejection and eight fixed-root friction branch cases, including explicitly declared one-sided behavior at exact clip thresholds. These are isolated algebra/API checks on the same limited local model; they confer no expanded physical accuracy. Read-only public-model review identifies a coupled dynamics route including tool mass and motor armature, with explicit friction-force and implicit integration contracts. Prediction accuracy for that route is still unvalidated. Any subsequent correction must use training data only and freeze before fresh validation.

- [Independent reference-v1 empty-box proof](../reviews/evidence/servo_safe_reference_v1_emptybox_20261007.md)
- [Independent reference-v2 precision diagnosis](../reviews/evidence/servo_safe_reference_v2_precision_20261007.md)
- [Independent signed continuation review](../reviews/evidence/signed_command_cone_math_audit_20261007.md)
- [Independent v3 model/QP/history audit](../reviews/evidence/servo_safe_reference_v3_root_audit_20261007.md)
- [Public coupled dynamics design review](../reviews/evidence/public_coupled_servo_design_review_20261007.md)
- [Independent nominal coupled friction-box oracle](../reviews/evidence/coupled_friction_box_root_oracle_20261007.md): seven fixed mathematical fixtures, original KKT checks and fixed-active-set sensitivities; root rerun produces exact JSON bytes. This supplies no physical prediction accuracy.
- [Causal C++ API/branch development review](../reviews/phase_5_causal_servo_api_v2_20261007.md)
- [Causal scalar v3 arithmetic hardening](../reviews/phase_5_causal_servo_finite_v3_20261007.md): a separate clone rejects nonfinite intermediate and returned transition/sensitivity arithmetic. The original finite-parameter counterexample is retained, old versions remain unchanged, and frozen scalar prediction accuracy is unchanged.

- [Preliminary implementation review](../reviews/evidence/phase5_implementation_review_20261006.md)
- [Independent moving-stop review](../reviews/evidence/phase5_moving_stop_root_review_20261007.md)
- [Independent command/servo mathematical review](../reviews/evidence/predictive_math_specialist_20261007.md)
- [Independent augmented-servo transition oracle](../reviews/evidence/augmented_servo_reference_20261007.md)
- [Independent failed causal-model audit](../reviews/evidence/servo_model_v1_math_audit_20261007.md)
- [Independent local soft-friction model review](../reviews/evidence/servo_soft_v2_math_audit_20261007.md)
- [Retrospective fixed-model stress and its scope](../reviews/evidence/servo_soft_v2_v19_retrospective_20261007.md)
- [Independent expanded failure and actual-stop audit](../reviews/evidence/servo_expanded_failure_stop_math_audit_20261007.md)
- [Complete producer negative diagnostic and render](../reviews/phase_5_servo_failure_stop_diagnostic_20261007.md)
- [Issue register](../reviews/issue_register.md)
- `results/phase5-early-review/reference-v14`: original failed motion and independent observations
- `results/phase5-early-review/moving-stop-v1`: immutable identities, exact replay/stop data and independent reviews
- `results/phase5-early-review/root-progress-continuation-fixed`: independent installed-library cone consumer

Complete predictive diagnostics, accuracy/retiming/early-intervention evidence, timing optimization, frozen evaluation and immutable export remain before the Phase 5 gate. Full research trials, retiming-package comparisons, scenario families, ablations, iiwa validation and final clean reproduction remain later work.

The isolated finite nominal/trial diagnostic now passes producer42-pair and
independent root13-pair value/branch/GLOBAL residual arithmetic checks. Root's
prospective finite nonuniform candidate changes friction branches; the actual
result and substantial residual remain recorded. No residual acceptance
threshold or finite trust radius is inferred. The earlier extension FD failure
remains failed. Main integration, candidate admission, task/timing and Phase5
acceptance remain open. See [independent review](../reviews/evidence/public_finite_trial_root_review_20261008.md).

Read-only source review confirms the installed preview is still a physical
double-integrator and has no external general-affine A/B/d interface. A separate
actual-coordinate30state/8input horizon adapter is specified, with explicit
fullcell native cumulative fields, lifted elimination, full objective constants
and failed-prefix refusal. Source review is complete; implementation/numerical
verification remain pending. See the [integration contract](../reviews/evidence/public_affine_horizon_integration_contract_20261008.md).

The source-only affine horizon interface is now independently reviewed after
three retained static revisions. Literal quadratic derivatives, cumulative
numeric quotas, complete sum fields and canonical accumulation are explicit.
Root oracle definitions pass syntax compilation only and are not evaluated.
This v1 prototype has a fixed N1/N4 diagnostic envelope; the project's
configurable N20/.8s and1.5s profiles still require a larger reviewed version.
All interface drafts and exact prepared source inputs are preserved on both
hosts. See the [source checkpoint](../reviews/evidence/public_affine_horizon_source_checkpoint_20261008.json).

The separate affine horizon core/CLI/native adapter now has a bounded source
semantic review. Ordered full-cost fields, literal raw-H polynomial derivatives,
archived relevant map/state native normalization and failure-path preallocation
ceilings are explicit. Root12-case/23-output-control and producer10-case/14-control
verification scripts are prepared as source only. No new build or numerical
execution has occurred. All static revisions and the temporary SSH transfer
failure are preserved, with52 source-preparation payloads verified on Mac/Dell.
See [source implementation checkpoint](../reviews/evidence/public_affine_horizon_source_implementation_review_20261008.json).


## Final minimal checkpoint before pause — 2026-10-08

The affine-horizon module retains its first failed build (exit2), receives only the reviewed yaml-cpp iterator compatibility/bracing fix, and completes the second build and first empty-input preflight (exit 0). Producer/root inputs are prepared without numerical evaluation. All 2,912 frozen dependencies and the 80,494,096-byte archive are hash verified; both Mac and Dell copies are retained. No nonempty kernel or checker was run, and no controller, motion, safety or Phase5 acceptance follows. Producer checker robustness concerns remain deferred. Historical pending/release fields in immutable evidence are superseded by the human pause.

[Checkpoint identities and verified copies](../reviews/evidence/public_affine_horizon_build_freeze_checkpoint_20261008.json); [pause record](../PROJECT_PAUSED.json). Private Git backs up small sources and these records; the large archive remains on both hosts.


## Resumed verification preparation — 2026-10-08

The versioned producer checker repairs three prospectively degenerate output controls without changing the reference formulas, input roster or tolerances. Static review and AST syntax validation pass; no numerical checker/kernel invocation has occurred. The old checker 8694 and freeze d3d4 remain preserved. New verification requires a separately reviewed full freeze with the root consumer’s explicit files schema. The USB4 bridge is active, but Dell SSH banner exchange times out; remote source installation and new freezing remain pending connection recovery.

[Versioned source review](../reviews/evidence/public_affine_horizon_checker_v2_source_review_20261008.json); [connection diagnostics](../reviews/evidence/public_affine_horizon_resume_connectivity_20261008.json). No new performance, motion, safety or phase result is claimed.


The separate v2 freezing helper passes source review: it preserves every old live/cache identity, writes fresh immutable copies, and emits the exact files schema required by the independent root audit. The fixed numerical execution plan is recorded prospectively. Neither the new freeze nor the numerical checks has run; Dell SSH recovery is still required. [Freeze source review](../reviews/evidence/public_affine_horizon_checker_v2_freeze_source_review_20261008.json); [prospective algebra plan](../reviews/evidence/public_affine_horizon_algebra_execution_plan_v2_20261008.json).


## Verification freeze completed — 2026-10-08

USB4 SSH recovered after the stopped Ubuntu/WSL instance and missing keeper were restored. Independent authenticated SSH and retained bidirectional transfer checks pass. The first v2 freeze completes with exit 0; all 2,921 live/cache inputs retain the original 2,912 identities and exact new checker/helper/review/plan/resumption sources. The 80,521,728-byte archive is fully verified on Mac and Dell, including all 2,723 payloads and embedded frozen inputs. Input coefficients, source model/binary and arithmetic gates remain unchanged; no nonempty numerical call has occurred. [Verified checkpoint](../reviews/evidence/public_affine_horizon_checker_v2_checkpoint_20261008.json). Numerical release follows remote backup verification; this preservation unit does not accept Phase5.


Before numerical release, the Mac USB4 bridge became inactive and lost its link-local IP. The extra root verification-report copy and second Dell archive read timed out (exit 255); they remain unconfirmed. Already verified immutable archive copies remain preserved on both hosts. The source checkpoint is saved while reconnection is pending; no numerical run has started. Repository visibility is now Public at the human’s explicit instruction in the communication-check chat; historical private wording is retained in immutable evidence.


## First fixed affine algebra verification — 2026-10-08

Both frozen first attempts pass: producer 10 cases (4 positive / 6 expected refusals), root 12 cases (4 / 8), all 37 output mutations rejected. Three malformed-document calls reject with exit 1 / no output. Recursive/lifted state and sample maps, full factor/offset/linear/constant objectives, actual initial shifts, native cumulative normalization and preserved source failures agree with the independent references. Original model/plant/solver/main/scorer calls remain zero.

Three inspected root-data diagnostic plots and full provenance are saved. Complete producer/root immutable archives are verified on both Mac and Dell. The earlier FD branch failure remains unchanged; public-source validation is limited to fixed N1/N4 algebra, not full project horizon or robot performance. [Independent review](../reviews/phase_5_public_affine_horizon_algebra_20261008.md); [checkpoint identities](../reviews/evidence/public_affine_horizon_algebra_checkpoint_20261008.json). The human has approved this checkpoint and future same-scope public backups. Source/figure backup proceeds under that authorization; no new main controller or motion run is released.


## Live typed-model source plan — 2026-10-08

The next interface plan passes source review and preserves every prior model/profile/failure. It separates measured q/v from accepted C/w/alpha history, binds actual completed boundaries, preserves the exact 4ms command law and requires honest new-model producer provenance. Configurable integer meshes support declared N20/.8s and balanced1.5s design shapes; .25/.75s exact requests refuse the4ms lattice mismatch. Compact capture retains all requested data and computed factors, while over-quota dense/maximal captures refuse explicitly. Resource tables are integer design estimates; opaque SDK allocations and process RSS are not certified. [Source plan](design/public_live_affine_v2/README.md); [independent review](../reviews/evidence/public_live_affine_v2_source_root_review_20261008.json). No new build or Model/plant/controller run is authorized by this source checkpoint.

## Live affine v2 foundation source — 2026-10-08

The separate foundation source now implements exact integer meshes, fixed shape/output quotas, shared batch/case ownership, static file/range identity facts, completed actual-history contexts and pure first4ms preview. Independent source review corrected candidate-versus-reconstructed acceleration in preview jerk and a shared-batch live quota gap; both earlier source versions remain preserved. All14 original source identities are unchanged. [Source and deferred verification](../tools/phase5_public_live_affine_v2/README.md); [independent review](../reviews/evidence/public_live_affine_v2_foundation_stage1_20261008/ROOT_SOURCE_REVIEW.json). This stage has not been configured, compiled or executed. Genuine Model/result ownership, normalization, full algebra/cost/capture and controller gates remain pending.

## Live Model boundary source2A — 2026-10-08

Independent static review passes the future frozen-protocol/profile gate and genuine Model/input/raw-result ownership source. Strict JSON scalar types, post-extraction handle availability and raw-base versus SDK allowance checks were repaired before delivery, with complete source histories retained. Only the necessary v2 foundation header extension changes an existing file; old original model/checker source and foundation cpp/CMake are unchanged. [Source/schema and deferred verification](../tools/phase5_public_live_affine_v2/model_boundary/SOURCE_REVIEW.md); [independent review](../reviews/evidence/public_live_affine_v2_model_boundary_stage2a_20261008/ROOT_SOURCE_REVIEW.json). No configure/build or Model call occurred. Complete cumulative normalization, algebra/cost/capture and separately reviewed frozen runtime protocol remain pending.

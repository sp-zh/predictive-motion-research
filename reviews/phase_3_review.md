# Phase 3 redundancy-resolution review

Decision: **PASS** for mathematical/component implementation and executed diagnostic coverage. The retained controller failures are essential evidence; this gate does not certify physical safety, collision handling or a research advantage. Phase 2's observation correction has passed its separate independent gate.

## Scope completed

The Eigen-only C++ library provides numerical-rank Moore–Penrose null projection, a separate damped leakage comparator, analytic externally bounded joint-centering cost/gradient, scaled and unscaled SVD indicators, finite-difference singular objectives and secondary command composition. Exact projection is evaluated as I-V_r*V_r^T; retained singular vectors use the declared relative cutoff. Truncating a nonzero singular value permits leakage of cutoff order. Positive-damping projection is explicitly excluded from executed secondary control.

Executed objectives are joint centering, minimum-singular-value ascent, regularized log-volume ascent and combined joint/sigma ascent, plus primary-only MP. Optional DLS primary is supported separately but no DLS-primary execution is claimed. Primary tracking uses the validated SE(3) differential. Joint centering is an aggregate quadratic objective, not a barrier; log-volume ascent does not imply increasing sigma_min. Finite-difference flags disclose repeated minima/rank-loss limitations. Finite inputs producing nonrepresentable SVD/leakage outputs are rejected.

## Evidence and independent checks

The immutable 516,910,135-byte source/evidence archive passed SHA-256 `f0c6f858dfd41cf7850bac2d3bc3f824b997cbfa796c62999bd4323eceef9803`. Root rejected an earlier still-growing transfer before extraction; final READY and manifest were verified. Restricted extraction checked all 407 manifest files. Canonical source/data were extracted; 158 historical files remain verified in the archive and native Dell workspace to avoid duplicate expansion. See `results/phase3/root_extract_review.json`.

Root rebuilt the math-only library in separate build/install prefixes and executed 13 actual GTest cases (15 aggregate cases including wrappers), with zero failures/skips. An installed external consumer ran from `/tmp`; its runtime dependencies are standard C++/C/math only. It checks exported projection, command, joint-objective and singular-indicator APIs on a different matrix dimension. `scripts/verify_phase3_independent.sh` and `results/phase3/root-independent` record the commands/results. Ament remains build/packaging infrastructure.

The numerical validator records 2,000 synthetic 6x7 matrices with exact/almost rank loss and 2,000 valid FR3 joint coordinates, analytic joint-gradient differences, projected descent, singular directional differences and both raw input matrices. Maximum exact JP leakage is 9.998107e-11, idempotency error 4.751222e-15, joint-gradient error 2.924944e-10, simple-sigma directional error 2.083419e-10 and regularized-log directional error 9.219968e-9. Damped JP leakage reaches 7.516507e-4 and idempotency error 0.0627414, demonstrating that it is a distinct operation.

Root's separate NumPy audit constructs the exact projector from null vectors and the damped projector by ridge normal equations. All 2,000 saved-input cases passed, with maximum recompute discrepancies <=4.10e-14 for projector diagnostics, zero analytic joint-gradient discrepancy and <=3.34e-16 for finite descent. This is an independent algebra check, not independent FK/derivative sampling. Model derivatives additionally have the recorded directional checks and the separately parsed URDF audit. `scripts/review_phase3_numerical.py` and `root_numerical_review.json` preserve the boundaries.

Root independently audited **all 216,000 canonical executed samples / 144 files** for post-step FK/q/pose-error alignment: position discrepancy <=1.970e-15 m, rotation <=5.578e-15 rad. A separate local stdlib audit recomputed command composition, state/target increments, accepted bounds, H/margins/directional derivatives, measured violations, pose errors, aggregates and failure classification. All passed. The worker's independent URDF/NumPy audit additionally recomputes J/projector/SVD/leakage at 4,320 executed samples. See `root_fk_summary.json`, `root_csv_review.json`, `summary.json` and the independent source programs.

Root streamed the preserved historical archive and compared every control/plant/reference array, q/time and intervention/violation flag against corrected records: all 144 files / 216,000 samples are exactly equal in serialized values. Only observation/error/clock fields differ. Historical gains were not replaced. Position-only scratch observation leaves integration state unchanged; the separately rebuilt observer consumer passed 200 observed/unobserved replay steps. The original cached-pose records are historical, not extra trials or current pose evidence.

## Freeze, results and failure evidence

Design SHA-256 is `d83bdea5698d28aafbf056b5370e2ee6c996a1fbbc6a82e7eb143c5cea7137b7`; selected gains hash is `8ce61c7ff52e84ceab749dde8afede084995350dc4618b3898afa19ffc19a0d2`. Development seeds 41011/41012 and evaluation 51011/51012 are disjoint. Each secondary objective receives three gains on the same eight development scenarios; 104 development and 40 evaluation trials use common original plant, 4 ms command/guard and virtual TCP. Selected gains are joint=1, sigma=.25, log-volume=4, combined=4. The historical selection used cached-pose error metrics; corrected diagnostic reranking agrees but is not substituted. Final research needs a new freeze with the corrected observer.

| Dataset | Completed | Measured-limit failures | Pose-tolerance failures |
|---|---:|---:|---:|
| Development | 101 | 3 | 0 |
| Evaluation | 32 | 6 | 2 |

Evaluation per objective: primary-only 8/8 completed, joint 6/8 with two pose failures, sigma 6/8 with two measured-limit failures, log-volume 8/8, combined 4/8 with four measured-limit failures. Broad component COMPLETED codes do not mean successful inspection tasks. All failures remain in raw records and aggregates. The joint-limit example shows combined control losing tracking after clipping despite raw leakage near roundoff; this supports the need for constrained control, not a claim of universally effective redundancy objectives.

## Known issues and technical debt

- Target limiting does not enforce measured velocity, acceleration/jerk, stale-state stopping or collision safety. CMD-001 remains open. Raw projection invariance cannot survive arbitrary command clipping and plant dynamics.
- Executed diagnostics use the original arm plant and a virtual TCP. All final methods must rerun on the common integrated CAD/tool/payload scene and independently validated geometry.
- Position-derived observation correction does not establish synchronized contacts, force or effort. That requires a separate observation contract; moving/mocap-driven bases are outside the tested observer scope.
- Execution compute timings exclude plant/CSV/ROS and precede added invalid-output checks. They are descriptive shared WSL costs, not complete-cycle 250 Hz evidence or a hardware guarantee. Final performance audit must use final code and explicitly measured load/latency.
- Two held-out seeds and small closed joint-derived paths cannot establish statistical superiority or meaningful inspection completion. Staying near the start can meet broad endpoint tolerances. Final protocols need nontrivial progress, strict completion and the mandatory 10/20-seed schedule.
- Fresh OS/container/hosted CI remain unverified. Current build uses installed Linux prerequisites; no GitHub remote exists.

## Scientific risk and next gate

Individual margins, aggregate H and singular indicators trade off, including unfavorable cases. Report these distinctions without pooling component scenarios into a research ranking. Numerical samples, replay, corrected reruns and adjacent trajectory rows are not independent experimental replicates.

Phase 4 must implement the OSQP reactive constrained baseline and common failure/command policy; independently validate collision geometry, normals/Jacobians and nearest-feature nonsmoothness; and integrate the strong MoveIt Servo baseline with comparable inputs/model/limits. No predictive, retiming, cross-robot, collision-control or hardware conclusion is supported by this gate.

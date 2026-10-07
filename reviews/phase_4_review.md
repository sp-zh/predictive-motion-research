# Phase 4 independent root review

Decision: **PASS for reactive constrained control, actual Servo integration and the stated component diagnostic envelope.** This opens Phase 5 implementation. It does not accept final research comparisons, continuous collision safety, hardware safety or real-time operation.

The immutable Dell export `phase4-evidence.tar.gz` is 135,699,457 bytes, SHA-256 `1e3ec6da7a8fb60a090aafa5d78405643624be6e4067c029af197d8dd5f17303`. Root verified all 544 manifest file identities and 545 regular archive members, and matched every pre-run identity to its executed source/binary snapshot. Original failures and the post-freeze monitor repair have separate identities. The transferred payload remains in `transfer/inbox/project-phase4`; its expanded snapshot is `results/phase4-export/predictive_motion`.

## Core mathematics and failure contracts

The C++ wrapper uses actual OSQP 1.0.0, with a quadratic tracking/ridge objective, explicit measured/accepted one-step position bounds, velocity bounds, commanded acceleration/jerk intersections and signed-distance velocity dampers. Fixed ridge regularization is the declared singularity treatment; manipulability is not claimed convex. Only a verified SOLVED result exposes a velocity. Nonfinite input, stale state, indefinite cost, inconsistent bounds, primal/dual infeasibility, solver limits and unacceptable constraint residuals remain distinct failure states.

Root read the implementation and actual XML: 16 QP, 7 IK and 6 null-space cases, with no failures, errors or skips. Regression cases reject the independently discovered finite-Hessian norm-overflow counterexample and derived constraint overflow. The normalized finite precheck and finite post-solve products resolve NUM-002 for this wrapper.

Root separately built a fresh three-DoF installed-package consumer outside the checkout and ran it from `/tmp`, with no robot/ROS runtime calls. Its coupled halfspace optimum and KKT multiplier were computed analytically: solution error1.924e-15, stationarity error9.442e-15, actual OSQP version1.0.0. This is one analytic consumer case, separate from the 29 unit cases.

The minimum-velocity stopping QP obeys the same history/limits/geometry. A moving nonfinite-request injection stopped the actual simulated plant in0.608s, with no contacts and declared physical derivative limits respected. Its command reverses briefly before settling; monotone or universal stopping is not established. When the intersection is infeasible, the runner records an unexecuted termination row, issues no new command and terminates simulation. This is an explicit failed trial, not a safe hardware-stop claim. The legacy ROS Plant invalid-command behavior remains a separate open scope.

## Independent data and geometry checks

Twenty expected paired diagnostic runs produced185,151 rows. Root independently reconstructed physical and commanded bounds, derivatives, accepted target integration, state ages, no-command termination state/time and summary outcomes. It rebuilt FK and SE(3) residuals from URDF with NumPy, without calling production Pinocchio or controller APIs:7,430 sampled states, maximum translation-residual error1.077e-15, rotation error9.676e-16. All recorded checks passed. Every raw trial SHA matches the independently audited file. Evidence: `results/phase4-early-review/root-csv-audit-20261005.json` and `package_review.json`.

The controller's collision provider reads model/configuration and measured joints, with no mjData or future plant rollout. It includes common arm hulls, all five full tool primitives including the bracket, four fixture components, floor and documented adjacent/fixed-mount exclusions. Source mesh vertices are retained inside their convex hulls, with asset identities and containment checks. The conservative1783-sphere tool cover has analytic box-cell/cylinder-slice enclosure proofs;50,016 sampled points provide additional enclosure checks. All81 offline path poses preserve conservative tool/environment comparison and clearance.

The reported geometry derivative sample counts are63 point directions,33,012 cover components,6,702 smooth true-distance components and858 nonsmooth one-sided components, with zero interval failures. Unchecked rows have zero checked counts and NaN error fields. Closest-feature ties remain present; the supervisor checks four kinematic subdivisions for both measured-state and persistent-target candidates. These discrete checks are not a continuous safety certificate. “True” clearance denotes unapproximated geometry of this shared controller model, not privileged physical ground truth. Independently synchronized MuJoCo contact counts provide a separate plant observation.

Each2ms plant step is followed by scratch mj_copyData/mj_forward. Production observations verify TCP/all-arm-frame alignment and exact unchanged live integration state. This accepts the recorded position/geometry/contact-state observation contract; it does not establish force/effort instrumentation.

## Actual Servo and retained outcomes

The external process calls installed MoveIt Servo2.12.4 C++ APIs; it is not a local imitation. Separate build contexts/PIDs isolate its ROS vendor dependencies from OSQP1.0. Common model/scene, Cartesian units, plant/reset/reference, limits and external command projection are documented. Collision, singularity protection and Butterworth smoothing remain enabled. A separate well-conditioned state exercises nonzero native output. Initial filter transients, plane-query crashes and other development failures remain preserved.

| Method | Development completed | Evaluation completed | Retained failures |
|---|---:|---:|---|
| MP | 2/2 | 2/2 | none |
| Fixed DLS | 2/2 | 2/2 | none |
| Adaptive DLS | 2/2 | 2/2 | none |
| Reactive QP | 2/2 | 1/2 | infeasible bounds, no feasible stop |
| Actual Servo | 0/2 | 0/2 | four native singularity halts |

These are two held-out seed clusters on one diagnostic path. They do not establish research superiority. Accepted MP/DLS/Servo commands are supervised projections and must retain that description. Decision age, API time, synchronization time and parent IPC time are separate; asynchronous Servo collision-state freshness is not inferred from a CSM match. The common external geometry supervisor provides the accepted measured-state check.

## Repair identity and remaining scope

Root caught the omitted online measured-position bound check. The executor added and compiled measuredPositionSafe;21 focused checks passed. Root verified that the benchmark diff only adds the guard include/check. The original source SHA `9c684eefd9515bb12ed5213a6d308ae87909be56b556de85bce0222d789c3cd7` and original binary remain preserved. New source SHA is `bff5c68ac9ecd62e89054583072e57bd9d5f3664af0be18c41a6ba591f9bdd17`; the original20 traces did not execute that new guard, although the independent original-row position audit passed.

Nominal command jerk20 reached20.006578992 within the declared propagated numerical tolerance20.0625. Physical post-warmup jerk402.437850 is below the declared500 simulation assumption, not a manufacturer limit. Decision age peaked37.639ms and excludes command commit, following physics/observations/logging and next-loop work. Full-cycle4ms timing was not recorded or proven. PERF-001 remains open.

Generated Servo models/meshes and shared-library identities are exported as explicitly post-run observations; the original pre-run freeze is unchanged. Future research freezes must capture the full effective input closure before evaluation. Geometry continuity, full scenario families, matched seven-method trials, predictive horizon/retiming, iiwa validation and final clean research reproduction remain unaccepted. ENV-003, SCI-001, continuous geometry and hardware scopes remain open.

# Phase 2 IK baseline review

Decision: **PASS** for basic IK implementation and corrected diagnostic evidence. Phase 2 was reopened after a post-step observation defect, then reinstated only after the independent correction checks below passed. Phase 3 review and all subsequent research gates remain separate.

## Scope completed and provenance

The C++ Eigen-only control library implements thresholded Moore–Penrose, fixed DLS and optional adaptive DLS, with invalid-input and nonfinite-output rejection. Positive damping uses stable singular-value gains; zero damping takes the thresholded inverse rather than dividing by zero at rank deficiency. Robot-specific configuration, kinematics and MuJoCo remain in a separate benchmark runner.

The delivered 71 MiB archive passed SHA-256 `2a2410af8c0627d3e32e84bd5e5cc96b037c53cb630c471fae4385aacb23f4be`; extraction rejected traversal and links and only accepted the control/config/phase2/evidence/consumer paths. The coordinator inspected the source, froze no new tuning settings, and independently rebuilt the mathematical library into separate build/install prefixes with benchmarks disabled. Seven GTest cases passed; an installed consumer ran from `/tmp` and its runtime libraries contain standard C++/C/math only. ROS ament is still the packaging/build infrastructure.

## Evidence

Tests cover all four Moore–Penrose identities, rank-deficient rectangular systems, full-rank agreement, DLS normal equations, exact-zero/near-singular sweeps, rank tolerance, adaptive policy, invalid inputs, damping covariance under global scaling and overflow failure. `results/phase2/root-independent` contains independent build/test/consumer/runtime-link evidence.

The original configuration was frozen before development. Development seeds 1101/1102 used the same five damping candidates (0.001, 0.003, 0.01, 0.03, 0.1) for both DLS methods: 44 executed development trials. Its declared objective selected fixed lambda=0.003 and adaptive maximum lambda=0.01 before the separate evaluation seeds 2101/2102. All 12 original evaluation trials completed within the declared development execution tolerances. These are two-seed component diagnostics, not the final 10/20-seed research schedule.

For each scientific seed, 20,000 configurations were screened within model/actuator limit intersections, and contact-free candidates were selected using declared singular-value quantiles. These screening samples are not independent executed controller trials. Raw-Jacobian weakest-direction sweeps and executed pose-residual differentials are distinguished. Weighting is [linear; 0.3*angular]; lambda and singular indicators belong to that weighted scale. The exact SE(3) tracking equation uses the validated residual derivative and desired-body derivative.

The coordinator's separate standard-library audit recomputed state/target continuity, accepted command bounds, measured violations, xyz errors, stable quaternion geodesic errors, aggregate errors/extrema and failure classification for **93,000 canonical executed samples**: 66,000 development, 18,000 original evaluation and 9,000 supplementary. `scripts/review_phase2_csv.py` passed and wrote `root_csv_review.json`. Repeated evaluation folders establish byte-identical replay after failure-policy fixes; they are not additional seeds/trials. Explicit invalid-config/fault probes are separately labeled.

## Dynamic singularity diagnostic and failure

Original joint-derived reference paths produced only gentle requested motion, so they did not exercise singular amplification dynamically. The review requested a separate supplement after the initial evaluation, using newly frozen seeds 3101/3102, the already selected damping and a small closed SE(3) excursion along the initial weakest left singular direction. The supplement is excluded from tuning and original evaluation aggregates; reference feasibility was not pre-certified.

Five of six supplementary runs completed within declared tolerances. In seed 3102, MP requested a maximum component 6,917.44 rad/s, had 585 intervention cycles and 164 measured speed-violation samples. The common adapter capped accepted components, but measured plant speed reached 7.52819 rad/s; corrected peak position error is 0.903217786 m and rotation error 2.565196034 rad. The run correctly reports **EXECUTED_LIMIT_VIOLATION**. Fixed/adaptive DLS in that case had no reported limit violations. MP also completed seed 3101 and had lower mean tracking error there. The graph is illustrative, not a representative statistical benefit claim.

## Known issues and debt

- Componentwise target-rate limiting does not bound actual plant velocity, as the retained stress failure proves. Acceleration/jerk, stopping behavior, stale state and collision enforcement still require later common-control work (CMD-001).
- Initial contact filtering does not establish trajectory collision safety. All methods in this phase used the original plant, with a virtual TCP. Final research trials must rerun all baselines on the same integrated CAD/tool/fixture/payload plant.
- Pose tolerances (final 0.01 m/0.05 rad; peak 0.05 m/0.2 rad) are broad development execution tolerances. The small closed excursions can meet endpoint tolerances without demonstrating completion of a meaningful inspection task. Report numerical termination/error trajectories separately from research task success; do not promote these codes to final success rates.
- Weighted residual-Jacobian singular indicators during tracking are not identical to raw geometric J indicators. Both conventions must remain explicit in later comparisons.
- The original two-seed evaluation and supplementary two-seed diagnostic cannot establish general/statistical superiority. No predictive, retiming, redundancy, constrained-control or hardware claim is supported.
- Fresh OS/container/hosted CI remain unverified. Independent build uses existing installed dependencies and the existing packaging overlay.

## Scientific risk and next gate

The supplementary diagnostic was requested after seeing the original evaluation's lack of excitation; this history must remain disclosed. Its feasibility and controller/plant/guard interactions prevent algorithm-only causal claims. Baseline parameters were not retuned on it. The subsequent research schedule must be frozen independently and include nontrivial progress/completion measures so staying near a closed path's start cannot appear successful.

Phase 3 must verify exact versus damped projector leakage, analytic joint-limit gradients, multiple singular indicators and executed self-motion objectives. It must preserve the distinction between mathematical null-space behavior and behavior after command guards/plant dynamics.

## Observation alignment correction and reinstatement

The earlier PASS review is preserved in `results/phase2/root_review_before_alignment_finding.md`. Independent Phase 3 review found that `Plant::step()` ends with `mj_step`, leaving cached sites before the final integration substep while q/time are post-step. The original CSV audit verified reported pose errors internally but did not compute FK from post-step q. Root independently reproduced the mismatch in all 62 original files / 93,000 rows: regular evaluation maximum 0.134 mm; supplementary maximum 6.839 mm and 0.018106 rad. Original pose metrics/plots remain historical, not corrected evidence.

The runner now copies post-step qpos into separate mjData and calls `mj_kinematics` there. Its position-only observer does not change the plant, solver caches or integration/warm-start state. It does not claim synchronized contact/force/effort data. The original plant and mathematical IK core remain unchanged. Root separately rebuilt the exported observation consumer: 200 observed/unobserved steps had identical integration state and time after every step, with same-q FK position/rotation error <=1.103e-15 m / 1.440e-15 rad.

Corrected archive SHA-256 is `db96ac3873843387192c8e6f046e8ab36ebed42962283c4561e72f4c5e3f66e4`; paths and prerequisites are in `results/phase2-observation-sync/metadata.json`. Root safely extracted it, reran the CSV audit locally and independently checked **every** corrected sample through its separate C++ FK program. All 62 files / 93,000 rows passed: position mismatch <=1.842e-15 m, rotation <=4.927e-15 rad; recomputed pose-error discrepancies <=2.23e-15. See `root_fk_summary.json`, `root_csv_review.json`, `root-observer-consumer`, and `tests/integration/inspection_scene/pose_alignment_probe.cpp`.

A separate root exact serialized-value comparison verifies that every q/time, requested/accepted/executed/reference array and intervention/violation flag matches original records, recorded in `root_trajectory_equivalence.json`. All 12 original evaluation outcomes remain COMPLETED; supplementary outcomes remain five COMPLETED and one EXECUTED_LIMIT_VIOLATION. Historical damping selection was made using the original cached-pose metrics and remains disclosed; it was not replaced. A diagnostic corrected development ranking happens to agree. Final research requires a fresh development freeze using the corrected observer, not these two-seed component results.

Canonical aligned pose evidence is `results/phase2-observation-sync/{development,evaluation,weak_direction}`. The original archive, data and reopened-review history remain retained. These executable checks resolve the Phase 2 observation defect and restore this component gate; they do not close command safety, collision fidelity or final research acceptance.

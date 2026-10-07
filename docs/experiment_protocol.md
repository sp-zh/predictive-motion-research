# Experiment protocol

This is a protocol, not an experimental result. Final numerical thresholds/configurations are frozen after development tests and before held-out evaluation.

## Trial identity and reproducibility

Every trial records source revision plus dirty-tree hash, robot/model revision and SHA-256, dependency inventory, compiler/build type, solver settings, host/kernel, clock periods, scenario parameters and seed. Failure output is retained in the same schema as success. Incomplete/controller-crashed runs are counted, not dropped from aggregate success rates.

Development and evaluation seed lists are separate versioned files. Obstacle/task generation uses a named deterministic RNG implementation; a seed alone does not identify an unspecified random generator. Frozen scenario families and limits are recorded before comparative data collection. Controller parameter search has a declared equal resource budget. Evaluation data is never used for tuning.

## Common plant and command policy

All methods share MuJoCo assets, actuator gains, timestep, joint limits, input reference, initial states, tool/fixture, collision model and evaluator. Compare 250 Hz requested control and report actual cycle timing. If Servo runs asynchronously, record actual message timestamps/latency and executed command age; do not count asynchronous latency as zero.

Reactive controllers receive the current reference/state and common scene. Predictive controllers additionally receive the declared path preview. TOPPRA receives complete fixed paths and is evaluated separately for that information advantage. External Servo safety features stay enabled with documented settings. Its status codes, scaling and smoothing are retained.

Every reset restores actuator/filter state, warm starts, prior acceleration/progress, contact state and RNG state. Reset tests compare complete recorded states at each step of repeated runs, not just the final TCP position.

## Metrics and censoring

Position error is ||p-p_d(s)||; rotational error is ||log(R^T R_d(s))|| in radians. Integrate time-weighted squared errors at executed sample times. Report incomplete-task error and success together so stopping at the initial state cannot appear accurate/successful.

Task success requires declared endpoint tolerance, terminal pose accuracy, no hard constraint violation and no fatal controller/plant failure. Duration-limited unfinished runs are right-censored for completion time but remain failures for completion rate. Record wall time and simulated task time separately.

Safety margin crossings and actual contact/collision events are distinct. An event is a contiguous interval below a threshold, not each control sample counted as a new collision. Report minimum independent signed clearance and time spent in violation. Allowed tool/workpiece interactions must be declared before running; fixture contact is not silently excluded.

Executed dq/acceleration/jerk are sampled at known periods; derivative filtering, interpolation and endpoint conventions are documented. Distinguish commanded constraints from plant compliance. Near-stop speed threshold/dwell is set in config; count transitions with hysteresis, not noisy sample crossings.

Record solver status, residual, iterations, build/linearize/collision/solve/update/ROS costs and complete cycle duration. Deadline miss means measured complete cycle >4 ms when requesting 250 Hz, independent of whether MuJoCo is running faster/slower than wall time.

All post-step evaluation poses, geometry and contact records must correspond to the same q/time as the executed joint-state sample. MuJoCo's derived caches after integration may describe the preceding substep. Refresh observations on independent scratch data with an explicitly documented scope; never replace integration/warm-start state with that scratch state. Acceptance includes FK from the recorded q, unchanged integration state, and observed-versus-unobserved replay. Position-only `mj_kinematics` observations do not validate contact/force/effort timestamps; those require a separate synchronized observation contract.

## Statistical comparisons

Use paired trials: methods share robot, initial configuration, path, obstacle and seed. Report success counts/denominators, binomial confidence intervals and paired outcome tables. Continuous comparisons include distributions and paired differences with seed-level resampling; do not treat adjacent time samples as independent experimental replicates.

The initial seed schedule has 10 development and 20 evaluation seeds. If rare failures require more samples, extend the frozen schedule before looking at method-specific wins and report the extension. Never claim general statistical power from this initial count alone.

Earlier component gates may use separately identified diagnostic seed sets. Phase 2 uses development 1101–1102 and evaluation 2101–2102 for algebra/plant validation; these runs do not replace the final research schedule and cannot support broad comparative or statistical claims. Its 20,000-configuration search per seed is a kinematic screening sample, not 20,000 independent executed controller trials.

## Ablation and horizon protocol

Remove prediction, singularity term, future joint-margin term, predictive collision, adaptive path speed, jerk constraint and reduce horizon in separate variants. Preserve remaining terms/constraints/settings. Document unavoidable changes in feasibility and solver size. A negligible or negative component benefit is reported.

Horizon durations: 0.10, 0.25, 0.50, 0.75, 1.00, 1.50 s. Record actual mesh/count/duration; ensure a requested duration is not rounded silently. Compare performance with complete-cycle timing, not solver average alone.

## Artifacts

Run directory includes config.yaml, metadata.json, metrics.json, trajectory.csv, solver_stats.csv, logs and optional rosbag. Analysis generates aggregate tables and figures from those files. Figure code, input manifest and analysis dependency versions travel with final evidence. Demo selections are labeled illustrative and excluded from claims based on held-out trials.

# Phase 5 local soft-friction servo model v2

Date: 2026-10-07, America/Toronto. Development model error checks: **PASS**.
Independent component review remains pending. Phase 5 is not accepted and the
main MPC has not been modified. This is a local measured-data model check,
not a task, stopping, robust-safety, hardware or online controller certificate.

## Declared causal model

For each configured joint, let e=c-q, where q/v are measured physical state and
c is the accepted position target. Published position gains, passive damping,
friction bounds and solver parameters are read from the frozen model XML and
joint order from robot.yaml. The model fits a positive local effective inertia
m and a constant bias g using only the 4,000 completed 91011 excitation substeps.
m is not identified rigid-body inertia and g is not identified true gravity.
Joint coupling and configuration variation are omitted approximations.

With h=2 ms, total damping D=kv+joint_damping, friction bound eta, impedance d,
and reference decay B, the frozen transition is

```
s = kp*(c-q) - D*v + g
f = -clip(d*(s+m*B*v), -eta, eta)
v_next = v + h/(m+h*D)*(s+f)
q_next = q + h*v_next
```

This is a declared diagonal approximation to the public soft friction box
problem: A=1/m, R=(1-d)/(d*m), minimize
`.5*(A+R)*f^2+(s/m+B*v)*f` over `|f|<=eta`. The scalar box solution gives the
clip expression. The damping update follows the public implicit-in-velocity
form; it does not incorporate the constraint-force derivative. The official
[MuJoCo 3.3.7 computation documentation](https://mujoco.readthedocs.io/en/3.3.7/computation/index.html)
specifies the friction box dual and implicitfast conventions. Defaults and the
reference-decay expression are checked against the fixed
[3.3.7 constraint source](https://github.com/google-deepmind/mujoco/blob/3.3.7/src/engine/engine_core_constraint.c).
This derivation does not assert equality with the full coupled plant.

The predictor uses NumPy arithmetic only: no mj_step, mj_forward, real-plant
clone, future physical measurements or future estimator data. Its 4 ms
transition composes two 2 ms predictions with a held accepted target. Other
durations are not silently interpolated. Clip thresholds are nonsmooth; the
supplied tangent is exact only within a fixed active branch and independently
finite-difference checked away from thresholds.

## Freeze and new validation trace

The frozen model is
`results/phase5/development/servo-model-soft-friction-v2-frozen/model.json`, SHA
`984ee85d086aeba7da8260a20b21b301e23dfd2c698a6c61ace0ff956bbec1bb`.
The fitting source, tests, scoring source, model and error limits are frozen
before collecting the new trace. All 187 execution inputs were materialized in
the immutable identity cache without missing files. The model SHA is unchanged
after execution.

The prospective run `servo-soft-friction-v2-validation` retains seed 91012 for
initialization but uses a new waveform: frequency `0.73+0.103*j` Hz and phase
`0.27*j` rad, zero-based j. Amplitude 0.0006 rad, the 0.8 s ramp, 8 s excitation,
2 s warmup, common plant and all command/geometry/50 ms guards are preserved.
The root confirmed this new protocol before collection. The observed v1 91012
trace is not reused for fitting or claimed as an untouched holdout. Neither
evaluation nor final research seeds were used. The original training binary and
source remain unchanged; the new validation-only executable refuses training.

Conditional predictions initialize measured q/v once at each 4 ms boundary in
excitation/stopping, then use completed recorded accepted targets. They do not
reset to future measurements inside a window. This offline conditional test is
not an online controller permitted to know its future accepted targets.
Overlapping windows are diagnostics, not independent trials.

| Duration | New heldout max q error (rad) | q limit (rad) | New heldout max v error (rad/s) | v limit (rad/s) |
|---|---:|---:|---:|---:|
| 2 ms | 4.04146e-8 | 1e-6 | 2.02073e-5 | 1e-4 |
| 4 ms | 8.53936e-8 | 1e-6 | 2.34998e-5 | 1e-4 |
| 40 ms | 2.52737e-6 | 1e-4 | 8.02332e-5 | 1e-3 |
| 800 ms | 1.19014e-5 | 1e-4 | 8.43685e-5 | 1e-3 |

The 800 ms row covers all seven joints and 2,024 starts, including windows that
cross into stopping. Training including stopping also passes: q 1.07722e-5 rad,
v 8.56621e-5 rad/s. These are the original v1 limits, with no holdout tuning.
They are empirical joint-error checks; the executed 10 mm task requirement and
all original SI/native SOLVED/hard/derivative limits remain unchanged.

Training q/v/c and target-minus-q ranges are recorded per joint in model.json.
The declared development domain is training excitation q min/max expanded by
0.002 rad, |v|<=0.005 rad/s, and training target-minus-q min/max expanded by
0.0003 rad. Every active new validation record stays inside this domain. It is
an applicability restriction, not a proven robust error tube or permission to
extrapolate to larger task motion. Measured acceleration, jerk, geometry and
task checks still require their independent executed-state validation.

The new fixture returns 0, finishes its bounded stop, and records clearance
0.0155670314 m. Its raw SHA is
`c435bea765c9a12e73bc12d12e2dfa7b6cbb6ddf877f1d519d9056810b21f03c`.
Warmup maximum speed is included in the reported 0.02992224 rad/s. Independent
root fixture review and full-cycle timing inspection remain separate.

## Preserved negative candidates and source checks

The original translation-invariant affine v1 remains failed and immutable.
The additional affine configuration-bias candidate `E(c-q)+Vv+G(q-q_ref)+d`
has rank 22, scaled condition 256.12 and hold spectral radius 0.996002. It passes
excitation-only 800 ms error checks, but the complete training replay including
stopping fails: q 5.34267e-4 rad, v 1.34760e-3 rad/s. It was not given a new
validation trial or adopted. Its model SHA is
`45d3a10a63339b88c451e057f7e807ba9e4abdf144296431a557b6b9a7462a19`.

A hard sign-friction force-balance exploration produces an indefinite fitted
mass matrix and is rejected. The training-only soft-friction probe and the
first pre-domain-record model are preserved as intermediate artifacts. None
uses old heldout data for fitting. These alternatives do not identify the
unique physical cause of the affine candidate's failure.

Four independent synthetic soft-model tests pass: numerical scalar box
minimization versus the closed-form transition, active/saturated branch
tangents versus finite differences, known positive inertia/bias recovery, and
unexcited-data rejection. Four additional configuration-bias affine tests pass.
These check model mathematics, not physical robot accuracy. The new validation
executable builds successfully. A missing-new-target first build and a
pre-execution runner missing-binary check are retained as development setup
failures; neither starts an experiment. Existing main-core source was not edited.

The actual-data figure shows all four error horizons and a worst heldout
position-error window. It has been visually inspected for readable labels,
units, legends and local scope. No CAD/model geometry units changed. Its
source/output hashes and inspection record are included in the checkpoint.

## Remaining work

Obtain the independent local component review first. Then translate the model
and exact tangents to C++ and verify them against independent references.
Preserve separate physical(q,v) and accepted(c,w) histories, optimize command
alpha, compose actual 4 ms target updates and two 2 ms physical substeps, check
command jerk against its 4 ms event duration, and declare terminal hold/
settling semantics. Do not infer robust terminal stopping from this empirical
velocity error, which is close to the 1e-4 rad/s observed-stop threshold.
Enforce the declared model domain and monitor residuals/cache invalidation.
Larger-domain identification/validation remains necessary before claiming a
complete predictive task. CTRL-001 stays open until coherent controller and
executed closed-loop evidence pass; Phase 5 still needs its independent gate.

Mac root owns independent review, source integration and private Git backup;
the current clean chat remains Dell's single source/experiment writer.

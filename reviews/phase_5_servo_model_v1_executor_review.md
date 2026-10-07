# Phase 5 servo-model v1 development checkpoint

Date: 2026-10-07, America/Toronto. Model integration decision: **FAIL**.
Phase 5 remains unaccepted; Phase 6 has not started. This work preserves a failed
local physical-prediction candidate, not a controller-performance result.

## Contract and independent split

The candidate uses only physical encoder q/v and the accepted, held position
target: `v_next=E(c-q)+Vv+d`, `q_next=q+0.002*v_next`. All seven joints are
coupled. E is in s^-1, V dimensionless and d in rad/s. The position equation
matches the recorded 2 ms implicit position update to 4.44e-16 rad. The 4 ms
transition composes two physical steps at the same accepted target. No fractional
matrix interpolation, privileged future plant state or simulator stepping is
used by this prediction code. No main-controller contract was changed.

Fit data are exactly the 4,000 excitation substeps of completed seed 91011;
warmup/stopping are excluded from fitting. Centered/scaled least squares has
rank 15, condition 74.2344, no ridge or selected hyperparameters. The held-target
state matrix has spectral radius 0.996297; stable hold is insufficient to make
the forecast accurate. Training-only exploratory probes are retained separately.

The model and all error limits were written before the new 91012 fixture was
started. The frozen model SHA-256 is
`904460b19cd1014b624e15a6e2dd8827f07a590db08c3d60f86ce896e8a19200`.
It is unchanged after that run. The new runner materialized 180 frozen inputs,
with no missing cache blobs. It preserved the existing fixture source, binary,
plant, excitation protocol, seed split, command/geometry/age guards and bounded
stopping policy. No completed 91011 training was repeated.

## Measured conditional prediction error

At each recorded 4 ms boundary in excitation/stopping, initialize q/v once and
predict using the completed trace's accepted targets. There is no state reset
within a prediction window. This is offline conditional model validation, not
an online forecast allowed to access future accepted targets. Windows overlap;
their counts do not represent independent trials. The maxima include all seven
joints and every eligible start, with 2,020 heldout 800 ms windows.

| Duration | Heldout max q error (rad) | q limit (rad) | Heldout max v error (rad/s) | v limit (rad/s) |
|---|---:|---:|---:|---:|
| 2 ms | 1.14592e-7 | 1e-6 | 5.72958e-5 | 1e-4 |
| 4 ms | 2.62484e-7 | 1e-6 | 7.39462e-5 | 1e-4 |
| 40 ms | 1.41669e-5 | 1e-4 | 6.09792e-4 | 1e-3 |
| 800 ms | 4.43666e-4 | 1e-4 | 1.85700e-3 | 1e-3 |

Training 800 ms error also fails: q 4.19258e-4 rad, v 2.07096e-3 rad/s
(including stopping windows). Neither trace leaves the declared local q/v box.
Short-duration fit accuracy does not validate the required 0.8 s horizon. These
prefrozen empirical joint-error limits are additional development checks; they
neither change nor establish the executed 10 mm Cartesian requirement. There is
no robust uncertainty bound or physical-stop certificate.

The 91012 fixture itself returns 0, completes bounded stopping, and records
minimum clearance 0.0155670314 m. Its 0.02992224 rad/s maximum includes warmup.
The raw SHA-256 is
`3331840951457d0219cc0c461ea1339cead478211727c3ffc8579a7e2f847912`.
Independent root review of the fixture and model remains required. Successful
fixture collection does not change the failed model decision.

## Source checks, visual and retained limitations

Four synthetic regressions check known coupled-model coefficient recovery,
unexcited/rank-deficient rejection, translation invariance and direct-versus-
composed held-target transitions. They pass; the intentionally rank-deficient
case emits a divide-by-zero condition-number warning before rejection. The
warning and exact fitting source remain preserved with the frozen candidate.
These tests do not validate robot dynamics.

The four-panel actual-data figure compares prefrozen error limits and a heldout
worst-position-error window. It is visually inspected: legends, units, recorded
versus predicted curves and rejection scope are legible without clipping. No CAD
geometry or model units changed. The figure's source/output hashes and visual
inspection record are retained under `servo-model-v1/figures`.

## Next authorized work

Do not integrate v1 into MPC, relax its limits, shorten the required horizon to
call it accepted, or refit it on 91012. CTRL-001 remains open. Investigate the
already failing 91011 multi-step prediction using a structurally constrained
public-dynamics/interface model or an explicitly declared causal model class.
Preserve v1 first. A later candidate needs its own model/protocol freeze and new
independent development-validation trace; the observed v1 91012 trace cannot be
silently reused as an untouched holdout. No evaluation/final-research seeds may
be spent on this development repair. After a model qualifies, implement the
physical(q,v)/accepted(c,w)/command-alpha preview and independently check its
micro-update, jerk and terminal semantics before closed-loop experiments.

Single writer: `01a114d9-3a3a-7071-b94f-624581000992` on the existing Dell WSL
project. Root `01a10958-048c-7480-a04e-51544112196c` retains independent review
and sole Mac Git integration/backup. Historical handoff and accepted Phase 4
evidence remain intact. A completed backup of this failed unit is not Phase 5
acceptance.

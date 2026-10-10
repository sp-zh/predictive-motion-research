# Coupled horizon to QP and first-command seam, source candidate V1

This package is SOURCE_ONLY. No configure, compiler, link, probe, constructor,
metadata, task getter, forecast, solver, numerical check, plant, main or scorer
has run for it. Phase5 NOT_ACCEPTED; Phase6 NOT_STARTED. Existing production,
parameters, original checker, ec1/d3d4 freezes and all prior failures are untouched.
The rejected seed91013 protocol V1 remains forbidden.

The useful new connection is implemented in C++, not just proposed:
`runFirstCycle` consumes an already prepared genuine single-use invocation;
`openPinnedModel -> forecastPublic -> normalizePublic -> assembleLiveAffine ->
connect inline objective/constraints -> solveQpCertified -> original SI gate ->
first4msRequest -> independent candidate-forward data request`.
The original forecast remains owned through normalization/affine/integration,
including returned raw values, error and unsupported derivative prefixes.
No public RawResult/fixture/algebra-state factory constructs an OwnedPublicForecast.
A failed or incomplete N20/T200/S400 roster stops; no shorter horizon exists.
No candidate request is an execution permission; executionPermission is always false.

## State, lattice and the command law

State order is q[0:7], v[7:14], C[14:21], w[21:28], s[28], r[29].
q/v are the actual physical observation. C/w are completed accepted command
history, independently of physical tracking lag. previous_alpha/previous_b are
completed command/progress history. All21 boundaries are composed from the
same genuine initial and all20 cell maps; all400 two-millisecond physical
sample prefixes are composed from the correct cell-cumulative A/B/defect.
Native Map.A/B are local cycle maps and are never substituted for cell_A/B.

N20 exact integer cycles are
[1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40], sum200, forecast .8 seconds.
This is a new diagnostic nonuniform profile; config/phase5.yaml's original
uniform20*.04s profile is retained and not rewritten. h=.004s, physical half=.002s.
For each accepted update: w_next=w+h*alpha, C_next=C+h*w_next.
For k constant-alpha updates: w_k=w_0+k*h*alpha,
C_k=C_0+k*h*w_0+k*(k+1)*h^2*alpha/2. Continuous .5*(k*h)^2 is incorrect for C.
Progress is separately s_next=s+h*r+.5*h^2*b and r_next=r+h*b.
Half references follow the native cell-origin progress polynomial. This does
not replace the distinct recursive cycle-end native values/defects.
Every input-change jerk compares alpha/b to accepted previous input at h=.004,
including future cell boundaries; it is not divided by cell duration.
Rounded implied command acceleration and jerk are checked again on the entire
candidate macro sequence. Strict original command/progress domains are retained.

## New inline objective and actual task provider

This is a NEW formulation in a separate namespace. It does not claim
CompleteQuadraticCost/input decoder execution or reuse their runtime acceptance.
Existing live cost source computes .5||Fc U+fc||^2 + ell*y + c, so its certificate
is Fc, not sqrt(2)*Fc. The new inline objective follows the same half-square
notation: J=.5||F U+f||^2 - progress_reward*s_N, including the full constant.
Each squared penalty's rows are explicitly sqrt(2*weight*quadrature)*localrow.
Thus a declared weight*quadrature*residual^2 is represented correctly.
H=F^T F; g=F^T f - progress_reward*M_sN; constant=.5*f^T f-progress_reward*c_sN.
H is calculated independently in source and supplied unchanged with sparse F
as the solver's PSD certificate. No symmetrization, replacement H, ridge,
changed solver epsilon or manufactured positive-definite certificate is used.

Actual task callback source is task_local_provider.cpp: a pinned world curve
uses start/end, lateral*sin(2*pi*s), vertical*sin(pi*s), and constant quaternion
xyzw; log(actual^-1*desired), the original RobotKinematics residual Jacobian,
and the original Jlog6 desired-body derivative convention. Angular rows are
scaled once by rotation_length=.3m. It borrows an actual RobotKinematics owner;
constructor and queries are separate future scopes. No coal or legacy
predictive.cpp dependency is introduced. The callback is local mathematics,
not an observer, source-of-permission or geometric safety witness.

The default numerical values mirror declared config/phase5.yaml values where
applicable; none have been applied to an existing controller. Every value and
reference must be frozen in the actual future profile. Units and channels:

| Term | Channels and units | Weight | Quadrature |
|---|---|---:|---|
| Tracking | SE3 translation m; rotation rad*.3m | 100 | node trapezoid seconds |
| Physical velocity | v, rad/s; independent of w | .01 | node trapezoid seconds |
| Posture | physical q-reference, rad | .001 | node trapezoid seconds |
| Command acceleration | alpha, rad/s^2 | .001 | cell seconds |
| Command jerk | (alpha-prev)/.004, rad/s^3 | .00001 | one .004s boundary |
| Progress acceleration | b, 1/s^2 | .001 | cell seconds |
| Progress jerk | (b-prev)/.004, 1/s^3 | .00001 | one .004s boundary |
| Terminal progress | s_N-1, dimensionless | .1 | terminal |
| Progress reward | -s_N, dimensionless | .1 | linear |

Weights carry the compensating units implied by their residual channels; equal
numeric values in distinct channels do not equate physical accelerations to b.
The progress penalties are independently named weights for this new formulation.
They use the declared acceleration/jerk numeric values; no prior cost pin is changed.
Factor rows=21*(6+7+7)+20*(7+7+1+1)+1=741;144 term descriptors include63 node,
80 input/jerk and1 terminal descriptors. The linear reward is retained separately.
The terminal s target is a SOFT objective, never a claim that the path is reachable
or completed within this .8-second horizon.

## Existing frozen cost artifact remains genuine and unused

The unchanged existing Model preparation still requires its original frozen
cost_input artifact, semantic SHA and FactorShape in INVOCATION_COST_BOUND_2.
The future runner must supply and preserve a legitimate previously reviewed
structural artifact, its exact bits and shape/semantic binding, in the same
source/readset closure. This package does NOT delete, replace, decode, execute,
retag or use that old cost for its online objective. The artifact remains a
required source-profile binding observed by the original preparation. Inline
objective source, task/math reference and parameters require their own reviewed
producer/source closure. There is no hidden redefinition of that old semantic SHA.
An existing prepare failure, resource refusal or mismatch still stops the chain.

## Constraints, coverage and separate storage

Each two-sided SI QP row has a stable unique label and unit. A matrix row with
lower/upper bounds is one row; its two inequalities are a different count.
The new QP row budget is independent of the old FactorShape.rows8192 ceiling.
The base new matrix has13156 rows, plus up to1600 supplied geometry rows:
320 input/feedback-jerk,20 progress Bernstein,3200 macro C/w/s/r,
800 half progress,16 terminal,8800 half physical q/v and q/s trust rows.
All400 half q/v checkpoints are covered. Initial actual q/v, accepted C/w,
previous alpha/b, and margins/domains are checked before assembly.
Physical speed limits must be supplied independently, using the reviewed mapped
phase4 velocity vector when that future profile is chosen; no command cap is
relabeled as a physical-speed cap.

The terminal rows set w_N, r_N, last alpha and last b to zero in SI. All command
macro bounds cover the known finite continuation throughout .8 seconds.
After solve the exact rounded tail state, last inputs and an exact-zero boolean
are retained. SI residual tolerance is not an infinite-time zero-tail proof.
A near-zero tail does not block a DATA-ONLY independent-forward diagnostic
request; it also does not open command execution. Exact zero would only certify
conditional command/progress zero extension. Neither proves physical v=0,
q equilibrium, safe geometry or a valid real supervisor stop. No snap/projection.

Geometry inputs are finite source-bound local scalar rows, at most4 per half;
empty inputs remain a QP component diagnostic with uncovered geometry. Even a
nonempty list is not full collision-pair coverage, conservative intersample
geometry, singularity clearance or nonlinear validation. Physical q/v sample
bounds and local trust rows are not nonlinear or intersample physical safety.
Physical acceleration, jerk, friction/contact branches and task accuracy still
require independent candidate forward and actual observer/plant gates.

New explicit arrays are checked against a separate logical plan before matrix
allocation: max20000 QP rows,160 controls,1600 supplied geometry rows,741 factor
rows,8,000,000 declared numeric slots. Original CaseBudget/ResourcePlan remains
unchanged. No unused old cost workspace is credited to the new adapter. This
is a finite shape/schedule bound, not a shared old CaseBudget receipt or OS RSS
certificate. Callback captured heap, allocator overhead, sparse conversion and
native solver memory totals remain unmeasured and need runtime process caps;
ordinary finite adapter work does not require complete Parent/RSS research closure.

## Timing, once entries and retained failures

The reviewed future protocol fixes one mode before execution. OfflineFrozenSimulationBoundary
keeps the original captured observer age, records all known real elapsed time
separately, and requires no simulation step/command change during the component.
It permits functional QP data without claiming online freshness or a4ms deadline.
OnlineWallAge adds actual externally supplied observation->preparation elapsed,
first-cycle open/metadata/forecast elapsed and connect/solve elapsed; it stops
on a stale candidate, with no timestamp refresh or switch to offline on failure.
Component timing does not itself prove the external elapsed assertion. V3 snapshot
age is compared exactly when present; a snapshot still captures caller observer
assertions and is not an independently certified physical observer. V1/V2 lack
that snapshot and remain clearly labeled CALLER_ASSERTIONS_ONLY.

Outcome::Storage owns the solver latch, set before solver admission. Replacing
CandidateOutcome cannot cause a second solve for the same source owner. Candidate
objects also retain their attempted state across Outcome changes. Reentry clears
the active request, records a refusal and keeps older outputs explicitly forensic.
solveAttempts counts the wrapper attempt; solverWrapperEntries counts C++ QP API
entry. Neither is OSQP/native/backend call telemetry. Runtime failures retain
original raw prefixes, partial matrices, rows/tasks written, native solver status,
violations, timing, previews and any prior forensic request. Catastrophic allocation
failure before an Outcome can exist must be caught by the future runner, which
must independently retain the original forecast evidence before adapter entry.
No retry, trust shrink, shorter horizon, epsilon change, teacher forcing or
substituted controller is implemented. Warm shift outputs controls only; it is
just a guess and cannot shift states/maps/permissions. Next actual initial must
be freshly observed and repropagated using its separately released genuine forecast.

# Functional diagnostic critical path

This is a source-backed diagnosis, not a benchmark or phase acceptance. Relevant
full implementations were read: legacy predictive.cpp/reactive_qp.cpp,
phase5_benchmark.cpp, live foundation/context and Model boundary, normalization,
affine, cost/input decoder, augmented extension, kinematics/task/reference/config.
The original source and accepted Phase4 evidence remain immutable.

The current legacy predictive state is nx16=[q,v,s,r], u=[a,b]; physical q uses
q+h*v+.5*h^2*a and v uses v+h*a. phase5_benchmark.cpp requests measured.dq+dt*a0,
then updates accepted command C from the projected requested velocity. These
legacy constraints, jerk timing and rollout cannot be renamed alpha or used as
the new coupled command dynamics. The new static-library chain is nx30 with
independent actual q/v and accepted C/w, but had no integration into a QP or
controller program. This new C++ package connects that chain to inline objective,
complete finite constraints, solver/SI gate and candidate first-command seam.
It does not claim the resulting source is compiled or numerically verified.

## Current code gaps on the necessary path

| Gap | Concrete status/action |
|---|---|
| Actual observer/history input provenance | Existing V3 snapshot captures caller assertions. Need one reviewed actual completed simulation-boundary adapter, mapped q/v and accepted C/w/alpha/b histories, no command in flight, contact facts, source IDs and timestamp provenance; never use archived fixtures as live authority. |
| Executable thin binding | Core orchestration/provider C++ are present; no new CLI/main serializer is included. Freeze a small standalone component entry point that supplies actual observer/context, protocol/readset pins, task provider and outputs to these functions. Do not invoke old phase5_benchmark. |
| Complete linked program | Original raw/normalization/affine/cost/codec static artifacts exist; new bridge/backend/provider are source only. Review one consolidated dependency/build manifest and build these targets with task provider ON; include unchanged typed factory and independent OSQP/reactive_qp backend. Avoid ROS/main/predictive.cpp and fresh side probes. |
| Profile and old cost binding | Freeze new nonuniform lattice, task curve/URDF/TCP/base, inline weights/margins, independent physical speeds, and the real unused original frozen cost artifact/shape required by existing preparation. Its old semantic pin cannot authorize a changed inline cost. |
| Candidate forward | Existing V1-V4 permit only one nominal extension forecast. Data-only request cannot use that permission for another candidate/validation rollout. Minimal new source/versioned factory design is specified separately; implementation and review still required. |
| Geometry and physical validation | Finite local rows are not complete safety. Need independent true candidate forward with every half q/v/contact/friction/physical accel/jerk observation and conservative geometry/singularity/task validation; preserve incomplete/unsupported prefixes and STOP. |
| Repeated controller session | 750 replans/commits need a new reviewed session factory/ledger and independently completed boundary on each cycle. This package contains no model-construction or planning loop. |
| Commit and stop transaction | Preview cannot issue. A separately reviewed plant/main adapter must validate/commit exact C_next/w_next, prove acceptance, update histories after completion and obtain a feasible physical stop. No silent projection/resets/fallback. |

## Independent review/freeze dependencies for the next execution package

One first-cycle OfflineFrozenSimulationBoundary COMPONENT package should be
released as one cohesive work unit after source review, source backup, complete
host/binary dependency freeze and actual observer/context provenance review.
It requires the real V3 permission/profile/readset/unused cost artifact/metadata
and a fresh immutable attempt claim, task Kinematics constructor/query scope,
one extension Model constructor/metadata/nominal forecast, normalization/affine,
one new inline objective+constraint assembly, one QP wrapper entry, original SI
and rounded command/progress gates, and complete output/failure retention.
Root must separately issue its build/configure/link and runtime scopes. Currently
all are closed. Existing zero-cost/provenance fields must be real and retained;
no old opaque cost execution is claimed. No candidate forward or plant commit
is included unless separately implemented/reviewed/released. The host-free draft
is a checklist/schema for binding, not a runnable or authorized protocol.

This package need not first execute all historical DEFERRED attack variants,
claim all Parent closure, OS RSS, global library call counts or performance.
Its actual required source/profile/callback/SDK/solver closure and process caps
must still be honest. Diagnostic elapsed/staleness/failures must be retained.
The next combined source/build/freeze/program evidence matters more than counts
of additional unrelated foundation cases. Earlier exceptions and freezes stay.

## Full three-second diagnostic versus complete task

3 seconds of TASK diagnostic time means750 complete4ms commits and1500 physical
2ms substeps, excluding any separately declared warmup and stop/settle time.
Every replan uses the complete .8-second N20/T200/S400 horizon;750 task commits
are not a750-cycle forecast. ResourcePolicyV2.cycles375/samples750 are per
forecast limits, not a permission to run a complete long controller session.
The current single-use Model release cannot be multiplied or renewed implicitly.

At s0=0 and r<=.2, the analytic3-second speed-integral upper bound is s<=.6;
acceleration/starting/stopping can lower it. A full s=1 path needs at least5
seconds at this speed before considering ramps/stops. Therefore the3-second
unit is a duration-complete functional diagnostic for a predeclared path segment,
not normalized full-path completion. Define actual task goal/segment/finish
criteria and stop time before runtime. Never teacher-force/renormalize s to1.
The first-cycle source package is neither a3-second execution nor a completed
arm task. Later successful whole-task runs can be rendered/recorded for videos
with all failure evidence preserved and declared showcase selection.

## Research acceptance that can follow functional correctness

Phase5 remains NOT_ACCEPTED; Phase6 NOT_STARTED. Controlled fixtures, source
plots and diagnostic diagrams do not establish safe complete trajectories,
real-time250Hz deadlines, comparative ranking, uniform accuracy/robustness,
hardware suitability or heldout performance. Those are distinct later acceptance
protocols. Do not weaken physical/geometry gates to obtain a demonstration.

# Affine source stage 3A — pending independent static review

Implemented source only: compact boundary/sample affine assembly, complete
control embedding and structured initial selector, plus optional independently
formed DenseAudit elimination. No configuration, compilation, numeric check,
Model/query/plant/solver/main/scorer execution occurred. Cost/capture/readers and
controller integration are not implemented. Phase5 NOT_ACCEPTED; Phase6 NOT_STARTED.

Only a complete genuine NormalizationOutcome enters assembly. Refused/unsupported
input stays owned with its original raw values/maps/errors and normalization
reason; it cannot produce a full assembly. LiveActual obtains x0 from the bound
validated actual context. A separate AlgebraTestInitial overload accepts finite
mathematical shifts including negative r; it acquires no live proposal or new
physical certificate. All7 scope flags remain fixed false.

## Compact representation

Each boundary stores o30, M30xDU, P30x30. Boundary0 is o=0/M=0/P=I; the next
boundary uses native cumulative wholecell A/B/d: o_next=A*o+d, M_next=A*M+B
inserted only into that cell's independent8 columns, P_next=A*P. No nominal state
reset, control tie or C/w-to-q/v alias exists. Complete y=[X0..XN;U]=T*U+t stores
T(DY,DU) and t(DY), with t_X=o+P*x0 and T_U=I/t_U=0. The complete initial selector
is represented by all stored P blocks plus an explicit zero U block; getters
return every entry without allocating a duplicate DYx30 matrix.

Samples use each native cumulative prefix at its own cell-origin boundary:
o_s=A_s*o_cell+d_s, M_s=A_s*M_cell+B_s at the own8-control slice, P_s=A_s*P_cell,
t_s=o_s+P_s*x0. A callback-only borrowed view exposes every o/M/P/t entry. It
cannot be copied or retained as a value. A bounded reused work array replaces
all S dense selectors in Compact. Polynomial sample progress and recursive
boundary progress remain encoded by their distinct original native defects.

## Optional DenseAudit

Requested mode must equal the captured whole-case ResourcePlan mode. DenseAudit
never silently falls back to Compact. Foundation preflight and actual shared
case/batch reservations may refuse the complete request without exposing partial
full-assembly output. Independent L has identity diagonal blocks and -A at the
previous boundary, E has own-cell B blocks, f has native defects and I0 selects
x0. A separately copied workspace performs scalar partial-pivot Gaussian
elimination for all control/offset/initial right-hand sides. It does not reuse
recursive output as the solution or call an Eigen/QP solver.

Residuals L*solution versus E/f/I0 and independently eliminated versus recursive
boundary maps use fixed abs=rel=2e-13 arithmetic defaults. Singularity, overflow,
quota or residual failure refuses the whole audit. Full S sample selectors over
y and both recursive/eliminated sample o/M/P are retained and checked. A selector's
native d remains available in the owned normalization source; it is not silently
folded into a missing summary. Exact arithmetic behavior and independent reference
gates still need a preregistered build/runtime review before any execution.

## Ownership and exact allocation schedule

The complete source normalization is anchored in the outcome before numeric
allocations; any ordinary validation/quota/allocation refusal retains it. Numeric
data is freed before tickets and before the owned normalization/raw provenance.
Private friend bridges access the already bound CaseBudget/ResourcePlan only;
no public arbitrary raw/maps factory, mutable raw accessor or const_cast is added.

Compact makes one whole reservation/allocation:
`(N+1)*(30+30*DU+900) + DY*DU+DY + (4*30*DU+4*900+60)` slots. The reused work
also holds the chosen30-coordinate initial. Buffer initial materialization is
charged by its owning reservation. Each later sample stream charges the entire
reviewed prefix-work amount before reusing that work; scalar FLOPs are not new
allocations. Matrix shapes and checked integer products are checked before
allocation. Stored X/t/T and streamed output are finite-checked during formation.

DenseAudit reserves ALL declared extras in one allocation before any audit write:
L/E/f/I0, `8*DX^2+6*DX*(DU+31)` workspace, `DX*(DU+31)` solution, S30xDY selectors
and two S*(30+30*DU+900) sample views. The matrix-per-sample cap applies to each
30xDY selector; its bounded tensor buffer holds all samples. Workspace is first
materialized from original L/RHS, then factored in place with scalar swaps/updates;
no additional dynamic numeric temporary or hidden dense sample allocation exists.
Unused workspace capacity is not an output value and must not be serialized.
This follows the existing prospective schedule without increasing any cap.

Actual reservations and every repeated-work charge obey case planned ceilings,
shared batchlive64m and cumulative limits. A stream can exhaust its cumulative
budget after repeated calls; no unlimited repeat is promised. Reentry, invalid
sample, empty/throwing callback or quota failure poisons the complete assembly,
retains the FIRST wrapper reason and prevents later complete-output access.
Original normalization/raw failures remain unchanged. Callback views are valid
only during the callback and are not a lifetime-owning snapshot.

## Versioning and outstanding gates

The accepted normalization.hpp/cpp and model_boundary.cpp are retained under
history/before_affine_private_bridges. Necessary extensions add only private
budget/plan access and future required source roles. A pre-whole-buffer cleanup
header/cpp snapshot is also preserved. Foundation/old Model/checker/profile and
immutable d3d4/ec1/Dell metadata stay unchanged. SDK planning remains a logical
allowance, not allocator/STL/string/process RAM telemetry.

The next source layers must implement full arbitrary costs and canonical ordered
term/sum evaluations, half-first Hessian, complete lossless capture/readers and
aggregate actual metadata/output quota enforcement. Independent build/freeze/run
protocol, controller/geometry/trust/stopping/timing and phase acceptance remain
separate. No cost weighting, solver or physical performance claim is inferred.
